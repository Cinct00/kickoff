"""Render a change analysis as terminal text, an AI-reviewer context pack, GitHub Markdown (+Mermaid) or HTML."""
from __future__ import annotations

import json
import posixpath
import re

from .util import est_tokens

MARK = {"signature": "~", "removed": "-", "renamed": "→", "moved": "→", "modified": "*", "added": "+"}
STATUS = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}
COMMENT_MARKER = "<!-- codemap-change-map -->"


def _sym_line(c: dict) -> str:
    sig = c.get("new_sig") or c.get("old_sig") or c["qualname"]
    if c["change"] == "signature":
        s = f"~ {c['new_sig']}  [was: {c['old_sig']}]"
    elif c["change"] in ("renamed", "moved"):
        s = f"→ {sig}  [{c['change']} from {c.get('old_name')}]"
    elif c["change"] == "modified":
        s = f"* {sig}  ({c['lines_changed']} lines)"
    else:
        s = f"{MARK[c['change']]} {sig}"
    if c.get("callers_outside"):
        s += f"  ⚠ callers outside diff: {', '.join(c['callers_outside'][:4])}" + (" …" if len(c["callers_outside"]) > 4 else "")
    return s


def _summary_line(a: dict) -> str:
    s = a["summary"]
    syms = ", ".join(f"{n} {k}" for k, n in sorted(s["symbols"].items(), key=lambda t: -t[1])) or "no symbol changes"
    head = "working tree" if a["head"] == "WORKTREE" else a["head"]
    return (f"change map: {a['repo']} {a['base_label']} ({a['base']}) → {head} · {s['files']} files "
            f"+{s['added_lines']} −{s['deleted_lines']} · symbols: {syms} · risk {s['level'].upper()} ({s['risk']})")


def _file_head(i: int, f: dict) -> str:
    moved = f" (from {f['old_path']})" if f.get("old_path") else ""
    why = f" — {'; '.join(f['reasons'])}" if f["reasons"] else ""
    return f"{i}. {f['path']}{moved}  {f['status']} +{f['added']} −{f['deleted']}  risk {f['risk']} {f['level']}{why}"


def text(a: dict, max_files: int = 40) -> str:
    out = [_summary_line(a)]
    if a["attention"]:
        out.append("attention:")
        for x in a["attention"]:
            out.append(f" {'!' if x['severity'] == 'high' else '·'} {x['message']}" + (f": {', '.join(x['where'][:5])}" if x["where"] else ""))
    out.append("review order:")
    for i, f in enumerate(a["files"][:max_files], 1):
        out.append(" " + _file_head(i, f))
        for c in f["symbols"][:12]:
            out.append("    " + _sym_line(c))
        if len(f["symbols"]) > 12:
            out.append(f"    (+{len(f['symbols']) - 12} more symbol changes)")
    if len(a["files"]) > max_files:
        out.append(f" (+{len(a['files']) - max_files} more files)")
    t = a["tests"]
    out.append(f"tests: {len(t['changed'])} changed" + (f" · affected but unchanged: {', '.join(t['affected_unchanged'][:6])}" if t["affected_unchanged"] else ""))
    if a["deps"]:
        out.append("dependencies: " + ", ".join(_dep(d) for d in a["deps"][:12]))
    out.append("next: codemap review --format context (AI review pack) · --format md (PR comment) · --format html --out change-map.html")
    return "\n".join(out)


def _dep(d: dict) -> str:
    if d["change"] == "added":
        return f"+{d['name']} {d.get('new', '')}".strip()
    if d["change"] == "removed":
        return f"-{d['name']}"
    return f"{d['name']} {d.get('old', '')}→{d.get('new', '')}"


