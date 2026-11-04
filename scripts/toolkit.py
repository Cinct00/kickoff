#!/usr/bin/env python3
"""ai-toolkit command line.

One stdlib-only script that builds, validates, installs and spreads the toolkit
across Claude Code, GitHub Copilot (CLI, cloud agent, VS Code) and any client
that reads Agent Skills.

    python3 scripts/toolkit.py build            # regenerate manifests + marketplaces
    python3 scripts/toolkit.py validate         # lint skills/agents/hooks, check generated files
    python3 scripts/toolkit.py catalog          # rescan upstream marketplaces into catalog/
    python3 scripts/toolkit.py install          # set up this device (Claude Code / Copilot CLI / skills dirs)
    python3 scripts/toolkit.py adopt <project>  # wire the toolkit into another repository
    python3 scripts/toolkit.py promote <dir>    # move a project-local skill/agent into the toolkit
    python3 scripts/toolkit.py sync             # git pull + refresh installed plugins
    python3 scripts/toolkit.py status           # what is installed where

Run any subcommand with --help for options.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "toolkit.json"
PLUGINS_DIR = ROOT / "plugins"
CATALOG_DIR = ROOT / "catalog"
KICKOFF_REFS = PLUGINS_DIR / "kickoff" / "skills" / "kickoff" / "references"
CATALOG_TSV = KICKOFF_REFS / "catalog.tsv"
LOCAL_MARKETPLACE = "kickoff"  # = toolkit.json "name"; plugins install as <plugin>@kickoff

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GEN_BEGIN = "<!-- BEGIN GENERATED:{} -->"
GEN_END = "<!-- END GENERATED:{} -->"
ADOPT_BEGIN = "<!-- ai-toolkit:begin -->"
ADOPT_END = "<!-- ai-toolkit:end -->"


# --------------------------------------------------------------------------- utils

def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def dump_json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def info(msg: str) -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr, flush=True)


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def parse_frontmatter(text: str) -> dict:
    """Parse the small YAML subset used in SKILL.md / agent frontmatter.

    Handles `key: value`, quoted values, folded/literal blocks (`>`, `|`) and
    simple inline lists. Anything fancier is kept as raw text.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    lines = text[3:end].strip("\n").splitlines()
    out: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            joiner = " " if val.startswith(">") else "\n"
            out[key] = joiner.join(b for b in block if b or joiner == "\n").strip()
            continue
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            out[key] = items
        elif len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            out[key] = val[1:-1]
        else:
            out[key] = val
        i += 1
    return out