def context(a: dict, budget: int = 6000) -> str:
    """Risk-ordered review pack for an AI reviewer: structure first, then hunks until the budget is spent."""
    head = [_summary_line(a)]
    if a["attention"]:
        head.append("ATTENTION (verify these first):")
        for x in a["attention"]:
            head.append(f"- {x['message']}" + (f": {', '.join(x['where'][:6])}" if x["where"] else ""))
    if a["deps"]:
        head.append("DEPENDENCIES: " + ", ".join(_dep(d) for d in a["deps"][:15]))
    t = a["tests"]
    if t["affected_unchanged"]:
        head.append("TESTS LIKELY AFFECTED (unchanged): " + ", ".join(t["affected_unchanged"][:10]))
    head.append("FILES IN REVIEW ORDER (risk-ranked; symbols: ~ signature, - removed, → renamed/moved, * modified, + added):")
    # The header gets at most 40% of the budget; keep its first and last lines.
    while len(head) > 3 and est_tokens("\n".join(head)) > budget * 0.4:
        head.pop(-2)
    out = list(head)
    tail_hint = "Use `codemap show <Symbol>`, `refs`, `impact` for more context on any item."
    budget -= est_tokens(tail_hint) + 30  # reserve room for the closing lines
    used = est_tokens("\n".join(out))
    skipped = []
    for i, f in enumerate(a["files"], 1):
        block = [_file_head(i, f)] + ["  " + _sym_line(c) for c in f["symbols"][:15]]
        if f["generated"]:
            block = [_file_head(i, f) + " (generated: diff omitted)"]
        else:
            for h in f["hunks"]:
                block.append(f"  @@ -{h['old_start']},{h['old_len']} +{h['new_start']},{h['new_len']} @@ {h['header']}".rstrip())
                block += [f"  {tag}{line}" for tag, line in h["lines"]]
            if f.get("hunks_truncated"):
                block.append("  … diff truncated; use `codemap show` for the rest")
        cost = est_tokens("\n".join(block))
        if used + cost > budget:
            # Fall back to structure only for this file, then one-liners.
            small = [_file_head(i, f)] + ["  " + _sym_line(c) for c in f["symbols"][:8]]
            sc = est_tokens("\n".join(small))
            if used + sc <= budget:
                out += small + ["  (diff omitted for budget: `codemap show <symbol>` or `git diff` this file)"]
                used += sc + 12
            else:
                skipped.append(f)
            continue
        out += block
        used += cost
    if skipped:
        names = [f"{f['path']} (risk {f['risk']})" for f in skipped]
        line = f"NOT INCLUDED ({len(skipped)} files, budget): " + ", ".join(names)
        while len(names) > 1 and est_tokens(line) > 30 + max(0, budget - used):
            names.pop()
            line = f"NOT INCLUDED ({len(skipped)} files, budget): " + ", ".join(names) + " …"
        out.append(line)
    out.append(tail_hint)
    return "\n".join(out)


# --------------------------------------------------------------------------- markdown / mermaid

def _mm_label(s: str) -> str:
    return s.replace('"', "#quot;").replace("<", "#lt;").replace(">", "#gt;").replace("|", "#124;")


GENERIC = {"index", "mod", "__init__", "main", "lib", "init", "types", "utils", "util", "common", "base", "router", "node"}


def short_name(path: str) -> str:
    """'src/jwt/index.ts' -> 'jwt/index.ts'; 'src/app/service.py' -> 'service.py'."""
    base = posixpath.basename(path)
    parent = posixpath.basename(posixpath.dirname(path))
    return f"{parent}/{base}" if parent and base.rsplit(".", 1)[0] in GENERIC else base


def mermaid(a: dict, max_changed: int = 15, max_impacted: int = 6, max_edges: int = 35) -> str:
    """A PR-comment-sized diagram: the riskiest changed files, a few impacted neighbours, the key edges."""
    g = a["graph"]
    changed = [n for n in g["nodes"] if not n["impacted"]][:max_changed]
    keep = {n["id"] for n in changed}
    inbound = {}
    for e in g["edges"]:
        if e["to"] in keep and e["from"] not in keep:
            inbound[e["from"]] = inbound.get(e["from"], 0) + 1
    impacted = [n for n in g["nodes"] if n["impacted"] and n["id"] in inbound]
    impacted = sorted(impacted, key=lambda n: -inbound[n["id"]])[:max_impacted]
    nodes = changed + impacted
    ids_ok = {n["id"] for n in nodes}
    risk = {n["id"]: n["risk"] for n in nodes}
    edges = [e for e in g["edges"] if e["from"] in ids_ok and e["to"] in ids_ok]
    edges = sorted(edges, key=lambda e: -(risk.get(e["from"], 0) + risk.get(e["to"], 0)))[:max_edges]
    g = {"nodes": nodes, "edges": edges}
    if not g["nodes"]:
        return ""
    styles = {"added": "fill:#dafbe1,stroke:#1a7f37,color:#0a3622",
              "modified": "fill:#fff8c5,stroke:#9a6700,color:#3d2a00",
              "deleted": "fill:#ffebe9,stroke:#cf222e,color:#5c0a12,stroke-dasharray:4 2",
              "renamed": "fill:#ddf4ff,stroke:#0969da,color:#0a2a4d",
              "impacted": "fill:#f6f8fa,stroke:#8c959f,color:#424a53,stroke-dasharray:3 3"}
    lines = ["flowchart LR"]
    for k, v in styles.items():  # Mermaid can't combine classes on a node, so high-risk gets its own variant
        lines.append(f"  classDef {k} {v}")
        lines.append(f"  classDef {k}High {v},stroke-width:3px")
    ids = {n["id"]: f"n{i}" for i, n in enumerate(g["nodes"])}
    by_dir: dict = {}
    for n in g["nodes"]:
        by_dir.setdefault(posixpath.dirname(n["id"]) or ".", []).append(n)
    for di, (d, ns) in enumerate(sorted(by_dir.items())):
        lines.append(f'  subgraph d{di}["{_mm_label(d + "/" if d != "." else "(root)")}"]')
        for n in ns:
            name = short_name(n["id"])
            if n["impacted"]:
                label = f"{name}<br/>impacted"
            else:
                warn = " ⚠" if n["level"] == "high" else ""
                label = f"{name}<br/>+{n['added']} −{n['deleted']}{warn}"
            cls = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}.get(n["status"], "impacted")
            cls += "High" if n["level"] == "high" else ""
            lines.append(f'    {ids[n["id"]]}["{_mm_label(label).replace("#lt;br/#gt;", "<br/>")}"]:::{cls}')
        lines.append("  end")
        lines.append(f"  style d{di} fill:transparent,stroke:#d0d7de")
    for e in g["edges"]:
        if e["from"] in ids and e["to"] in ids:
            lines.append(f"  {ids[e['from']]} --> {ids[e['to']]}")
    return "\n".join(lines)