def est_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def one_line(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def run(cmd: list[str], dry_run: bool = False, cwd: Path | None = None, check: bool = False) -> int:
    shown = " ".join(_quote(c) for c in cmd)
    if dry_run:
        info(f"  [dry-run] {shown}")
        return 0
    info(f"  $ {shown}")
    try:
        proc = subprocess.run(cmd, cwd=cwd)
    except FileNotFoundError:
        warn(f"command not found: {cmd[0]}")
        return 127
    if check and proc.returncode != 0:
        die(f"command failed ({proc.returncode}): {shown}")
    return proc.returncode


def _quote(s: str) -> str:
    return s if re.match(r"^[A-Za-z0-9_@%+=:,./-]+$", s) else json.dumps(s)


def own_plugin_dirs() -> list[Path]:
    """Plugin dirs in toolkit.json order (kickoff first), unknown dirs last."""
    order = list(load_config()["plugins"])
    dirs = [p for p in PLUGINS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]
    return sorted(dirs, key=lambda p: (order.index(p.name) if p.name in order else len(order), p.name))


def write_if_changed(path: Path, content: str, check: bool, stale: list[str]) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return
    if check:
        stale.append(str(path.relative_to(ROOT)))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    info(f"  wrote {path.relative_to(ROOT)}")


def replace_block(text: str, tag: str, body: str) -> str:
    begin, end = GEN_BEGIN.format(tag), GEN_END.format(tag)
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    replacement = f"{begin}\n{body.rstrip()}\n{end}"
    if not pattern.search(text):
        raise ValueError(f"missing generated block markers for '{tag}'")
    return pattern.sub(lambda _: replacement, text)


# --------------------------------------------------------------------------- inventory

def inventory_plugin(pdir: Path, entry: dict | None = None) -> dict:
    """Describe the skills, agents, commands, hooks and MCP servers in a plugin dir."""
    entry = entry or {}
    manifest = {}
    for cand in (".claude-plugin/plugin.json", "plugin.json", ".github/plugin/plugin.json", ".plugin/plugin.json"):
        f = pdir / cand
        if f.is_file():
            try:
                manifest = json.loads(f.read_text(encoding="utf-8"))
                break
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    def as_list(v):
        if v is None:
            return []
        return [v] if isinstance(v, str) else list(v)

    ext = (manifest.get("extensions") or {}).get("com.github.awesome-copilot") or {}
    skill_paths = as_list(entry.get("skills")) or as_list(manifest.get("skills")) or as_list(ext.get("skills")) or ["skills/"]
    agent_paths = as_list(entry.get("agents")) or as_list(manifest.get("agents")) or as_list(ext.get("agents")) or ["agents/"]
    cmd_paths = as_list(entry.get("commands")) or as_list(manifest.get("commands")) or ["commands/"]

    skills, agents, commands = [], [], []
    for sp in skill_paths:
        base = (pdir / sp).resolve()
        if not base.exists() or not str(base).startswith(str(pdir.resolve())):
            continue
        cands = [base] if (base / "SKILL.md").is_file() else sorted(d for d in base.iterdir() if d.is_dir()) if base.is_dir() else []
        for d in cands:
            sf = d / "SKILL.md"
            if sf.is_file():
                fm = parse_frontmatter(sf.read_text(encoding="utf-8", errors="replace"))
                skills.append({"name": fm.get("name") or d.name, "description": one_line(fm.get("description", ""), 400)})
    for ap in agent_paths:
        base = (pdir / ap)
        files = [base] if base.is_file() else sorted(base.glob("*.md")) if base.is_dir() else []
        for f in files:
            fm = parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            stem = f.name[: -len(".agent.md")] if f.name.endswith(".agent.md") else f.stem
            agents.append({"name": fm.get("name") or stem, "description": one_line(fm.get("description", ""), 400)})
    for cp in cmd_paths:
        base = pdir / cp
        files = [base] if base.is_file() else sorted(base.glob("*.md")) if base.is_dir() else []
        for f in files:
            fm = parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            commands.append({"name": f.stem, "description": one_line(fm.get("description", ""), 400)})

    hooks = set()
    for hf in (pdir / "hooks" / "hooks.json", pdir / "hooks.json"):
        if hf.is_file():
            try:
                hooks.update((json.loads(hf.read_text(encoding="utf-8")).get("hooks") or {}).keys())
            except (json.JSONDecodeError, AttributeError):
                pass
    mcp = set()
    for mf in (pdir / ".mcp.json", pdir / "mcp.json", pdir / ".github" / "mcp.json"):
        if mf.is_file():
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                mcp.update((data.get("mcpServers") or data).keys())
            except (json.JSONDecodeError, AttributeError):
                pass
    return {
        "manifest": manifest,
        "skills": skills,
        "agents": agents,
        "commands": commands,
        "hooks": sorted(hooks),
        "mcp": sorted(k for k in mcp if not k.startswith("$")),
    }


def profile_refs(cfg: dict) -> list[str]:
    refs = []
    for key, group in cfg["upstream"]["profile"].items():
        if key.startswith("$"):
            continue
        refs.extend(group)
    return refs


# --------------------------------------------------------------------------- build

def build_plugin_manifests(cfg: dict) -> dict[Path, str]:
    out: dict[Path, str] = {}
    repo_url = f"https://github.com/{cfg['repository']}"
    for pdir in own_plugin_dirs():
        meta = cfg["plugins"].get(pdir.name)
        if meta is None:
            die(f"plugins/{pdir.name} has no entry in toolkit.json 'plugins'")
        common = {
            "name": pdir.name,
            "version": meta.get("version", cfg["version"]),
            "description": meta["description"],
            "author": cfg["owner"],
            "homepage": f"{repo_url}/tree/main/plugins/{pdir.name}",
            "repository": repo_url,
            "license": cfg["license"],
            "keywords": meta.get("keywords", []),
        }
        # Claude Code reads .claude-plugin/plugin.json and auto-discovers
        # skills/, agents/ and hooks/hooks.json (Claude hook format).
        out[pdir / ".claude-plugin" / "plugin.json"] = dump_json(common)

        # Copilot CLI / cloud agent read the root plugin.json first. Point
        # hooks at the Copilot-format file so it never parses Claude's.
        copilot = dict(common)
        copilot["category"] = meta.get("category", "productivity")
        if (pdir / "skills").is_dir():
            copilot["skills"] = ["skills/"]
        if (pdir / "agents").is_dir():
            copilot["agents"] = "agents/"
        if (pdir / "hooks" / "copilot-hooks.json").is_file():
            copilot["hooks"] = "hooks/copilot-hooks.json"
        if (pdir / "copilot-mcp.json").is_file():
            # Copilot expands ${PLUGIN_ROOT}; Claude's .mcp.json uses ${CLAUDE_PLUGIN_ROOT}.
            copilot["mcpServers"] = "copilot-mcp.json"
        out[pdir / "plugin.json"] = dump_json(copilot)
    return out


def build_marketplace(cfg: dict) -> str:
    plugins = []
    for pdir in own_plugin_dirs():
        meta = cfg["plugins"][pdir.name]
        plugins.append({
            "name": pdir.name,
            "source": f"./plugins/{pdir.name}",
            "description": meta["description"],
            "version": meta.get("version", cfg["version"]),
            "author": cfg["owner"],
            "license": cfg["license"],
            "category": meta.get("category", "productivity"),
            "keywords": meta.get("keywords", []),
        })
    return dump_json({
        "name": cfg["name"],
        "owner": cfg["owner"],
        "metadata": {"description": cfg["description"], "version": cfg["version"]},
        "plugins": plugins,
    })


def build_readme_tables(cfg: dict) -> dict[str, str]:
    rows = ["| Plugin | Skills | Agents | Hooks | What it is for |", "|---|---|---|---|---|"]
    skills_rows = ["| Skill | Plugin | Use it when |", "|---|---|---|"]
    for pdir in own_plugin_dirs():
        inv = inventory_plugin(pdir)
        rows.append(
            f"| [`{pdir.name}`](plugins/{pdir.name}) | {len(inv['skills'])} | {len(inv['agents'])} | "
            f"{'yes' if inv['hooks'] else '—'} | {cfg['plugins'][pdir.name]['description']} |"
        )
        for s in inv["skills"]:
            desc = one_line(s["description"].split(". Use")[0], 140)
            skills_rows.append(f"| `{s['name']}` | {pdir.name} | {desc} |")
    prof = ["| Group | Plugins |", "|---|---|"]
    for key, group in cfg["upstream"]["profile"].items():
        if not key.startswith("$"):
            prof.append(f"| {key} | " + ", ".join(f"`{r}`" for r in group) + " |")
    return {"plugins": "\n".join(rows), "skills": "\n".join(skills_rows), "profile": "\n".join(prof)}


def build_plugin_readme(cfg: dict, pdir: Path) -> str:
    """Return the plugin README with its generated 'install' block refreshed."""
    inv = inventory_plugin(pdir)
    lines = [
        "## Install",
        "",
        "Claude Code:",
        "",
        "```",
        f"/plugin marketplace add {cfg['repository']}",
        f"/plugin install {pdir.name}@{LOCAL_MARKETPLACE}",
        "```",
        "",
        "GitHub Copilot CLI:",
        "",
        "```bash",
        f"copilot plugin marketplace add {cfg['repository']}",
        f"copilot plugin install {pdir.name}@{LOCAL_MARKETPLACE}",
        "```",
        "",
        "Any other Agent Skills client: copy or link `skills/*` into `~/.agents/skills/` "
        "(or run `python3 scripts/toolkit.py install --target skills` from the toolkit).",
        "",
        "## Contents",
        "",
    ]
    for kind, label in (("skills", "Skill"), ("agents", "Agent")):
        if inv[kind]:
            lines += [f"| {label} | Description |", "|---|---|"]
            for c in inv[kind]:
                folder = f"skills/{c['name']}/SKILL.md" if kind == "skills" else f"agents/{c['name']}.agent.md"
                lines.append(f"| [`{c['name']}`]({folder}) | {one_line(c['description'], 220).replace('|', '/')} |")
            lines.append("")
    if inv["hooks"]:
        cop = pdir / "hooks" / "copilot-hooks.json"
        cop_events = sorted((json.loads(cop.read_text(encoding="utf-8")).get("hooks") or {}).keys()) if cop.is_file() else []
        lines += [f"Hooks: Claude Code {', '.join(inv['hooks'])} (`hooks/hooks.json`); "
                  f"Copilot {', '.join(cop_events) or 'none'} (`hooks/copilot-hooks.json`).", ""]
    body = "\n".join(lines)
    readme = pdir / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        if GEN_BEGIN.format("install") in text:
            return replace_block(text, "install", body)
        return text  # hand-written README without markers: leave it alone
    return (f"# {pdir.name}\n\n{cfg['plugins'][pdir.name]['description']}\n\n"
            f"Part of [{cfg['name']}](../../README.md).\n\n"
            f"{GEN_BEGIN.format('install')}\n{body.rstrip()}\n{GEN_END.format('install')}\n")


def own_catalog_entries(cfg: dict) -> list[dict]:
    entries = []
    for pdir in own_plugin_dirs():
        inv = inventory_plugin(pdir)
        inv.pop("manifest")
        entries.append({"name": pdir.name, "description": cfg["plugins"][pdir.name]["description"],
                        "source": "bundled", "status": "own", **inv})
    return entries


def catalog_rows(mk_name: str, plugins: list[dict]) -> list[str]:
    rows = []
    for p in plugins:
        ref = f"{p['name']}@{mk_name}"
        rows.append(f"plugin\t{p['name']}\t{ref}\t{p['status']}\t{one_line(p['description'], 200)}")
        for kind in ("skills", "agents", "commands"):
            for c in p.get(kind, []):
                rows.append(f"{kind[:-1]}\t{c['name']}\t{ref}\t{p['status']}\t{one_line(c['description'], 200)}")
    return rows


def refreshed_catalog_tsv(cfg: dict) -> str | None:
    """Re-derive this toolkit's own rows in catalog.tsv offline; upstream rows are kept as scanned."""
    if not CATALOG_TSV.exists():
        return None
    lines = CATALOG_TSV.read_text(encoding="utf-8").splitlines()
    header = [l for l in lines if l.startswith("#")]
    rest = [l for l in lines if not l.startswith("#") and f"@{LOCAL_MARKETPLACE}\t" not in l]
    return "\n".join(header + catalog_rows(LOCAL_MARKETPLACE, own_catalog_entries(cfg)) + rest) + "\n"


def cmd_build(args) -> int:
    cfg = load_config()
    stale: list[str] = []
    check = getattr(args, "check", False)
    for path, content in build_plugin_manifests(cfg).items():
        write_if_changed(path, content, check, stale)
    tsv = refreshed_catalog_tsv(cfg)
    if tsv is not None:
        write_if_changed(CATALOG_TSV, tsv, check, stale)
    for pdir in own_plugin_dirs():
        write_if_changed(pdir / "README.md", build_plugin_readme(cfg, pdir), check, stale)
    market = build_marketplace(cfg)
    # Identical copies: Claude Code reads .claude-plugin/, Copilot prefers .github/plugin/.
    write_if_changed(ROOT / ".claude-plugin" / "marketplace.json", market, check, stale)
    write_if_changed(ROOT / ".github" / "plugin" / "marketplace.json", market, check, stale)
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    new = text
    for tag, body in build_readme_tables(cfg).items():
        new = replace_block(new, tag, body)
    write_if_changed(readme, new, check, stale)
    if check and stale:
        for s in stale:
            warn(f"out of date: {s}")
        info("run: python3 scripts/toolkit.py build")
        return 1
    if not check:
        info("build complete")
    return 0


# --------------------------------------------------------------------------- validate

PROPRIETARY_MARKERS = ("Anthropic, PBC. All rights reserved", "Proprietary. LICENSE.txt")


def cmd_validate(args) -> int:
    cfg = load_config()
    errors: list[str] = []
    warnings: list[str] = []
    seen_skills: dict[str, str] = {}
    known = set(cfg["app_builtins"]["skills"].keys())

    dirs = {p.name for p in own_plugin_dirs()}
    for name in cfg["plugins"]:
        if name not in dirs:
            errors.append(f"toolkit.json lists plugin '{name}' but plugins/{name} does not exist")
    for bundle, members in cfg["bundles"].items():
        for m in members:
            if m not in cfg["plugins"]:
                errors.append(f"bundle '{bundle}' references unknown plugin '{m}'")

    skill_files = sorted(PLUGINS_DIR.glob("*/skills/*/SKILL.md"))
    for sf in skill_files:
        rel = sf.relative_to(ROOT)
        text = sf.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        name, desc = fm.get("name", ""), fm.get("description", "")
        if not fm:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue
        if name != sf.parent.name:
            errors.append(f"{rel}: name '{name}' must match directory '{sf.parent.name}'")
        if not NAME_RE.match(name or "") or len(name) > 64:
            errors.append(f"{rel}: name must be lowercase-hyphenated, max 64 chars")
        if not desc:
            errors.append(f"{rel}: description is required")
        elif len(desc) > 1024:
            errors.append(f"{rel}: description is {len(desc)} chars (Agent Skills limit is 1024)")
        if name in seen_skills:
            errors.append(f"{rel}: duplicate skill name (also in {seen_skills[name]})")
        seen_skills[name] = str(rel)
        known.add(name)
        if len(text.splitlines()) > 500:
            warnings.append(f"{rel}: over 500 lines; move detail into references/")

    for sf in skill_files:
        prose = re.sub(r"`[^`\n]*`", "", sf.read_text(encoding="utf-8"))  # ignore examples in inline code
        for link in re.findall(r"\[\[([a-z0-9-]+)\]\]", prose):
            if link not in known:
                warnings.append(f"{sf.relative_to(ROOT)}: [[{link}]] does not match any toolkit skill")

    for af in sorted(PLUGINS_DIR.glob("*/agents/*.md")):
        rel = af.relative_to(ROOT)
        if not af.name.endswith(".agent.md"):
            errors.append(f"{rel}: agent files must be named <name>.agent.md (Copilot requirement; Claude accepts it)")
            continue
        fm = parse_frontmatter(af.read_text(encoding="utf-8"))
        stem = af.name[: -len(".agent.md")]
        if fm.get("name") != stem:
            errors.append(f"{rel}: frontmatter name '{fm.get('name')}' must equal file stem '{stem}'")
        if not fm.get("description"):
            errors.append(f"{rel}: description is required")
        if isinstance(fm.get("model"), list):
            errors.append(f"{rel}: 'model' must be a single string (lists are Copilot-only and break Claude)")

    for pdir in own_plugin_dirs():
        claude_h = pdir / "hooks" / "hooks.json"
        copilot_h = pdir / "hooks" / "copilot-hooks.json"
        if claude_h.exists() != copilot_h.exists():
            warnings.append(f"plugins/{pdir.name}: ship both hooks/hooks.json (Claude) and hooks/copilot-hooks.json (Copilot)")
        for hf, fmt in ((claude_h, "claude"), (copilot_h, "copilot")):
            if not hf.exists():
                continue
            try:
                data = json.loads(hf.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"{hf.relative_to(ROOT)}: invalid JSON ({e})")
                continue
            if fmt == "copilot" and data.get("version") != 1:
                errors.append(f"{hf.relative_to(ROOT)}: Copilot hooks need \"version\": 1")
            for event in (data.get("hooks") or {}):
                if fmt == "claude" and not event[:1].isupper():
                    errors.append(f"{hf.relative_to(ROOT)}: Claude hook events are PascalCase ('{event}')")
                if fmt == "copilot" and not event[:1].islower():
                    errors.append(f"{hf.relative_to(ROOT)}: use camelCase Copilot event names ('{event}')")

    for lic in PLUGINS_DIR.rglob("*"):
        if lic.is_file() and lic.suffix in (".md", ".txt") and lic.stat().st_size < 400_000:
            head = lic.read_text(encoding="utf-8", errors="ignore")[:2000]
            if any(m in head for m in PROPRIETARY_MARKERS):
                errors.append(f"{lic.relative_to(ROOT)}: proprietary third-party content must not be vendored; reference it in toolkit.json instead")

    for ref in profile_refs(cfg):
        if "@" not in ref:
            errors.append(f"profile entry '{ref}' must be plugin@marketplace")
        elif ref.split("@", 1)[1] not in {m["name"] for m in cfg["upstream"]["marketplaces"]}:
            errors.append(f"profile entry '{ref}' uses a marketplace not listed in upstream.marketplaces")

    if not CATALOG_TSV.exists():
        warnings.append(f"{CATALOG_TSV.relative_to(ROOT)} missing; run: python3 scripts/toolkit.py catalog")

    for w in warnings:
        warn(w)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    build_rc = cmd_build(argparse.Namespace(check=True))
    if errors or build_rc:
        info(f"validate: {len(errors)} error(s), {len(warnings)} warning(s)" + ("; generated files stale" if build_rc else ""))
        return 1
    info(f"validate: ok ({len(skill_files)} skills, {len(warnings)} warning(s))")
    return 0


# --------------------------------------------------------------------------- catalog

def _git_clone(repo: str, dest: Path, ref: str | None = None) -> bool:
    url = repo if "://" in repo else f"https://github.com/{repo}.git"
    if dest.exists():
        shutil.rmtree(dest)
    cmd = ["git", "clone", "-q", "--depth", "1", "--filter=blob:limit=512k"]
    if ref:
        cmd += ["--branch", ref]
    cmd += [url, str(dest)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 and ref:
        return _git_clone(repo, dest, None)
    if proc.returncode != 0:
        warn(f"clone failed for {repo}: {proc.stderr.strip()[:200]}")
    return proc.returncode == 0


def _read_marketplace(root: Path) -> dict | None:
    for cand in (".claude-plugin/marketplace.json", ".github/plugin/marketplace.json", "marketplace.json", ".plugin/marketplace.json"):
        f = root / cand
        if f.is_file():
            return json.loads(f.read_text(encoding="utf-8"))
    return None


def _source_label(src) -> str:
    if isinstance(src, str):
        return "bundled"
    if isinstance(src, dict):
        repo = src.get("repo") or src.get("url", "")
        repo = re.sub(r"^https://github.com/|\.git$", "", repo)
        path = src.get("path")
        return f"{repo}{':' + path if path else ''}"
    return "?"


def cmd_catalog(args) -> int:
    cfg = load_config()
    active = set(profile_refs(cfg))
    cache = Path(args.cache or Path(tempfile.gettempdir()) / "ai-toolkit-catalog")
    cache.mkdir(parents=True, exist_ok=True)
    stamp = _dt.date.today().isoformat()
    marketplaces = []

    marketplaces.append({"name": LOCAL_MARKETPLACE, "repo": cfg["repository"], "publisher": cfg["owner"]["name"],
                         "trust": "own", "plugins": own_catalog_entries(cfg)})

    previous = {}
    if args.only and (CATALOG_DIR / "index.json").is_file():
        # Partial rescan: keep the other marketplaces from the last full scan.
        previous = {m["name"]: m for m in json.loads((CATALOG_DIR / "index.json").read_text(encoding="utf-8"))["marketplaces"]}

    for mk in cfg["upstream"]["marketplaces"]:
        if args.only and mk["name"] not in args.only:
            if mk["name"] in previous:
                kept = previous[mk["name"]]
                for p in kept["plugins"]:
                    p["status"] = "active" if f"{p['name']}@{mk['name']}" in active else "available"
                marketplaces.append(kept)
            continue
        info(f"scanning {mk['repo']} …")
        dest = cache / mk["name"]
        if not _git_clone(mk["repo"], dest):
            continue
        manifest = _read_marketplace(dest)
        if not manifest:
            warn(f"{mk['repo']}: no marketplace.json found")
            continue
        entries = []
        for p in manifest.get("plugins", []):
            ref = f"{p['name']}@{mk['name']}"
            src = p.get("source")
            item = {"name": p["name"], "description": one_line(p.get("description", ""), 400),
                    "source": _source_label(src), "status": "active" if ref in active else "available",
                    "skills": [], "agents": [], "commands": [], "hooks": [], "mcp": []}
            pdir = None
            if isinstance(src, str):
                pdir = (dest / (manifest.get("metadata", {}).get("pluginRoot") or "") / src).resolve()
            elif isinstance(src, dict) and (args.deep or ref in active) and src.get("source") in ("github", "url", "git-subdir"):
                sub = cache / "_ext" / f"{mk['name']}__{p['name']}"
                repo = src.get("repo") or src.get("url")
                if repo and _git_clone(repo, sub, src.get("ref")):
                    pdir = (sub / src["path"]).resolve() if src.get("path") else sub
            if pdir and pdir.is_dir():
                inv = inventory_plugin(pdir, p)
                inv.pop("manifest")
                item.update(inv)
            entries.append(item)
        marketplaces.append({**mk, "plugins": entries})

    builtins = [{"name": k, "description": v} for k, v in cfg["app_builtins"]["skills"].items() if not k.startswith("$")]
    index = {"generated": stamp, "marketplaces": marketplaces, "app_builtins": builtins}
    CATALOG_DIR.mkdir(exist_ok=True)
    (CATALOG_DIR / "index.json").write_text(dump_json(index), encoding="utf-8")

    # Grep-friendly component list that ships inside the kickoff skill.
    lines = ["# kind\tname\tplugin@marketplace\tstatus\tdescription",
             f"# generated {stamp} by scripts/toolkit.py catalog. status: own = this toolkit, active = in your profile, available = installable, app = Claude app built-in"]
    for mk in marketplaces:
        lines += catalog_rows(mk["name"], mk["plugins"])
    for b in builtins:
        lines.append(f"skill\t{b['name']}\tclaude-app\tapp\t{b['description']}")
    KICKOFF_REFS.mkdir(parents=True, exist_ok=True)
    CATALOG_TSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Human-readable overview.
    md = [f"# Catalog", "", f"Generated {stamp} by `python3 scripts/toolkit.py catalog`. Do not edit by hand.", "",
          "Status: **own** = in this repo · **active** = in your profile (`toolkit.json` → `upstream.profile`) · available = installable from that marketplace.", "",
          "Machine-readable versions: [`index.json`](index.json) and the kickoff skill's "
          "[`catalog.tsv`](../plugins/kickoff/skills/kickoff/references/catalog.tsv).", ""]
    for mk in marketplaces:
        md += [f"## {mk['name']}", "", f"`{mk['repo']}` · {mk.get('publisher', '')} · trust: {mk.get('trust', '')}", "",
               "| Plugin | Status | Skills | Agents | Commands | Hooks | MCP | Description |", "|---|---|---|---|---|---|---|---|"]
        for p in sorted(mk["plugins"], key=lambda x: (x["status"] != "own", x["status"] != "active", x["name"])):
            md.append(f"| `{p['name']}` | {'**' + p['status'] + '**' if p['status'] != 'available' else p['status']} | "
                      f"{len(p['skills'])} | {len(p['agents'])} | {len(p['commands'])} | {', '.join(p['hooks']) or '—'} | "
                      f"{', '.join(p['mcp']) or '—'} | {one_line(p['description'], 160).replace('|', '/')} |")
        md.append("")
    (CATALOG_DIR / "CATALOG.md").write_text("\n".join(md), encoding="utf-8")

    n_plugins = sum(len(m["plugins"]) for m in marketplaces)
    info(f"catalog: {len(marketplaces)} marketplaces, {n_plugins} plugins, {len(lines) - 2} rows → {CATALOG_TSV.relative_to(ROOT)}")
    missing = [r for r in active if not any(f"{p['name']}@{m['name']}" == r for m in marketplaces for p in m["plugins"])]
    for r in missing:
        warn(f"profile plugin not found upstream: {r}")
    return 0


# --------------------------------------------------------------------------- install

def toolkit_home_marker() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "ai-toolkit" / "home"


def _plugin_refs_for(cfg: dict, bundle: str, with_upstream: bool) -> tuple[list[str], list[str]]:
    own = [f"{p}@{LOCAL_MARKETPLACE}" for p in cfg["bundles"][bundle]]
    upstream = profile_refs(cfg) if with_upstream else []
    return own, upstream


def _marketplace_source(cfg: dict, local: bool) -> str:
    return str(ROOT) if local else cfg["repository"]


class Ledger:
    """Record of everything install wrote outside the toolkit, so doctor can verify and repair it."""

    def __init__(self, dry_run: bool):
        self.path = toolkit_home_marker().parent / "installed.json"
        self.dry_run = dry_run
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.data = {}
        self.entries = {e["path"]: e for e in self.data.get("entries", [])}

    def owns(self, path: Path, source: Path) -> bool:
        """True if a previous install wrote `path` from `source` (so it may be replaced)."""
        e = self.entries.get(str(path))
        return bool(e) and e.get("source") == str(source) and e.get("kind") in ("link", "copy")

    def add(self, kind: str, path: Path, source: Path | None, target: str, **extra) -> None:
        self.entries[str(path)] = {"kind": kind, "path": str(path), "source": str(source) if source else None,
                                   "target": target, **extra}

    def save(self, cfg: dict, targets, bundle: str) -> None:
        if self.dry_run:
            return
        self.data = {"toolkit": str(ROOT), "version": cfg["version"], "commit": _git_head(), "bundle": bundle,
                     "installed_at": _dt.datetime.now().isoformat(timespec="seconds"),
                     "targets": sorted(set(self.data.get("targets", [])) | set(targets)),
                     "entries": sorted(self.entries.values(), key=lambda e: e["path"])}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(dump_json(self.data), encoding="utf-8")


def _bundle_items(cfg: dict, bundle: str):
    """Yield (plugin_dir, kind, path) for skills and agents in a bundle."""
    for pname in cfg["bundles"][bundle]:
        pdir = PLUGINS_DIR / pname
        for sdir in sorted((pdir / "skills").glob("*")):
            if (sdir / "SKILL.md").is_file():
                yield pdir, "skill", sdir
        for af in sorted((pdir / "agents").glob("*.agent.md")):
            yield pdir, "agent", af


def _abs_plugin_paths(obj, pdir: Path):
    """Replace plugin-root placeholders with an absolute path (for user-level configs)."""
    if isinstance(obj, str):
        for ph in ("${CLAUDE_PLUGIN_ROOT}", "${PLUGIN_ROOT}", "${COPILOT_PLUGIN_ROOT}"):
            obj = obj.replace(ph, str(pdir))
        return obj
    if isinstance(obj, list):
        return [_abs_plugin_paths(x, pdir) for x in obj]
    if isinstance(obj, dict):
        return {k: _abs_plugin_paths(v, pdir) for k, v in obj.items()}
    return obj


def _write_json_file(path: Path, data: dict, dry_run: bool) -> None:
    content = dump_json(data)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    if dry_run:
        info(f"  [dry-run] write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    info(f"  wrote {path}")


def _install_copilot_user(cfg: dict, bundle: str, ledger: Ledger, copy: bool, dry_run: bool) -> None:
    """Copilot's user-level layout: ~/.copilot/{skills,agents,hooks,mcp-config.json} (all repos on this device)."""
    home = Path(os.environ.get("COPILOT_HOME", Path.home() / ".copilot"))
    info(f"\n== copilot user level ({home})")
    for pdir, kind, src in _bundle_items(cfg, bundle):
        if kind == "skill":
            dest = home / "skills" / src.name
            managed = _link_or_copy(src, dest, copy, dry_run)
        else:
            dest = home / "agents" / src.name
            managed = _link_or_copy_file(src, dest, copy, dry_run, owned=ledger.owns(dest, src))
        if managed:
            ledger.add("copy" if copy or os.name == "nt" else "link", dest, src, "copilot-user")
    hooks: dict = {}
    servers: dict = {}
    for pname in cfg["bundles"][bundle]:
        pdir = PLUGINS_DIR / pname
        ch = pdir / "hooks" / "copilot-hooks.json"
        if ch.is_file():
            for event, entries in (json.loads(ch.read_text(encoding="utf-8")).get("hooks") or {}).items():
                for e in entries:
                    e = dict(e)
                    e["env"] = {**(e.get("env") or {}), "PLUGIN_ROOT": str(pdir)}
                    hooks.setdefault(event, []).append(e)
        cm = pdir / "copilot-mcp.json"
        if cm.is_file():
            servers.update(_abs_plugin_paths(json.loads(cm.read_text(encoding="utf-8")).get("mcpServers") or {}, pdir))
    if hooks:
        hp = home / "hooks" / "ai-toolkit.json"
        _write_json_file(hp, {"version": 1, "hooks": hooks}, dry_run)
        ledger.add("file", hp, None, "copilot-user")
    if servers:
        mp = home / "mcp-config.json"
        data = {}
        if mp.exists():
            try:
                data = json.loads(mp.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                warn(f"{mp} is not valid JSON; not touching it")
                data = None
        if data is not None:
            data.setdefault("mcpServers", {}).update(servers)
            _write_json_file(mp, data, dry_run)
            for name in servers:
                ledger.add("json-key", mp, None, "copilot-user", key=f"mcpServers.{name}")


def _install_claude_user(cfg: dict, bundle: str, ledger: Ledger, copy: bool, dry_run: bool) -> None:
    """Claude Code without plugins: ~/.claude/{skills,agents}, user MCP, hooks in ~/.claude/settings.json."""
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    info(f"\n== claude user level ({home})")
    for pdir, kind, src in _bundle_items(cfg, bundle):
        dest = home / ("skills" if kind == "skill" else "agents") / (src.name if kind == "skill" else src.name.replace(".agent.md", ".md"))
        managed = (_link_or_copy(src, dest, copy, dry_run) if kind == "skill"
                   else _link_or_copy_file(src, dest, copy, dry_run, owned=ledger.owns(dest, src)))
        if managed:
            ledger.add("copy" if copy or os.name == "nt" else "link", dest, src, "claude-user")
    settings = home / "settings.json"
    try:
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    except json.JSONDecodeError:
        warn(f"{settings} is not valid JSON; skipping hooks")
        data = None
    if data is not None:
        hooks = data.setdefault("hooks", {})
        for event in list(hooks):  # drop entries a previous install added, then re-add
            ours = json.dumps(str(PLUGINS_DIR))[1:-1]  # JSON-escaped, so Windows backslashes match
            hooks[event] = [g for g in hooks[event] if ours not in json.dumps(g)]
            if not hooks[event]:
                del hooks[event]
        for pname in cfg["bundles"][bundle]:
            hf = PLUGINS_DIR / pname / "hooks" / "hooks.json"
            if hf.is_file():
                for event, groups in (json.loads(hf.read_text(encoding="utf-8")).get("hooks") or {}).items():
                    hooks.setdefault(event, []).extend(_abs_plugin_paths(groups, PLUGINS_DIR / pname))
        if not hooks:
            data.pop("hooks")
        _write_json_file(settings, data, dry_run)
        ledger.add("json-key", settings, None, "claude-user", key="hooks")
    for pname in cfg["bundles"][bundle]:
        mf = PLUGINS_DIR / pname / ".mcp.json"
        if mf.is_file():
            for name, spec in _abs_plugin_paths(json.loads(mf.read_text(encoding="utf-8")).get("mcpServers") or {},
                                                PLUGINS_DIR / pname).items():
                if shutil.which("claude") or dry_run:
                    run(["claude", "mcp", "remove", "--scope", "user", name], dry_run) if not dry_run else None
                    run(["claude", "mcp", "add", "--scope", "user", name, "--", spec["command"], *spec.get("args", [])], dry_run)
                    ledger.add("mcp", Path(f"claude-mcp:{name}"), None, "claude-user")
                else:
                    info(f"  claude CLI not found; add MCP server '{name}' manually: {spec['command']} {' '.join(spec.get('args', []))}")


def _install_shim(ledger: Ledger, dry_run: bool) -> None:
    """Put `codemap` on PATH (~/.local/bin) pointing at this checkout."""
    script = PLUGINS_DIR / "codemap" / "scripts" / "codemap.py"
    if not script.is_file():
        return
    bindir = Path(os.environ.get("AI_TOOLKIT_BIN", Path.home() / ".local" / "bin"))
    if os.name == "nt":
        dest, body = bindir / "codemap.cmd", f'@echo off\r\npython "{script}" %*\r\n'
    else:
        dest, body = bindir / "codemap", f'#!/bin/sh\nexec python3 "{script}" "$@"\n'
    if dest.exists() and dest.read_text(encoding="utf-8", errors="replace") == body:
        ledger.add("file", dest, script, "shim")
        return
    if dry_run:
        info(f"  [dry-run] write {dest}")
        return
    bindir.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    if os.name != "nt":
        dest.chmod(0o755)
    ledger.add("file", dest, script, "shim")
    info(f"  wrote {dest}")
    if str(bindir) not in os.environ.get("PATH", "").split(os.pathsep):
        warn(f"{bindir} is not on PATH; add it so agents can run `codemap`")


def cmd_install(args) -> int:
    cfg = load_config()
    targets = set(args.target or ["auto"])
    have = {t: shutil.which(t) is not None for t in ("claude", "copilot", "git")}
    if "auto" in targets:
        targets = {"skills"}
        if have["claude"]:
            targets.add("claude")
        if have["copilot"] or (Path.home() / ".copilot").is_dir():
            targets.add("copilot-user")
    own, upstream = _plugin_refs_for(cfg, args.bundle, not args.no_upstream)
    market_src = _marketplace_source(cfg, args.local)
    ledger = Ledger(args.dry_run)
    info(f"toolkit home: {ROOT}")
    info(f"targets: {', '.join(sorted(targets))}; bundle: {args.bundle}; upstream plugins: {len(upstream)}")

    if not args.dry_run:
        marker = toolkit_home_marker()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(ROOT) + "\n", encoding="utf-8")
        info(f"  recorded toolkit home in {marker}")

    upstream_markets = {m["name"]: m["repo"] for m in cfg["upstream"]["marketplaces"]}
    needed_markets = sorted({r.split("@", 1)[1] for r in upstream})
    failures = []

    for cli, target in (("claude", "claude"), ("copilot", "copilot"), ("copilot", "copilot-user")):
        if target not in targets:
            continue
        if not have[cli] and not args.dry_run:
            if target != "copilot-user":
                warn(f"'{cli}' CLI not found on PATH; skipping")
            continue
        info(f"\n== {cli} plugins")
        refs = (own if target != "copilot-user" else []) + upstream
        if target != "copilot-user":
            run([cli, "plugin", "marketplace", "add", market_src], args.dry_run)
        for name in needed_markets:
            run([cli, "plugin", "marketplace", "add", upstream_markets[name]], args.dry_run)
        for ref in refs:
            if run([cli, "plugin", "install", ref], args.dry_run):
                failures.append(f"{cli}: {ref}")

    if "copilot-user" in targets:
        _install_copilot_user(cfg, args.bundle, ledger, args.copy, args.dry_run)
    if "claude-user" in targets:
        _install_claude_user(cfg, args.bundle, ledger, args.copy, args.dry_run)

    if "skills" in targets:
        dirs = [Path(d).expanduser() for d in (args.skills_dir or ["~/.agents/skills"])]
        info(f"\n== skills directories: {', '.join(str(d) for d in dirs)}")
        for d in dirs:
            for _pdir, kind, src in _bundle_items(cfg, args.bundle):
                if kind == "skill" and _link_or_copy(src, d / src.name, args.copy, args.dry_run):
                    ledger.add("copy" if args.copy or os.name == "nt" else "link", d / src.name, src, "skills")

    if not args.no_shim:
        info("\n== codemap command")
        _install_shim(ledger, args.dry_run)

    if args.global_instructions:
        info("\n== global instructions")
        block = _global_instruction_block()
        for f in (Path("~/.claude/CLAUDE.md"), Path("~/.copilot/copilot-instructions.md"), Path("~/.codex/AGENTS.md")):
            f = f.expanduser()
            if f.parent.exists() or args.dry_run:
                _upsert_block(f, block, args.dry_run)
                ledger.add("block", f, None, "instructions")

    ledger.save(cfg, targets, args.bundle)
    if failures:
        info("\nsome installs failed (often: plugin not compatible with that client, or network):")
        for f in failures:
            info(f"  - {f}")
    info("\ndone. Check health any time with `toolkit.py doctor`; start your next task with `kickoff`.")
    return 0


def _link_or_copy(src: Path, dest: Path, copy: bool, dry_run: bool) -> bool:
    """Link or copy a skill directory. Returns False when dest belongs to the user and was left alone."""
    if dest.is_symlink() and dest.resolve() == src.resolve():
        return True
    if dest.exists() and not dest.is_symlink() and not (dest / ".ai-toolkit").exists():
        warn(f"{dest} exists and is not managed by ai-toolkit; leaving it")
        return False
    if dry_run:
        info(f"  [dry-run] {'copy' if copy else 'link'} {dest} -> {src}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        dest.unlink()
    elif dest.exists():
        shutil.rmtree(dest)
    if copy or os.name == "nt":
        shutil.copytree(src, dest)
        (dest / ".ai-toolkit").write_text(str(src) + "\n", encoding="utf-8")
    else:
        dest.symlink_to(src, target_is_directory=True)
    info(f"  {'copied' if copy else 'linked'} {dest.name}")
    return True


def _link_or_copy_file(src: Path, dest: Path, copy: bool, dry_run: bool, owned: bool = False) -> bool:
    """Link or copy one agent file. `owned`: the install ledger says a previous install wrote dest from src.
    Returns False when dest belongs to the user and was left alone."""
    if dest.is_symlink() and dest.resolve() == src.resolve():
        return True
    if dest.exists() and not dest.is_symlink() and not owned and not _same_file(dest, src):
        warn(f"{dest} exists and is not managed by ai-toolkit; leaving it")
        return False
    if dry_run:
        info(f"  [dry-run] {'copy' if copy else 'link'} {dest} -> {src}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        dest.unlink()  # a stale link or a copy this toolkit owns
    if copy or os.name == "nt":
        shutil.copy2(src, dest)
    else:
        dest.symlink_to(src)
    info(f"  {'copied' if copy else 'linked'} {dest.name}")
    return True


def _same_file(a: Path, b: Path) -> bool:
    try:
        return a.read_bytes() == b.read_bytes()
    except OSError:
        return False


def _global_instruction_block() -> str:
    return (f"{ADOPT_BEGIN}\n## AI toolkit\n\n"
            "For any substantial task, load the `kickoff` skill first: it routes the task to the right skills, "
            "agents and plugin commands, checks for gaps, and finishes with a harvest step that grows the toolkit.\n"
            "Look locally before remotely: read local clones, installed dependencies and local docs before querying "
            "remote MCP servers or the web for code or documentation.\n"
            f"Toolkit home: `{ROOT}` (catalog: `plugins/kickoff/skills/kickoff/references/catalog.tsv`).\n{ADOPT_END}\n")


def _upsert_block(path: Path, block: str, dry_run: bool) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(re.escape(ADOPT_BEGIN) + r".*?" + re.escape(ADOPT_END) + r"\n?", re.S)
    new = pattern.sub(lambda _: block, text) if pattern.search(text) else (text.rstrip() + "\n\n" if text.strip() else "") + block
    if new == text:
        return
    if dry_run:
        info(f"  [dry-run] update {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new, encoding="utf-8")
    info(f"  updated {path}")


# --------------------------------------------------------------------------- adopt

def _merge_json(path: Path, patch: dict, dry_run: bool) -> None:
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            die(f"{path} is not valid JSON; fix it or remove it before adopting")
    for key, val in patch.items():
        if isinstance(val, dict):
            data.setdefault(key, {})
            data[key].update(val)
        else:
            data[key] = val
    content = dump_json(data)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    if dry_run:
        info(f"  [dry-run] merge into {path}:\n" + "\n".join("      " + l for l in dump_json(patch).splitlines()))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    info(f"  updated {path}")


def _project_block(cfg: dict, plugins: list[str], vendored: bool) -> str:
    where = ("vendored into `.claude/skills/` and `.claude/agents/` (read by Claude Code and GitHub Copilot)"
             if vendored else "installed as plugins from the `ai-toolkit` marketplace (see `.claude/settings.json` "
             "and `.github/copilot/settings.json`)")
    return (f"{ADOPT_BEGIN}\n## AI toolkit\n\n"
            f"This repository uses [{cfg['name']}](https://github.com/{cfg['repository']}): {', '.join(f'`{p}`' for p in plugins)}, {where}.\n\n"
            "- Start every substantial task with the `kickoff` skill. It picks the skills, agents and commands for the task, "
            "says the route in one line, does the work, then runs `harvest`.\n"
            "- Harvested skills and agents for this project go in `.claude/skills/` and `.claude/agents/` so every client sees them; "
            "anything reusable across projects should be promoted to the toolkit (`toolkit.py promote`).\n"
            "- Gaps the toolkit could not fill are logged in `.github/ai-toolkit/gaps.md`.\n"
            f"{ADOPT_END}\n")


def cmd_adopt(args) -> int:
    cfg = load_config()
    proj = Path(args.project).expanduser().resolve()
    if not proj.is_dir():
        die(f"{proj} is not a directory")
    plugins = list(dict.fromkeys(args.plugin or cfg["bundles"][args.bundle]))
    for p in plugins:
        if p not in cfg["plugins"]:
            die(f"unknown toolkit plugin '{p}' (choose from: {', '.join(cfg['plugins'])})")
    upstream = [r for r in (args.upstream or [])]
    info(f"adopting into {proj} ({args.mode}): {', '.join(plugins)}" + (f" + {', '.join(upstream)}" if upstream else ""))
    lock_path = proj / ".github" / "ai-toolkit" / "lock.json"
    try:
        previous = json.loads(lock_path.read_text(encoding="utf-8")).get("vendored") or {}
    except (OSError, json.JSONDecodeError, AttributeError):
        previous = {}
    vendor = Vendor(proj, previous, args.force, args.dry_run)

    if args.mode == "plugins":
        src = {"source": "github", "repo": cfg["repository"]}
        markets = {LOCAL_MARKETPLACE: {"source": src}}
        mk_repo = {m["name"]: m["repo"] for m in cfg["upstream"]["marketplaces"]}
        for ref in upstream:
            name = ref.split("@", 1)[1]
            if name not in mk_repo:
                die(f"unknown marketplace in '{ref}'")
            markets[name] = {"source": {"source": "github", "repo": mk_repo[name]}}
        enabled = {f"{p}@{LOCAL_MARKETPLACE}": True for p in plugins}
        enabled.update({r: True for r in upstream})
        patch = {"extraKnownMarketplaces": markets, "enabledPlugins": enabled}
        # Claude Code (team settings) and Copilot CLI + Copilot cloud agent both honour these keys.
        _merge_json(proj / ".claude" / "settings.json", patch, args.dry_run)
        _merge_json(proj / ".github" / "copilot" / "settings.json", patch, args.dry_run)
    else:
        for pname in plugins:
            pdir = PLUGINS_DIR / pname
            for sdir in sorted((pdir / "skills").glob("*")):
                if (sdir / "SKILL.md").is_file():
                    vendor.tree(sdir, proj / ".claude" / "skills" / sdir.name)
            for af in sorted((pdir / "agents").glob("*.agent.md")):
                vendor.file(af, proj / ".claude" / "agents" / af.name.replace(".agent.md", ".md"))
                if args.github_agents:
                    vendor.file(af, proj / ".github" / "agents" / af.name)
            vend_root = f".github/ai-toolkit/plugins/{pname}"
            runtime = [d for d in ("scripts", "hooks") if (pdir / d).is_dir()]
            if (pdir / "scripts").is_dir() or (args.hooks and (pdir / "hooks").is_dir()):
                # Hooks and MCP servers need the plugin's runtime files inside the repo.
                for d in runtime:
                    vendor.tree(pdir / d, proj / vend_root / d)
            mcp_src = pdir / ".mcp.json"
            if mcp_src.is_file():
                # Project MCP config: Claude Code reads .mcp.json; Copilot CLI reads .mcp.json / .github/mcp.json.
                servers = json.loads(mcp_src.read_text(encoding="utf-8")).get("mcpServers") or {}
                servers = json.loads(json.dumps(servers).replace("${CLAUDE_PLUGIN_ROOT}", vend_root))
                _merge_json(proj / ".mcp.json", {"mcpServers": servers}, args.dry_run)
            cop_hooks = pdir / "hooks" / "copilot-hooks.json"
            if cop_hooks.exists() and args.hooks:
                # Repo-level hooks have no PLUGIN_ROOT: set it explicitly (relative to the repo root, the hook cwd).
                data = json.loads(cop_hooks.read_text(encoding="utf-8"))
                for entries in data.get("hooks", {}).values():
                    for e in entries:
                        e.setdefault("env", {})["PLUGIN_ROOT"] = vend_root
                content = dump_json(data)
                dest = proj / ".github" / "hooks" / f"ai-toolkit-{pname}.json"
                if args.dry_run:
                    info(f"  [dry-run] write {dest}")
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    info(f"  wrote {dest.relative_to(proj)}")

    if args.review_workflow:
        wf = proj / ".github" / "workflows" / "change-map.yml"
        body = REVIEW_WORKFLOW.replace("__REPO__", cfg["repository"]).replace("__REF__", args.review_ref)
        if wf.exists() and wf.read_text(encoding="utf-8") != body and not args.force:
            warn(f"{wf} exists and differs; pass --force to overwrite")
        elif args.dry_run:
            info(f"  [dry-run] write {wf}")
        else:
            wf.parent.mkdir(parents=True, exist_ok=True)
            wf.write_text(body, encoding="utf-8")
            info(f"  wrote {wf.relative_to(proj)} (PR change map: sticky comment, job summary, HTML report, AI-review pack)")

    block = _project_block(cfg, plugins, args.mode == "vendor")
    _upsert_block(proj / "AGENTS.md", block, args.dry_run)
    claude_md = proj / "CLAUDE.md"
    if not claude_md.exists():
        if args.dry_run:
            info(f"  [dry-run] create {claude_md} importing AGENTS.md")
        else:
            claude_md.write_text("@AGENTS.md\n", encoding="utf-8")
            info("  created CLAUDE.md (imports AGENTS.md)")
    elif "@AGENTS.md" not in claude_md.read_text(encoding="utf-8"):
        _upsert_block(claude_md, f"{ADOPT_BEGIN}\n@AGENTS.md\n{ADOPT_END}\n", args.dry_run)

    gaps = proj / ".github" / "ai-toolkit" / "gaps.md"
    if not gaps.exists():
        if args.dry_run:
            info(f"  [dry-run] create {gaps}")
        else:
            gaps.parent.mkdir(parents=True, exist_ok=True)
            gaps.write_text(GAPS_TEMPLATE, encoding="utf-8")
            info(f"  created {gaps.relative_to(proj)}")

    lock = {"toolkit": cfg["repository"], "version": cfg["version"], "commit": _git_head(), "mode": args.mode,
            "plugins": plugins, "upstream": upstream, "adopted": _dt.date.today().isoformat()}
    if args.mode == "vendor":
        # Keep the recorded hash of anything skipped, so a later run still recognises it as customised.
        lock["vendored"] = {**{k: v for k, v in previous.items() if k in vendor.skipped}, **vendor.hashes}
    if args.dry_run:
        info(f"  [dry-run] write {lock_path}")
    else:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(dump_json(lock), encoding="utf-8")
    if vendor.skipped:
        info(f"adopt complete, but {len(vendor.skipped)} locally customised path(s) were left as they are (see warnings).")
        return 1
    info("adopt complete. Review the diff, then commit it in that repository.")
    return 0


REVIEW_WORKFLOW = """name: change-map

# Structural, risk-ranked change map on every pull request (ai-toolkit codemap review).
# Posts a sticky PR comment with a Mermaid dependency view, writes the job summary,
# and uploads an interactive HTML report plus an AI-review pack (review-pack.txt).
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read
  pull-requests: write

jobs:
  change-map:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # the base commit must be available
      # Pin to a commit SHA for supply-chain safety, e.g. __REPO__/.github/actions/change-map@<sha>
      - uses: __REPO__/.github/actions/change-map@__REF__
        id: map
      # Optional: hand the review pack to an AI reviewer step, e.g. include
      # ${{ steps.map.outputs.review-pack }} in its prompt.
"""


GAPS_TEMPLATE = """# Toolkit gaps

Kickoff appends here when a task had no good route, or a tool fell short. Harvest closes a gap by
building a skill, agent or hook, or by installing an existing plugin from the catalog.

| Date | Task | Gap | Resolution |
|---|---|---|---|
"""


def _git_head() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or None
    except FileNotFoundError:
        return None


class Vendor:
    """Copies toolkit files into a repo, but never overwrites a copy someone edited after the last adopt.

    lock.json records the hash of every vendored path; a destination whose current hash matches neither that
    record nor the new source is a local customisation and is skipped unless --force.
    """

    def __init__(self, proj: Path, previous: dict, force: bool, dry_run: bool):
        self.proj, self.previous, self.force, self.dry_run = proj, previous, force, dry_run
        self.hashes: dict = {}
        self.skipped: list = []

    def _ok_to_write(self, src: Path, dest: Path) -> bool:
        rel = dest.relative_to(self.proj).as_posix()
        if not dest.exists() or self.force:
            return True
        current = _tree_hash(dest)
        if current in (_tree_hash(src), self.previous.get(rel)):
            return True
        self.skipped.append(rel)
        warn(f"{rel} has local changes since the last adopt; leaving it (pass --force to overwrite, "
             f"or `toolkit.py promote` to keep the change in the toolkit)")
        return False

    def tree(self, src: Path, dest: Path) -> None:
        if not self._ok_to_write(src, dest):
            return
        self.hashes[dest.relative_to(self.proj).as_posix()] = _tree_hash(src)
        if self.dry_run:
            info(f"  [dry-run] copy {src.relative_to(ROOT)} -> {dest}")
            return
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__"))
        info(f"  vendored {dest}")

    def file(self, src: Path, dest: Path) -> None:
        if not self._ok_to_write(src, dest):
            return
        self.hashes[dest.relative_to(self.proj).as_posix()] = _tree_hash(src)
        if self.dry_run:
            info(f"  [dry-run] copy {src.relative_to(ROOT)} -> {dest}")
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        info(f"  vendored {dest}")


# --------------------------------------------------------------------------- promote

def cmd_promote(args) -> int:
    cfg = load_config()
    src = Path(args.path).expanduser().resolve()
    if args.plugin not in cfg["plugins"]:
        die(f"unknown plugin '{args.plugin}'")
    if (src / "SKILL.md").is_file():
        fm = parse_frontmatter((src / "SKILL.md").read_text(encoding="utf-8"))
        name = fm.get("name") or src.name
        dest = PLUGINS_DIR / args.plugin / "skills" / name
    elif src.is_file() and src.suffix == ".md":
        fm = parse_frontmatter(src.read_text(encoding="utf-8"))
        name = fm.get("name") or src.stem.replace(".agent", "")
        dest = PLUGINS_DIR / args.plugin / "agents" / f"{name}.agent.md"
    else:
        die("path must be a skill directory (with SKILL.md) or an agent .md file")
    if not NAME_RE.match(name):
        die(f"name '{name}' must be lowercase-hyphenated")
    clash = [p for p in PLUGINS_DIR.glob(f"*/skills/{name}") if p != dest]
    if clash and not args.force:
        die(f"a skill named '{name}' already exists at {clash[0].relative_to(ROOT)}; improve it instead or pass --force")
    if dest.exists() and not args.force:
        die(f"{dest.relative_to(ROOT)} exists; pass --force to overwrite")
    if args.dry_run:
        info(f"  [dry-run] copy {src} -> {dest}")
    elif src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)  # --force was given (checked above)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    if not args.dry_run:
        cmd_build(argparse.Namespace(check=False))
        info("promoted. Run `python3 scripts/toolkit.py validate`, then commit and push so other devices get it.")
    return 0


# --------------------------------------------------------------------------- doctor

def _tree_hash(path: Path) -> str | None:
    import hashlib
    h = hashlib.sha1()
    try:
        if path.is_file():
            return hashlib.sha1(path.read_bytes()).hexdigest()
        for f in sorted(path.rglob("*")):
            if f.is_file() and f.name != ".ai-toolkit" and "__pycache__" not in f.parts:
                h.update(str(f.relative_to(path)).encode())
                h.update(f.read_bytes())
    except OSError:
        return None
    return h.hexdigest()


def _toolkit_index(cfg: dict) -> tuple[dict, dict]:
    skills = {s.parent.name: s.parent for s in PLUGINS_DIR.glob("*/skills/*/SKILL.md")}
    agents = {a.name[: -len(".agent.md")]: a for a in PLUGINS_DIR.glob("*/agents/*.agent.md")}
    return skills, agents


def doctor_findings(cfg: dict, repo: Path | None, quick: bool = False) -> list:
    """Return [(severity, message, fix_callable_or_None)]."""
    found = []
    skills, agents = _toolkit_index(cfg)

    # Toolkit checkout itself.
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip() \
        if shutil.which("git") and (ROOT / ".git").exists() else ""
    if dirty:
        n = len(dirty.splitlines())
        found.append(("warn", f"toolkit has {n} uncommitted change(s) (harvested work?). Commit and push so other devices get them.", None))
    if CATALOG_TSV.exists():
        m = re.search(r"generated (\d{4}-\d{2}-\d{2})", CATALOG_TSV.read_text(encoding="utf-8")[:400])
        if m and (_dt.date.today() - _dt.date.fromisoformat(m.group(1))).days > 14:
            found.append(("info", f"catalog is from {m.group(1)}; run `toolkit.py catalog` to discover new upstream plugins", None))

    # Everything install wrote.
    ledger = Ledger(dry_run=False)
    if not ledger.entries:
        found.append(("info", "no install ledger on this device; run `toolkit.py install`", None))
    for path_s, e in sorted(ledger.entries.items()):
        path = Path(path_s)
        src = Path(e["source"]) if e.get("source") else None
        if e["kind"] in ("link", "copy") and src is not None:
            owned = _toolkit_owned(path, e["kind"])
            if not path.exists() and not path.is_symlink():
                found.append(("warn", f"{path} is missing; re-run `toolkit.py install`", None))
            elif not owned:
                found.append(("warn", f"{path} was replaced by something the toolkit did not write; leaving it "
                              "(remove it yourself and re-run install to restore the toolkit version)", None))
            elif not src.exists():
                found.append(("warn", f"{path} points at a removed toolkit item ({src.name}); remove it",
                              lambda path=path: (path.unlink() if path.is_symlink() or path.is_file() else shutil.rmtree(path, ignore_errors=True))))
            elif e["kind"] == "link" and path.resolve() != src.resolve():
                found.append(("warn", f"{path} is no longer linked to the toolkit; relink",
                              lambda path=path, src=src: _relink(path, src)))
            elif e["kind"] == "copy" and _tree_hash(path) != _tree_hash(src):
                found.append(("warn", f"{path} is a stale copy of {src.name}; refresh",
                              lambda path=path, src=src: _recopy(path, src)))
        elif e["kind"] == "file" and not path.exists():
            found.append(("warn", f"{path} is missing; re-run `toolkit.py install`", None))

    # New toolkit items not yet installed for a target that is in use.
    targets = set(ledger.data.get("targets", []))
    installed = {Path(e["source"]).name.replace(".agent.md", "") for e in ledger.entries.values()
                 if e.get("source") and e["kind"] in ("link", "copy")}
    if targets & {"copilot-user", "claude-user", "skills"}:
        bundle = ledger.data.get("bundle", "full")
        wanted = {src.name.replace(".agent.md", "") for _p, _k, src in _bundle_items(cfg, bundle)} \
            if bundle in cfg["bundles"] else set(skills) | set(agents)
        new = sorted(wanted - installed)
        if new:
            found.append(("info", f"{len(new)} toolkit skill/agent(s) not installed at user level yet: {', '.join(new[:8])}"
                          f"{' …' if len(new) > 8 else ''}; re-run `toolkit.py install`", None))

    if shutil.which("codemap") is None and (PLUGINS_DIR / "codemap").is_dir():
        found.append(("info", "`codemap` is not on PATH (agents can still use the MCP tool); run `toolkit.py install`", None))

    if quick or repo is None:
        return found

    # Repository checks: vendored copies vs user-level installs (Copilot: project skills shadow personal ones).
    user_level = any(t in targets for t in ("copilot-user", "claude-user", "skills", "claude", "copilot"))
    for base in (".github/skills", ".claude/skills", ".agents/skills"):
        d = repo / base
        if not d.is_dir():
            continue
        for sdir in sorted(x for x in d.iterdir() if (x / "SKILL.md").is_file()):
            src = skills.get(sdir.name)
            if src is None:
                continue
            if _tree_hash(sdir) == _tree_hash(src):
                msg = (f"{base}/{sdir.name} duplicates the toolkit skill"
                       + (" you already have at user level; project copies shadow personal ones and add listing tokens"
                          if user_level else ""))
                found.append(("warn" if user_level else "info", msg,
                              (lambda sdir=sdir: shutil.rmtree(sdir)) if user_level else None))
            else:
                found.append(("warn", f"{base}/{sdir.name} differs from the toolkit version (stale vendored copy, or a local "
                              f"customization). Compare, then `adopt --mode vendor` to update or `promote` to keep it.", None))
    for base, suffix in ((".github/agents", ".agent.md"), (".claude/agents", ".md")):
        d = repo / base
        if not d.is_dir():
            continue
        for af in sorted(d.glob("*" + suffix)):
            name = af.name[: -len(suffix)]
            src = agents.get(name)
            if src is None:
                continue
            if _same_file(af, src):
                found.append(("info", f"{base}/{af.name} duplicates the toolkit agent (Copilot prefers the personal one)",
                              (lambda af=af: af.unlink()) if user_level else None))
            else:
                found.append(("warn", f"{base}/{af.name} differs from the toolkit agent (stale or customized)", None))
    lock = repo / ".github" / "ai-toolkit" / "lock.json"
    if lock.is_file():
        try:
            lk = json.loads(lock.read_text(encoding="utf-8"))
            if lk.get("version") != cfg["version"]:
                found.append(("info", f"repo adopted toolkit v{lk.get('version')}; current is v{cfg['version']}. "
                              f"Re-run `toolkit.py adopt {repo} --mode {lk.get('mode', 'plugins')}` to update.", None))
            gone = [p for p in lk.get("plugins", []) if p not in cfg["plugins"]]
            if gone:
                found.append(("warn", f"repo enables toolkit plugins that no longer exist: {', '.join(gone)}", None))
        except json.JSONDecodeError:
            found.append(("warn", f"{lock} is not valid JSON", None))
    for sf in (repo / ".github" / "copilot" / "settings.json", repo / ".claude" / "settings.json"):
        if sf.is_file():
            try:
                enabled = json.loads(sf.read_text(encoding="utf-8")).get("enabledPlugins") or {}
            except json.JSONDecodeError:
                continue
            stale = [k for k in enabled if k.endswith("@" + LOCAL_MARKETPLACE) and k.split("@")[0] not in cfg["plugins"]]
            if stale:
                found.append(("warn", f"{sf.relative_to(repo)} enables unknown toolkit plugins: {', '.join(stale)}", None))
    return found


def _toolkit_owned(path: Path, kind: str) -> bool:
    """Whether doctor may replace or delete `path`: a symlink, a marked copied directory, or a copied file."""
    if path.is_symlink():
        return True
    if kind == "link":
        return False  # the toolkit wrote a link here; a real file or directory now means the user replaced it
    if path.is_dir():
        return (path / ".ai-toolkit").exists()
    return path.is_file()


def _relink(path: Path, src: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
    path.symlink_to(src, target_is_directory=src.is_dir())


def _recopy(path: Path, src: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        shutil.copytree(src, path)
        (path / ".ai-toolkit").write_text(str(src) + "\n", encoding="utf-8")
    else:
        shutil.copy2(src, path)


def cmd_doctor(args) -> int:
    cfg = load_config()
    repo = None
    if not args.quick:
        cand = Path(args.repo).expanduser().resolve() if args.repo else Path.cwd()
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cand, capture_output=True, text=True)
        repo = Path(top.stdout.strip()) if top.returncode == 0 else cand
        if repo.resolve() == ROOT.resolve():
            repo = None  # the toolkit itself: vendored-copy checks do not apply
    found = doctor_findings(cfg, repo, args.quick)
    if args.summary:
        warns = sum(1 for s, _, _ in found if s == "warn")
        if warns:
            print(f"toolkit doctor: {warns} issue(s); run `python3 {ROOT / 'scripts' / 'toolkit.py'} doctor`")
        return 0
    if not found:
        info("doctor: all good")
        return 0
    fixed = 0
    for sev, msg, fix in found:
        mark = {"warn": "!", "info": "·"}[sev]
        info(f"{mark} {msg}" + (" [fixable]" if fix and not args.fix else ""))
        if fix and args.fix:
            try:
                fix()
                fixed += 1
                info("  fixed")
            except OSError as e:
                warn(f"  fix failed: {e}")
    if args.fix:
        info(f"doctor: fixed {fixed} of {sum(1 for f in found if f[2])} fixable issue(s)")
    elif any(f[2] for f in found):
        info("run with --fix to apply the fixable ones")
    return 1 if any(s == "warn" for s, _, f in found if not (args.fix and f)) else 0


# --------------------------------------------------------------------------- audit

STOPWORDS = set("""a an and or the of to in on for with when use using this that is are be it as at by from how what
your you any into about while should can will not do does its their them they has have was were if then than so such
via per also more most less only just each every over under before after during without within these those which""".split())


def _words(text: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z-]{2,}", text.lower()) if w not in STOPWORDS}


def _git_age_days(path: Path) -> int | None:
    out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(path)], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if not out:
        return None
    return int((_dt.datetime.now().timestamp() - int(out)) // 86400)


def cmd_audit(args) -> int:
    """Token cost and freshness of the toolkit's own skills, agents and routes."""
    cfg = load_config()
    lines, problems = [], 0
    per_plugin = {}
    skill_rows = []
    for pdir in own_plugin_dirs():
        inv = inventory_plugin(pdir)
        always = sum(est_tokens(f"{s['name']}: {s['description']}") for s in inv["skills"]) + \
            sum(est_tokens(f"{a['name']}: {a['description']}") for a in inv["agents"])
        mcp = 0
        if (pdir / ".mcp.json").is_file():
            mcp = 150  # one compact tool schema
        per_plugin[pdir.name] = always + mcp
        for sf in sorted((pdir / "skills").glob("*/SKILL.md")):
            text = sf.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            body = text.split("\n---", 2)[-1]
            skill_rows.append((pdir.name, fm.get("name", sf.parent.name), fm.get("description", ""), est_tokens(body), sf))
    lines.append("Always-on cost (skill/agent listings + MCP schemas, paid every request):")
    for b, members in cfg["bundles"].items():
        lines.append(f"  bundle {b:5} ~{sum(per_plugin.get(m, 0) for m in members):5,} tokens  ({', '.join(f'{m} {per_plugin.get(m, 0)}' for m in members)})")

    lines.append("\nSkills to tighten:")
    n0 = len(lines)
    for plugin, name, desc, body_tok, sf in skill_rows:
        issues = []
        if len(desc) > 700:
            issues.append(f"description {len(desc)} chars (aim ≤ 700; it is paid on every request)")
        if not re.search(r"\b(use|when|trigger)\b", desc, re.I):
            issues.append("description has no 'use when…' trigger")
        if body_tok > 4000:
            issues.append(f"body ~{body_tok} tokens (split detail into references/)")
        if issues:
            lines.append(f"  {name} ({plugin}): " + "; ".join(issues))
    if len(lines) == n0:
        lines.append("  none")

    lines.append("\nPossible overlaps (merge or sharpen the descriptions):")
    n0 = len(lines)
    ws = [(n, _words(d)) for _, n, d, _, _ in skill_rows]
    for i in range(len(ws)):
        for j in range(i + 1, len(ws)):
            a, b = ws[i][1], ws[j][1]
            if a and b:
                jac = len(a & b) / len(a | b)
                if jac >= args.overlap:
                    lines.append(f"  {ws[i][0]} ↔ {ws[j][0]} ({jac:.0%} shared vocabulary)")
    if len(lines) == n0:
        lines.append("  none")

    lines.append("\nRouting table freshness (kickoff):")
    n0 = len(lines)
    known = set()
    if CATALOG_TSV.exists():
        for row in CATALOG_TSV.read_text(encoding="utf-8").splitlines():
            parts = row.split("\t")
            if len(parts) >= 3 and not row.startswith("#"):
                known.add(parts[1])
                known.add(parts[2].split("@")[0])
    known |= set(cfg["app_builtins"]["skills"]) | {"Explore"}
    kick = (PLUGINS_DIR / "kickoff" / "skills" / "kickoff" / "SKILL.md").read_text(encoding="utf-8")
    table = kick[kick.find("## Routing table"): kick.find("## Availability")]
    table = re.sub(r"\([^()]*\)", "", table)  # parenthesised usage notes hold sub-commands, not tool names
    for tool in sorted(set(re.findall(r"`([a-z][a-z0-9-]+)`", table))):
        if tool not in known:
            problems += 1
            lines.append(f"  `{tool}` is not in the catalog (renamed or removed upstream?)")
    for ref in profile_refs(cfg):
        if CATALOG_TSV.exists() and f"\t{ref}\t" not in CATALOG_TSV.read_text(encoding="utf-8"):
            problems += 1
            lines.append(f"  profile plugin {ref} is no longer in its marketplace")
    if len(lines) == n0:
        lines.append("  all routes resolve")

    if not args.no_git:
        lines.append(f"\nNot touched in {args.stale_days}+ days (review, refresh or retire):")
        n0 = len(lines)
        for plugin, name, _d, _b, sf in skill_rows:
            age = _git_age_days(sf)
            if age is not None and age >= args.stale_days:
                lines.append(f"  {name} ({plugin}) — {age} days")
        if len(lines) == n0:
            lines.append("  none")
    print("\n".join(lines))
    return 1 if (problems and args.strict) else 0


# --------------------------------------------------------------------------- sync / status

def cmd_sync(args) -> int:
    cfg = load_config()
    failed = []
    if (ROOT / ".git").exists() and run(["git", "pull", "--ff-only"], args.dry_run, cwd=ROOT) != 0:
        warn("git pull failed (uncommitted or diverged changes?); fix the checkout, then sync again")
        return 1  # updating plugins from a stale checkout would report success for old content
    for cli in ("claude", "copilot"):
        if shutil.which(cli) or args.dry_run:
            info(f"\n== {cli}")
            if run([cli, "plugin", "marketplace", "update", LOCAL_MARKETPLACE], args.dry_run) != 0:
                failed.append(f"{cli} marketplace update")
            for p in cfg["plugins"]:
                if run([cli, "plugin", "update", f"{p}@{LOCAL_MARKETPLACE}"], args.dry_run) != 0:
                    failed.append(f"{cli} {p}")
    if failed:
        warn(f"sync finished with {len(failed)} failure(s): {', '.join(failed)}")
        return 1
    return 0


def cmd_status(args) -> int:
    cfg = load_config()
    info(f"toolkit: {ROOT} (v{cfg['version']}, commit {(_git_head() or '?')[:8]})")
    marker = toolkit_home_marker()
    info(f"home marker: {marker} -> {marker.read_text().strip() if marker.exists() else 'not set (run install)'}")
    for cli in ("claude", "copilot", "code"):
        info(f"{cli:8} {'found' if shutil.which(cli) else 'not found'}")
    for d in ("~/.agents/skills", "~/.copilot/skills", "~/.claude/skills"):
        p = Path(d).expanduser()
        if p.is_dir():
            def managed(x: Path) -> bool:
                if x.is_symlink():
                    return str(x.resolve()).startswith(str(PLUGINS_DIR))
                return (x / ".ai-toolkit").exists()
            info(f"{d}: {sum(managed(x) for x in p.iterdir())} toolkit skills")
    n_skills = len(list(PLUGINS_DIR.glob("*/skills/*/SKILL.md")))
    n_agents = len(list(PLUGINS_DIR.glob("*/agents/*.agent.md")))
    info(f"toolkit content: {len(cfg['plugins'])} plugins, {n_skills} skills, {n_agents} agents, {len(profile_refs(cfg))} upstream plugins in profile")
    return 0


# --------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="toolkit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="regenerate plugin manifests, marketplaces and README tables")
    b.add_argument("--check", action="store_true", help="fail if anything is out of date instead of writing")
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("validate", help="lint skills, agents, hooks and generated files")
    v.set_defaults(func=cmd_validate)

    c = sub.add_parser("catalog", help="rescan upstream marketplaces into catalog/ and the kickoff catalog.tsv")
    c.add_argument("--deep", action="store_true", help="also clone externally-hosted plugins to list their components")
    c.add_argument("--only", nargs="*", help="limit to these marketplace names")
    c.add_argument("--cache", help="clone cache directory (default: system temp)")
    c.set_defaults(func=cmd_catalog)

    i = sub.add_parser("install", help="set up this device")
    i.add_argument("--target", action="append", choices=["auto", "claude", "copilot", "copilot-user", "claude-user", "skills"],
                   help="where to install (repeatable). claude/copilot = plugins via the CLI; copilot-user = ~/.copilot "
                        "skills/agents/hooks/MCP (Copilot's user-level layout); claude-user = ~/.claude without plugins; "
                        "skills = ~/.agents/skills. Default auto = claude (if found) + copilot-user (if Copilot is set up) + skills")
    i.add_argument("--bundle", default="full", help="which toolkit bundle (see toolkit.json bundles)")
    i.add_argument("--no-upstream", action="store_true", help="skip the Anthropic/GitHub/partner plugin profile")
    i.add_argument("--local", action="store_true", help="register this checkout as the marketplace instead of GitHub")
    i.add_argument("--skills-dir", action="append", help="skills directory to link into (default ~/.agents/skills)")
    i.add_argument("--copy", action="store_true", help="copy skills instead of symlinking")
    i.add_argument("--no-shim", action="store_true", help="do not put a `codemap` command in ~/.local/bin")
    i.add_argument("--global-instructions", action="store_true",
                   help="add a kickoff pointer to ~/.claude/CLAUDE.md, ~/.copilot/copilot-instructions.md, ~/.codex/AGENTS.md")
    i.add_argument("--dry-run", action="store_true")
    i.set_defaults(func=cmd_install)

    a = sub.add_parser("adopt", help="wire the toolkit into another repository")
    a.add_argument("project", help="path to the target repository")
    a.add_argument("--mode", choices=["plugins", "vendor"], default="plugins",
                   help="plugins: declare marketplace + enabledPlugins (Claude Code, Copilot CLI, Copilot cloud agent). "
                        "vendor: copy skills/agents into the repo (works in any client, incl. VS Code and Codex)")
    a.add_argument("--bundle", default="dev")
    a.add_argument("--plugin", action="append", help="toolkit plugin to include (repeatable; overrides --bundle)")
    a.add_argument("--upstream", action="append", help="also enable plugin@marketplace from the profile (plugins mode)")
    a.add_argument("--github-agents", action="store_true", help="vendor mode: also write .github/agents/*.agent.md")
    a.add_argument("--hooks", action="store_true", help="vendor mode: also install Copilot hooks into .github/hooks/")
    a.add_argument("--review-workflow", action="store_true",
                   help="add .github/workflows/change-map.yml: change map on every PR (comment, summary, HTML report)")
    a.add_argument("--review-ref", default="main", help="toolkit ref for the change-map action (pin a SHA in production)")
    a.add_argument("--force", action="store_true", help="overwrite an existing, different change-map workflow and locally customised vendored files")
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(func=cmd_adopt)

    p = sub.add_parser("promote", help="move a project-local skill or agent into the toolkit")
    p.add_argument("path")
    p.add_argument("--plugin", required=True, help="toolkit plugin to put it in")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_promote)

    d = sub.add_parser("doctor", help="check this device (and a repo) for stale, broken or shadowing toolkit installs")
    d.add_argument("--repo", help="repository to check (default: current directory)")
    d.add_argument("--fix", action="store_true", help="apply safe fixes (relink, refresh copies, drop duplicate vendored copies)")
    d.add_argument("--quick", action="store_true", help="device checks only, no repository scan")
    d.add_argument("--summary", action="store_true", help="one line, only when there are issues (for hooks)")
    d.set_defaults(func=cmd_doctor)

    au = sub.add_parser("audit", help="token cost, overlaps, stale routes and stale skills in the toolkit")
    au.add_argument("--overlap", type=float, default=0.3, help="vocabulary overlap threshold (default 0.3)")
    au.add_argument("--stale-days", type=int, default=180)
    au.add_argument("--no-git", action="store_true", help="skip git age checks")
    au.add_argument("--strict", action="store_true", help="exit 1 when routes or profile entries are stale")
    au.set_defaults(func=cmd_audit)

    s = sub.add_parser("sync", help="git pull and update installed toolkit plugins")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_sync)

    st = sub.add_parser("status", help="show what is installed")
    st.set_defaults(func=cmd_status)

    args = ap.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