def markdown(a: dict, max_files: int = 25, html_hint: str | None = None) -> str:
    s = a["summary"]
    icon = {"high": "🔴", "medium": "🟠", "low": "🟢"}[s["level"]]
    syms = " · ".join(f"{n} {k}" for k, n in sorted(s["symbols"].items(), key=lambda t: -t[1])) or "no symbol changes"
    out = [COMMENT_MARKER, f"## 🗺️ Change map {icon} {s['level']} risk",
           f"**{s['files']} files** (+{s['added_lines']} −{s['deleted_lines']}) · **symbols:** {syms} · "
           f"**tests changed:** {s['tests_changed']} · base `{a['base_label']}` ({a['base']})", ""]
    mm = mermaid(a)
    if mm:
        out += [f"<details open><summary><b>Dependency view</b> (riskiest changed files by status, grey = impacted but unchanged, "
                f"arrows = uses; tests listed below)</summary>",
                "", "```mermaid", mm, "```", "", "</details>", ""]
    if a["attention"]:
        out.append("### ⚠️ Needs attention")
        for x in a["attention"]:
            where = f" — {', '.join(f'`{w}`' for w in x['where'][:5])}" if x["where"] else ""
            out.append(f"- {'**' if x['severity'] == 'high' else ''}{x['message']}{'**' if x['severity'] == 'high' else ''}{where}")
        out.append("")
    out += ["### Review order", "", "| # | File | Risk | Change | Why |", "|---:|---|---|---|---|"]
    for i, f in enumerate(a["files"][:max_files], 1):
        lv = {"high": "🔴", "medium": "🟠", "low": "🟢"}[f["level"]]
        moved = f" ← `{f['old_path']}`" if f.get("old_path") else ""
        why = "; ".join(f["reasons"]).replace("|", "/") or "—"
        out.append(f"| {i} | `{f['path']}`{moved} | {lv} {f['risk']} | {STATUS.get(f['status'], f['status'])} +{f['added']} −{f['deleted']} | {why} |")
    if len(a["files"]) > max_files:
        out.append(f"| | … {len(a['files']) - max_files} more files | | | |")
    out.append("")
    sym_files = [f for f in a["files"] if f["symbols"]]
    if sym_files:
        out += ["<details><summary><b>Symbol changes</b></summary>", ""]
        for f in sym_files[:max_files]:
            out.append(f"**`{f['path']}`**")
            out.append("```diff")
            for c in f["symbols"][:20]:
                line = _sym_line(c)
                prefix = {"added": "+ ", "removed": "- ", "signature": "! ", "renamed": "! ", "moved": "! ", "modified": "  "}[c["change"]]
                out.append(prefix + line[2:])
            out.append("```")
        out += ["</details>", ""]
    t = a["tests"]
    if t["changed"] or t["affected_unchanged"] or t["untested"]:
        out.append("### Tests")
        if t["changed"]:
            out.append(f"- changed: {', '.join(f'`{p}`' for p in t['changed'][:10])}")
        if t["affected_unchanged"]:
            out.append(f"- likely affected, not changed (run them): {', '.join(f'`{p}`' for p in t['affected_unchanged'][:10])}")
        if t["untested"]:
            out.append(f"- changed code with no tests: {', '.join(f'`{p}`' for p in t['untested'][:10])}")
        out.append("")
    if a["deps"]:
        out.append("### Dependencies")
        out += [f"- `{d['manifest']}`: {_dep(d)}" for d in a["deps"][:20]]
        out.append("")
    foot = "<sub>Generated by codemap review (ai-toolkit). AI reviewers: `codemap review --format context --budget 8000` gives the same view as a risk-ordered review pack."
    if html_hint:
        foot += f" Interactive report: {html_hint}."
    out.append(foot + "</sub>")
    text = "\n".join(out)
    if len(text) > 60000:  # GitHub comment limit is 65,536 characters
        text = text[:60000] + "\n\n… truncated (comment size limit)."
    return text


# --------------------------------------------------------------------------- html

def html(a: dict) -> str:
    data = json.dumps(a, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    title = f"Change map · {a['repo']}"
    return HTML_TEMPLATE.replace("__TITLE__", re.sub(r"[<>&\"]", "", title)).replace("__DATA__", data)


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#ffffff;--fg:#1f2328;--muted:#59636e;--line:#d1d9e0;--card:#f6f8fa;--add:#1a7f37;--add-bg:#dafbe1;--del:#cf222e;--del-bg:#ffebe9;
--mod:#9a6700;--mod-bg:#fff8c5;--ren:#0969da;--ren-bg:#ddf4ff;--imp:#8c959f;--high:#cf222e;--med:#bc4c00;--low:#1a7f37;--accent:#0969da}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--line:#30363d;--card:#151b23;
--add:#3fb950;--add-bg:#12261e;--del:#f85149;--del-bg:#2d1214;--mod:#d29922;--mod-bg:#2e2410;--ren:#58a6ff;--ren-bg:#0c2d4d;--imp:#6e7681;
--high:#f85149;--med:#db6d28;--low:#3fb950;--accent:#58a6ff}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--line:#30363d;--card:#151b23;--add:#3fb950;--add-bg:#12261e;--del:#f85149;
--del-bg:#2d1214;--mod:#d29922;--mod-bg:#2e2410;--ren:#58a6ff;--ren-bg:#0c2d4d;--imp:#6e7681;--high:#f85149;--med:#db6d28;--low:#3fb950;--accent:#58a6ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:1200px;margin:0 auto;padding:20px 16px 60px}h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 10px}
.muted{color:var(--muted)}code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}.card b{display:block;font-size:20px}
.pill{display:inline-block;border-radius:999px;padding:1px 8px;font-size:12px;font-weight:600;border:1px solid currentColor}
.high{color:var(--high)}.medium{color:var(--med)}.low{color:var(--low)}
#graphwrap{border:1px solid var(--line);border-radius:8px;background:var(--card);position:relative}
#graph{width:100%;height:440px;display:block;touch-action:none}#legend{display:flex;flex-wrap:wrap;gap:12px;padding:8px 12px;border-top:1px solid var(--line);font-size:12px}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:-1px;border:1px solid}
.attn li{margin:4px 0}.attn .h{color:var(--high);font-weight:600}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;color:var(--muted);font-weight:600}tr.row{cursor:pointer}tr.row:hover{background:var(--card)}
.tablewrap{overflow-x:auto}details.file{border:1px solid var(--line);border-radius:8px;margin:10px 0;background:var(--bg)}
details.file>summary{padding:8px 12px;cursor:pointer;display:flex;gap:10px;flex-wrap:wrap;align-items:center;list-style:none}
details.file>summary::-webkit-details-marker{display:none}details.file[open]>summary{border-bottom:1px solid var(--line)}
.syms{padding:8px 12px;margin:0;list-style:none}.syms li{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;padding:2px 0;word-break:break-word}
.c-added{color:var(--add)}.c-removed{color:var(--del)}.c-signature,.c-renamed,.c-moved{color:var(--ren)}.c-modified{color:var(--mod)}
.warn{color:var(--high)}pre.diff{margin:0;overflow-x:auto;font-size:12px;line-height:1.45;border-top:1px solid var(--line)}
pre.diff span{display:block;padding:0 12px;white-space:pre}.dl-add{background:var(--add-bg)}.dl-del{background:var(--del-bg)}.dl-hunk{color:var(--muted);background:var(--card)}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:4px 10px;cursor:pointer;font:inherit}
.reason{color:var(--muted);font-size:12.5px}.tag{font-size:11px;border-radius:4px;padding:0 5px;border:1px solid var(--line);color:var(--muted)}
@media (max-width:640px){#graph{height:320px}.hide-sm{display:none}}
</style></head><body><main>
<header><h1 id="title"></h1><div class="muted" id="sub"></div></header>
<div class="cards" id="cards"></div>
<h2>Dependency view</h2>
<div id="graphwrap"><svg id="graph" role="img" aria-label="Changed files and their dependencies"></svg>
<div id="legend"></div></div>
<section id="attnsec"><h2>Needs attention</h2><ul class="attn" id="attn"></ul></section>
<h2>Review order</h2><div class="tablewrap"><table><thead><tr><th>#</th><th>File</th><th>Risk</th><th class="hide-sm">Change</th><th>Why</th></tr></thead><tbody id="order"></tbody></table></div>
<h2>Files</h2><div class="toolbar"><button id="expand">Expand all</button><button id="collapse">Collapse all</button></div><div id="files"></div>
<section id="testsec"><h2>Tests</h2><div id="tests"></div></section>
<section id="depsec"><h2>Dependencies</h2><ul id="deps"></ul></section>
<p class="muted" style="margin-top:32px">Generated by codemap review (ai-toolkit).</p>
</main>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
const A = JSON.parse(document.getElementById('data').textContent);
const $ = (id) => document.getElementById(id);
function el(tag, attrs, ...kids){const e=document.createElement(tag);for(const k in (attrs||{})){if(k==='class')e.className=attrs[k];else if(k==='text')e.textContent=attrs[k];else e.setAttribute(k,attrs[k]);}
  for(const c of kids){if(c==null)continue;e.appendChild(typeof c==='string'?document.createTextNode(c):c);}return e;}
const S = A.summary, head = A.head==='WORKTREE'?'working tree':A.head;
$('title').textContent = 'Change map · ' + A.repo;
$('sub').textContent = A.base_label + ' (' + A.base + ') → ' + head;
const symTotal = Object.values(S.symbols).reduce((a,b)=>a+b,0);
const cards=[['Files',S.files],['Lines','+'+S.added_lines+' −'+S.deleted_lines],['Symbol changes',symTotal],['Tests changed',S.tests_changed],['High-risk files',S.high]];
for(const [k,v] of cards){$('cards').appendChild(el('div',{class:'card'},el('span',{class:'muted',text:k}),el('b',{text:String(v)})));}
$('cards').appendChild(el('div',{class:'card'},el('span',{class:'muted',text:'Overall risk'}),el('b',{class:S.level,text:S.level.toUpperCase()+' '+S.risk})));
// attention
if(!A.attention.length){$('attnsec').style.display='none';}
for(const x of A.attention){const li=el('li',null,el('span',{class:x.severity==='high'?'h':'',text:(x.severity==='high'?'⚠ ':'')+x.message}));
  if(x.where&&x.where.length){li.appendChild(el('div',{class:'mono muted',text:x.where.slice(0,8).join('  ·  ')}));}$('attn').appendChild(li);}
// order + files
const MARK={signature:'~',removed:'−',renamed:'→',moved:'→',modified:'✱',added:'+'};
const STATUS={A:'added',M:'modified',D:'deleted',R:'renamed'};
A.files.forEach((f,i)=>{
  const tr=el('tr',{class:'row'},el('td',{text:String(i+1)}),el('td',null,el('code',{text:f.path})),
    el('td',null,el('span',{class:'pill '+f.level,text:f.level+' '+f.risk})),
    el('td',{class:'hide-sm',text:(STATUS[f.status]||f.status)+' +'+f.added+' −'+f.deleted}),el('td',{class:'reason',text:f.reasons.join('; ')||'—'}));
  tr.addEventListener('click',()=>openFile(f.path));$('order').appendChild(tr);
  const sum=el('summary',null,el('span',{class:'pill '+f.level,text:f.risk}),el('code',{text:f.path}),
    f.old_path?el('span',{class:'tag',text:'from '+f.old_path}):null,el('span',{class:'tag',text:STATUS[f.status]||f.status}),
    el('span',{class:'muted',text:'+'+f.added+' −'+f.deleted}),f.generated?el('span',{class:'tag',text:'generated'}):null);
  const d=el('details',{class:'file',id:'f-'+i},sum);d.dataset.path=f.path;
  if(f.symbols.length){const ul=el('ul',{class:'syms'});for(const c of f.symbols){
      let t=MARK[c.change]+' '+(c.new_sig||c.old_sig||c.qualname);
      if(c.change==='signature')t+='   (was: '+c.old_sig+')';if(c.change==='renamed'||c.change==='moved')t+='   ('+c.change+' from '+c.old_name+')';
      if(c.change==='modified')t+='   ('+c.lines_changed+' lines)';
      const li=el('li',{class:'c-'+c.change,text:t});
      if(c.callers_outside){li.appendChild(el('div',{class:'warn',text:'⚠ callers outside this change: '+c.callers_outside.slice(0,6).join(', ')}));}
      ul.appendChild(li);}d.appendChild(ul);}
  if(f.dependents&&f.dependents.length){d.appendChild(el('div',{class:'reason',style:'padding:0 12px 8px',text:'Used by (unchanged): '+f.dependents.slice(0,10).join(', ')+(f.dependents.length>10?' …':'')}));}
  if(f.hunks.length){const pre=el('pre',{class:'diff'});
    for(const h of f.hunks){pre.appendChild(el('span',{class:'dl-hunk',text:'@@ -'+h.old_start+','+h.old_len+' +'+h.new_start+','+h.new_len+' @@ '+h.header}));
      for(const [tag,line] of h.lines){pre.appendChild(el('span',{class:tag==='+'?'dl-add':tag==='-'?'dl-del':'',text:tag+line}));}}
    if(f.hunks_truncated)pre.appendChild(el('span',{class:'dl-hunk',text:'… truncated'}));d.appendChild(pre);}
  $('files').appendChild(d);});
function openFile(p){const d=[...document.querySelectorAll('details.file')].find(x=>x.dataset.path===p);if(d){d.open=true;d.scrollIntoView({behavior:'smooth',block:'start'});}}
$('expand').onclick=()=>document.querySelectorAll('details.file').forEach(d=>d.open=true);
$('collapse').onclick=()=>document.querySelectorAll('details.file').forEach(d=>d.open=false);
// tests + deps
const T=A.tests;const tb=$('tests');
if(!T.changed.length&&!T.affected_unchanged.length&&!T.untested.length){$('testsec').style.display='none';}
[['Changed',T.changed],['Likely affected, not changed (run them)',T.affected_unchanged],['Changed code with no tests',T.untested]].forEach(([k,v])=>{
  if(v.length)tb.appendChild(el('p',null,el('b',{text:k+': '}),el('span',{class:'mono',text:v.join(', ')})));});
if(!A.deps.length)$('depsec').style.display='none';
for(const d of A.deps){$('deps').appendChild(el('li',{class:'mono',text:d.manifest+': '+(d.change==='added'?'+ '+d.name+' '+(d.new||''):d.change==='removed'?'− '+d.name:d.name+' '+(d.old||'')+' → '+(d.new||''))}));}
// graph: small force layout, no libraries
const G=A.graph, svg=$('graph'), NS='http://www.w3.org/2000/svg';
const colors={A:['--add-bg','--add'],M:['--mod-bg','--mod'],D:['--del-bg','--del'],R:['--ren-bg','--ren'],impacted:['--card','--imp']};
const css=(v)=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
[['added','A'],['modified','M'],['deleted','D'],['renamed','R'],['impacted (unchanged)','impacted']].forEach(([k,s])=>{
  const sw=el('span',{class:'sw'});sw.style.background=css(colors[s][0]);sw.style.borderColor=css(colors[s][1]);$('legend').appendChild(el('span',null,sw,k));});
$('legend').appendChild(el('span',{class:'muted',text:'arrow = uses · size = risk · click a node to open the file'}));
if(!G.nodes.length){$('graphwrap').style.display='none';return;}
const GENERIC=new Set(['index','mod','__init__','main','lib','init','types','utils','util','common','base','router','node']);
function shortName(p){const parts=p.split('/');const b=parts.pop();const stem=b.replace(/\.[^.]+$/,'');return parts.length&&GENERIC.has(stem)?parts.pop()+'/'+b:b;}
const tog=el('label',{style:'margin-left:auto'});const cb=el('input',{type:'checkbox'});cb.checked=true;tog.appendChild(cb);tog.appendChild(document.createTextNode(' impacted files'));$('legend').appendChild(tog);
const W=()=>svg.clientWidth||800, H=()=>svg.clientHeight||440;
const nodes=G.nodes.map((n,i)=>({...n,x:W()/2+Math.cos(i)*120+Math.random()*20,y:H()/2+Math.sin(i)*120+Math.random()*20,vx:0,vy:0}));
const idx=Object.fromEntries(nodes.map((n,i)=>[n.id,i]));const links=G.edges.filter(e=>e.from in idx&&e.to in idx).map(e=>({s:idx[e.from],t:idx[e.to]}));
const defs=document.createElementNS(NS,'defs');defs.innerHTML='<marker id="arr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="'+css('--muted')+'"/></marker>';svg.appendChild(defs);
const lg=document.createElementNS(NS,'g'),ng=document.createElementNS(NS,'g');svg.appendChild(lg);svg.appendChild(ng);
const lines=links.map(()=>{const l=document.createElementNS(NS,'line');l.setAttribute('stroke',css('--line'));l.setAttribute('stroke-width','1.4');l.setAttribute('marker-end','url(#arr)');lg.appendChild(l);return l;});
const R=(n)=>n.impacted?7:9+Math.min(14,n.risk/7);
const gs=nodes.map((n)=>{const g=document.createElementNS(NS,'g');g.style.cursor=n.impacted?'default':'pointer';
  const c=document.createElementNS(NS,'circle');c.setAttribute('r',R(n));const col=colors[n.impacted?'impacted':n.status]||colors.M;
  c.setAttribute('fill',css(col[0]));c.setAttribute('stroke',css(col[1]));c.setAttribute('stroke-width',n.level==='high'?3:1.6);if(n.impacted)c.setAttribute('stroke-dasharray','3 2');
  const t=document.createElementNS(NS,'text');t.textContent=shortName(n.id);t.setAttribute('font-size','11');t.setAttribute('fill',css('--fg'));t.setAttribute('dy',R(n)+12);t.setAttribute('text-anchor','middle');
  const tt=document.createElementNS(NS,'title');tt.textContent=n.id+(n.impacted?' (impacted, unchanged)':' · risk '+n.risk+' · +'+n.added+' −'+n.deleted);
  g.appendChild(c);g.appendChild(t);g.appendChild(tt);ng.appendChild(g);if(!n.impacted)g.addEventListener('click',()=>openFile(n.id));return g;});
let drag=null;svg.addEventListener('pointerdown',(e)=>{const i=gs.findIndex(g=>g.contains(e.target));if(i>=0){drag=i;svg.setPointerCapture(e.pointerId);}});
svg.addEventListener('pointermove',(e)=>{if(drag==null)return;const r=svg.getBoundingClientRect();nodes[drag].x=e.clientX-r.left;nodes[drag].y=e.clientY-r.top;nodes[drag].vx=nodes[drag].vy=0;kick();});
svg.addEventListener('pointerup',()=>{drag=null;});
let alpha=1;function step(){const w=W(),h=H();
  const rep=1800+nodes.length*90;
  for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy||1;const f=rep/d2;const d=Math.sqrt(d2);dx/=d;dy/=d;a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f;}
  for(const l of links){const a=nodes[l.s],b=nodes[l.t];const dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1;const f=(d-110)*0.02;a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;}
  for(const [i,n] of nodes.entries()){if(i===drag)continue;n.vx+=(w/2-n.x)*0.004;n.vy+=(h/2-n.y)*0.004;n.x+=n.vx*alpha;n.y+=n.vy*alpha;n.vx*=0.6;n.vy*=0.6;
    n.x=Math.max(30,Math.min(w-30,n.x));n.y=Math.max(20,Math.min(h-30,n.y));}
  links.forEach((l,k)=>{const a=nodes[l.s],b=nodes[l.t];const dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1;const rb=R(b)+3;
    lines[k].setAttribute('x1',a.x);lines[k].setAttribute('y1',a.y);lines[k].setAttribute('x2',b.x-dx/d*rb);lines[k].setAttribute('y2',b.y-dy/d*rb);});
  gs.forEach((g,i)=>{g.setAttribute('transform','translate('+nodes[i].x+','+nodes[i].y+')');g.style.display=(nodes[i].impacted&&!cb.checked)?'none':'';});
  links.forEach((l,k)=>{lines[k].style.display=((nodes[l.s].impacted||nodes[l.t].impacted)&&!cb.checked)?'none':'';});
  alpha*=0.985;if(alpha>0.02)requestAnimationFrame(step);}
function kick(){if(alpha<=0.02){alpha=0.3;requestAnimationFrame(step);}else alpha=Math.max(alpha,0.3);}
cb.addEventListener('change',kick);
requestAnimationFrame(step);
})();
</script></body></html>
"""
