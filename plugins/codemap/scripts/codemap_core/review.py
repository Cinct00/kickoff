"""Structural change analysis for code review.

Turns `git diff BASE [HEAD]` into: per-file status and churn, symbol-level
changes (added / removed / modified / signature / renamed / moved), callers
outside the diff that a signature change or removal may break, affected and
missing tests, dependency changes, and a risk-ranked review order. Renderers
live in review_render.py.
"""
from __future__ import annotations

import math
import os
import posixpath
import re
import subprocess
from dataclasses import dataclass, field

from .extract import extract
from .manifests import is_manifest, parse_manifest_text
from .queries import PACKAGE_SCOPED, Q
from .util import est_tokens, is_test_path, lang_of

WORKTREE = "WORKTREE"
MAX_HUNK_LINES_PER_FILE = 400
SENSITIVE = re.compile(
    r"(auth|login|session|token|secret|password|passwd|credential|crypt|permission|acl|rbac|oauth|jwt|payment|billing|"
    r"invoice|migration|schema|\.github/workflows/|dockerfile|docker-compose|terraform|\.tf$|helm|k8s|kubernetes|"
    r"security|sanitiz|escape|csrf|cors|firewall|iam)", re.I)
GENERATED = re.compile(r"(\.lock$|-lock\.json$|\.lock\.json$|\.min\.(js|css)$|\.snap$|/vendor/|/dist/|/generated/|"
                       r"\.g\.cs$|_pb2\.py$|\.pb\.go$|\.designer\.cs$|go\.sum$|pnpm-lock\.yaml$|yarn\.lock$)", re.I)


class ReviewError(Exception):
    pass


@dataclass
class Hunk:
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    header: str
    lines: list = field(default_factory=list)  # (tag, text) tag in ' ', '+', '-'
    old_changed: set = field(default_factory=set)
    new_changed: set = field(default_factory=set)


@dataclass
class FileDiff:
    path: str
    old_path: str
    status: str  # A M D R
    binary: bool = False
    added: int = 0
    deleted: int = 0
    hunks: list = field(default_factory=list)


# --------------------------------------------------------------------------- git

def _git(root, *args, check=True) -> str:
    proc = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        raise ReviewError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def resolve_base(root, base: str | None) -> tuple[str, str]:
    """Return (sha, label). Default: merge-base of HEAD with the default branch."""
    if base:
        sha = _git(root, "rev-parse", "--verify", base + "^{commit}", check=False).strip()
        if not sha:
            raise ReviewError(f"unknown base ref '{base}' (fetch it first: git fetch origin {base})")
        mb = _git(root, "merge-base", sha, "HEAD", check=False).strip()
        return (mb or sha), base
    cands = []
    if os.environ.get("CODEMAP_REVIEW_BASE"):
        cands.append(os.environ["CODEMAP_REVIEW_BASE"])
    if os.environ.get("GITHUB_BASE_REF"):
        cands.append("origin/" + os.environ["GITHUB_BASE_REF"])
    head_ref = _git(root, "symbolic-ref", "-q", "refs/remotes/origin/HEAD", check=False).strip()
    if head_ref:
        cands.append(head_ref.replace("refs/remotes/", ""))
    cands += ["origin/main", "origin/master", "main", "master"]
    current = _git(root, "rev-parse", "--abbrev-ref", "HEAD", check=False).strip()
    for c in cands:
        if c == current:
            continue
        sha = _git(root, "rev-parse", "--verify", "-q", c + "^{commit}", check=False).strip()
        if sha:
            mb = _git(root, "merge-base", sha, "HEAD", check=False).strip()
            if mb:
                return mb, c
    sha = _git(root, "rev-parse", "--verify", "-q", "HEAD~1", check=False).strip()
    if sha:
        return sha, "HEAD~1"
    raise ReviewError("no base to compare against: pass --base REF (e.g. origin/main)")


def parse_patch(text: str) -> list:
    files, cur, hunk = [], None, None
    old_ln = new_ln = 0
    for line in text.split("\n"):
        if line.startswith("diff --git "):
            cur = FileDiff(path="", old_path="", status="M")
            files.append(cur)
            hunk = None
            m = re.match(r"diff --git a/(.*) b/(.*)$", line)
            if m:
                cur.old_path, cur.path = m.group(1), m.group(2)
            continue
        if cur is None:
            continue
        if hunk is None:  # file headers only appear before the file's first hunk
            if line.startswith("new file mode"):
                cur.status = "A"
                continue
            if line.startswith("deleted file mode"):
                cur.status = "D"
                continue
            if line.startswith("rename from "):
                cur.status, cur.old_path = "R", line[len("rename from "):]
                continue
            if line.startswith("rename to "):
                cur.path = line[len("rename to "):]
                continue
            if line.startswith("Binary files") or line.startswith("GIT binary patch"):
                cur.binary = True
                continue
            if line.startswith("--- "):
                if line[4:] != "/dev/null":
                    cur.old_path = line[6:] if line.startswith("--- a/") else line[4:]
                continue
            if line.startswith("+++ "):
                if line[4:] != "/dev/null":
                    cur.path = line[6:] if line.startswith("+++ b/") else line[4:]
                continue
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)", line)
        if m:
            hunk = Hunk(int(m.group(1)), int(m.group(2) or 1), int(m.group(3)), int(m.group(4) or 1), m.group(5).strip())
            cur.hunks.append(hunk)
            old_ln, new_ln = hunk.old_start, hunk.new_start
            continue
        if hunk is None or not line or line.startswith("\\"):
            continue
        tag, body = line[0], line[1:]
        if tag == "+":
            hunk.lines.append(("+", body))
            hunk.new_changed.add(new_ln)
            new_ln += 1
            cur.added += 1
        elif tag == "-":
            hunk.lines.append(("-", body))
            hunk.old_changed.add(old_ln)
            old_ln += 1
            cur.deleted += 1
        elif tag == " ":
            hunk.lines.append((" ", body))
            old_ln += 1
            new_ln += 1
    for f in files:
        if f.status == "D":
            f.path = f.old_path
        if f.status == "A":
            f.old_path = f.path
    return [f for f in files if f.path]


def collect_diff(root, base_sha: str, head: str) -> list:
    args = ["diff", "--no-color", "--no-ext-diff", "-M", "-U3", base_sha]
    if head != WORKTREE:
        args.append(head)
    files = parse_patch(_git(root, *args))
    if head == WORKTREE:
        seen = {f.path for f in files}
        for p in _git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
            if not p or p in seen:
                continue
            try:
                text = (root / p).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                files.append(FileDiff(path=p, old_path=p, status="A", binary=True))
                continue
            lines = text.split("\n")
            if lines and lines[-1] == "":
                lines.pop()
            h = Hunk(0, 0, 1, len(lines), "", [("+", l) for l in lines], set(), set(range(1, len(lines) + 1)))
            files.append(FileDiff(path=p, old_path=p, status="A", added=len(lines), hunks=[h]))
    return files


def file_text(root, ref: str, path: str) -> str:
    if ref == WORKTREE:
        try:
            return (root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
    return _git(root, "show", f"{ref}:{path}", check=False)


# --------------------------------------------------------------------------- symbols

def _keyed(symbols) -> dict:
    out, seen = {}, {}
    for i, s in enumerate(symbols):
        base = (s.qualname or s.name, s.kind.replace("method", "function"))
        n = seen.get(base, 0)
        seen[base] = n + 1
        out[base + (n,)] = i
    return out


def _own_lines(symbols, i) -> set:
    s = symbols[i]
    own = set(range(s.line, s.end_line + 1))
    for c in symbols:
        if c.parent == i:
            own -= set(range(c.line, c.end_line + 1))
    return own


def _norm_body(text_lines, s, name) -> str:
    body = "\n".join(text_lines[s.line - 1:s.end_line])
    body = re.sub(r"\b" + re.escape(name) + r"\b", "§", body)
    return re.sub(r"\s+", " ", body).strip()


def _norm_sig(sig: str) -> str:
    return re.sub(r"\s+", "", sig or "")


def symbol_changes(path, lang, old_text, new_text, fd: FileDiff) -> list:
    old_f = extract(old_text, lang) if old_text else None
    new_f = extract(new_text, lang) if new_text else None
    olds = old_f.symbols if old_f else []
    news = new_f.symbols if new_f else []
    old_lines, new_lines = old_text.split("\n"), new_text.split("\n")
    old_changed = set().union(*(h.old_changed for h in fd.hunks)) if fd.hunks else set()
    new_changed = set().union(*(h.new_changed for h in fd.hunks)) if fd.hunks else set()
    ok, nk = _keyed(olds), _keyed(news)
    out = []
    for key, ni in nk.items():
        n = news[ni]
        if key not in ok:
            continue
        o = olds[ok[key]]
        own_new, own_old = _own_lines(news, ni), _own_lines(olds, ok[key])
        touched = len(own_new & new_changed) + len(own_old & old_changed)
        if _norm_sig(o.signature) != _norm_sig(n.signature):
            out.append({"change": "signature", "kind": n.kind, "name": n.name, "qualname": n.qualname, "line": n.line,
                        "end_line": n.end_line, "old_sig": o.signature, "new_sig": n.signature, "exported": n.exported,
                        "lines_changed": touched})
        elif touched:
            out.append({"change": "modified", "kind": n.kind, "name": n.name, "qualname": n.qualname, "line": n.line,
                        "end_line": n.end_line, "new_sig": n.signature, "exported": n.exported, "lines_changed": touched})
    removed = [olds[i] for k, i in ok.items() if k not in nk]
    added = [news[i] for k, i in nk.items() if k not in ok]
    # Renames within the file: same kind and same body once the name is masked.
    for r in list(removed):
        rb = _norm_body(old_lines, r, r.name)
        for a in added:
            if a.kind == r.kind and len(rb) > 20 and _norm_body(new_lines, a, a.name) == rb:
                out.append({"change": "renamed", "kind": a.kind, "name": a.name, "qualname": a.qualname, "line": a.line,
                            "end_line": a.end_line, "old_name": r.qualname, "new_sig": a.signature, "exported": a.exported,
                            "lines_changed": 0})
                removed.remove(r)
                added.remove(a)
                break
    for a in added:
        out.append({"change": "added", "kind": a.kind, "name": a.name, "qualname": a.qualname, "line": a.line,
                    "end_line": a.end_line, "new_sig": a.signature, "exported": a.exported,
                    "lines_changed": a.end_line - a.line + 1, "_body": _norm_body(new_lines, a, a.name)})
    for r in removed:
        out.append({"change": "removed", "kind": r.kind, "name": r.name, "qualname": r.qualname, "old_line": r.line,
                    "old_sig": r.signature, "exported": r.exported, "lines_changed": r.end_line - r.line + 1,
                    "_body": _norm_body(old_lines, r, r.name)})
    # Children of an added/removed container are implied by it.
    def implied(c):
        if c["change"] not in ("added", "removed"):
            return False
        prefix = c["qualname"].rsplit(".", 1)[0] if "." in c["qualname"] else None
        return bool(prefix) and any(o is not c and o["change"] == c["change"] and o["qualname"] == prefix for o in out)
    out = [c for c in out if not implied(c)]
    order = {"signature": 0, "removed": 1, "renamed": 2, "modified": 3, "added": 4}
    return sorted(out, key=lambda c: (order[c["change"]], c.get("line") or c.get("old_line") or 0))


# --------------------------------------------------------------------------- analysis

def analyze(store, base: str | None = None, head: str = WORKTREE) -> dict:
    root = store.root
    base_sha, base_label = resolve_base(root, base)
    if head != WORKTREE:
        h = _git(root, "rev-parse", "--verify", head + "^{commit}", check=False).strip()
        if not h:
            raise ReviewError(f"unknown head ref '{head}'")
    diffs = collect_diff(root, base_sha, head)
    q = Q(store)
    db = store.db
    changed_paths = {d.path for d in diffs} | {d.old_path for d in diffs}
    ranks = sorted(r[0] or 0 for r in db.execute("SELECT rank FROM files WHERE lang IS NOT NULL AND lang!='markdown'"))

    def pct(rank):
        if not ranks:
            return 0.0
        lo, hi = 0, len(ranks)
        while lo < hi:
            mid = (lo + hi) // 2
            if ranks[mid] < rank:
                lo = mid + 1
            else:
                hi = mid
        return lo / len(ranks)

    files, attention, deps = [], [], []
    all_moves = []
    for d in diffs:
        lang = lang_of(d.path)
        row = db.execute("SELECT id, rank, is_test, tokens FROM files WHERE path=?", (d.path,)).fetchone()
        info = {"path": d.path, "old_path": d.old_path if d.old_path != d.path else None, "status": d.status,
                "lang": lang, "added": d.added, "deleted": d.deleted, "binary": d.binary,
                "is_test": is_test_path(d.path),
                "generated": bool(GENERATED.search(d.path)) or bool(row and db.execute(
                    "SELECT generated FROM files WHERE id=?", (row["id"],)).fetchone()[0]),
                "rank_pct": round(pct(row["rank"]), 2) if row else None, "symbols": [], "dependents": [],
                "tests": [], "tokens": row["tokens"] if row else None,
                "hunks": [{"old_start": h.old_start, "old_len": h.old_len, "new_start": h.new_start, "new_len": h.new_len,
                           "header": h.header, "lines": [[t, s] for t, s in h.lines]} for h in d.hunks]}
        trimmed, n = [], 0
        for h in info["hunks"]:
            if n >= MAX_HUNK_LINES_PER_FILE:
                info["hunks_truncated"] = True
                break
            trimmed.append(h)
            n += len(h["lines"])
        info["hunks"] = trimmed
        if lang and not d.binary and not info["generated"]:
            old_text = file_text(root, base_sha, d.old_path) if d.status != "A" else ""
            new_text = file_text(root, head, d.path) if d.status != "D" else ""
            info["symbols"] = symbol_changes(d.path, lang, old_text, new_text, d)
        if is_manifest(d.path) or (d.old_path and is_manifest(d.old_path)):
            old = {(e, n): v for e, n, v, _ in parse_manifest_text(d.old_path, file_text(root, base_sha, d.old_path))} \
                if d.status != "A" else {}
            new = {(e, n): v for e, n, v, _ in parse_manifest_text(d.path, file_text(root, head, d.path))} \
                if d.status != "D" else {}
            for k in sorted(set(old) | set(new)):
                if k not in old:
                    deps.append({"manifest": d.path, "change": "added", "ecosystem": k[0], "name": k[1], "new": new[k]})
                elif k not in new:
                    deps.append({"manifest": d.path, "change": "removed", "ecosystem": k[0], "name": k[1], "old": old[k]})
                elif old[k] != new[k]:
                    deps.append({"manifest": d.path, "change": "changed", "ecosystem": k[0], "name": k[1], "old": old[k], "new": new[k]})
        if row and not info["is_test"] and lang and lang != "markdown":
            dependents = q._dependents(row["id"])
            paths = {r[0]: (r[1], r[2]) for r in db.execute(
                f"SELECT id, path, is_test FROM files WHERE id IN ({','.join(map(str, dependents)) or '0'})")}
            info["dependents"] = sorted(p for p, t in paths.values() if not t and p not in changed_paths)
            tests = sorted(p for p, t in paths.values() if t)
            stem = posixpath.basename(d.path).rsplit(".", 1)[0].lower()
            if len(stem) > 2:
                tests += [p for (p,) in db.execute("SELECT path FROM files WHERE is_test=1 AND lang IS NOT NULL")
                          if stem in posixpath.basename(p).lower() and p not in tests]
            info["tests"] = sorted(set(tests))
        all_moves.extend((info, c) for c in info["symbols"] if c["change"] in ("added", "removed"))
        files.append(info)

    # Moves across files: removed in one, added in another with the same body.
    removed = [(f, c) for f, c in all_moves if c["change"] == "removed"]
    for f_add, c_add in [(f, c) for f, c in all_moves if c["change"] == "added"]:
        for f_rem, c_rem in removed:
            if f_rem is not f_add and c_rem["kind"] == c_add["kind"] and len(c_add["_body"]) > 20 and c_rem["_body"] == c_add["_body"]:
                c_add.update(change="moved", old_name=f"{f_rem['path']}:{c_rem['qualname']}")
                f_rem["symbols"].remove(c_rem)
                removed.remove((f_rem, c_rem))
                break
    for f in files:
        for c in f["symbols"]:
            c.pop("_body", None)

    # Callers outside the diff that a signature change or removal may break.
    for f in files:
        if f["is_test"] or f["generated"]:
            continue
        for c in f["symbols"]:
            if c["change"] not in ("signature", "removed", "renamed", "moved") or c["kind"].startswith("h"):
                continue
            name = c["name"] if c["change"] in ("signature",) else (c.get("old_name") or c["qualname"]).split(":")[-1].split(".")[-1]
            if len(name) < 3:
                continue
            callers = _outside_callers(store, f, name, changed_paths)
            if callers:
                c["callers_outside"] = callers[:12]
                what = {"signature": "signature changed", "removed": "removed", "renamed": f"renamed to {c['name']}",
                        "moved": "moved"}[c["change"]]
                attention.append({"severity": "high" if c["change"] in ("removed", "renamed") or c.get("exported") else "medium",
                                  "path": f["path"], "symbol": c["qualname"] if c["change"] != "renamed" else c.get("old_name"),
                                  "message": f"`{name}` {what} but {len(callers)} file(s) outside this change still use it",
                                  "where": callers[:6]})

    # Tests.
    changed_tests = sorted(f["path"] for f in files if f["is_test"])
    code_files = [f for f in files if not f["is_test"] and f["lang"] and f["lang"] != "markdown" and not f["generated"]]
    untested, affected = [], set()
    for f in code_files:
        affected.update(t for t in f["tests"] if t not in changed_tests)
        has_logic = any(c["change"] != "removed" for c in f["symbols"]) or f["status"] == "A"
        stem = posixpath.basename(f["path"]).rsplit(".", 1)[0].lower()
        covered = any(t in changed_tests for t in f["tests"]) or any(stem in posixpath.basename(t).lower() for t in changed_tests)
        f["tests_changed"] = covered
        if has_logic and f["status"] != "D" and not f["tests"] and not covered:
            untested.append(f["path"])
    if untested:
        attention.append({"severity": "medium", "path": None, "symbol": None,
                          "message": f"{len(untested)} changed code file(s) have no tests referencing them and no test changes",
                          "where": untested[:8]})
    if deps:
        added = [d["name"] for d in deps if d["change"] == "added"]
        if added:
            attention.append({"severity": "medium", "path": None, "symbol": None,
                              "message": f"new dependencies: {', '.join(added[:8])}", "where": []})

    for f in files:
        f["risk"], f["level"], f["reasons"] = _risk(f, untested)
    files.sort(key=lambda f: (-f["risk"], f["path"]))
    attention.sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}[a["severity"]])

    sym_counts = {}
    for f in files:
        for c in f["symbols"]:
            sym_counts[c["change"]] = sym_counts.get(c["change"], 0) + 1
    overall = max((f["risk"] for f in files), default=0)
    return {
        "base": base_sha[:10], "base_label": base_label[:10] if re.fullmatch(r"[0-9a-f]{40}", base_label) else base_label, "head": head if head == WORKTREE else head,
        "head_sha": _git(root, "rev-parse", "--short", "HEAD", check=False).strip(),
        "repo": root.name,
        "summary": {"files": len(files), "added_lines": sum(f["added"] for f in files),
                    "deleted_lines": sum(f["deleted"] for f in files), "symbols": sym_counts,
                    "risk": overall, "level": _level(overall),
                    "high": sum(1 for f in files if f["level"] == "high"),
                    "tests_changed": len(changed_tests)},
        "files": files, "attention": attention, "deps": deps,
        "tests": {"changed": changed_tests, "affected_unchanged": sorted(affected)[:40], "untested": untested},
        "graph": _graph(store, files, changed_paths),
    }


def _outside_callers(store, f, name, changed_paths) -> list:
    db = store.db
    row = db.execute("SELECT id, lang FROM files WHERE path=?", (f["path"],)).fetchone()
    importers = set()
    if row:
        importers = {r[0] for r in db.execute("SELECT DISTINCT file_id FROM imports WHERE target_id=?", (row[0],))}
    d = posixpath.dirname(f["path"])
    out = []
    for fid, path, lines, lang, is_test in db.execute(
            "SELECT i.file_id, fl.path, i.lines, fl.lang, fl.is_test FROM idents i JOIN files fl ON fl.id=i.file_id "
            "WHERE i.name=?", (name,)):
        if path in changed_paths:
            continue
        linked = fid in importers or (lang in PACKAGE_SCOPED and posixpath.dirname(path) == d)
        if linked:
            first = (lines or "").split(",")[0]
            out.append(f"{path}:{first}" if first else path)
    return sorted(out)


def _level(score: int) -> str:
    return "high" if score >= 55 else "medium" if score >= 30 else "low"


def _risk(f, untested) -> tuple:
    reasons = []
    if f["generated"]:
        return 3, "low", ["generated / lock file: skim"]
    score = {"A": 10, "D": 10, "M": 12, "R": 5}.get(f["status"], 10)
    churn = f["added"] + f["deleted"]
    if churn:
        c = min(25, int(6 * math.log2(1 + churn)))
        score += c
        if churn >= 100:
            reasons.append(f"large change ({churn} lines)")
    if f["rank_pct"] is not None and f["rank_pct"] >= 0.8:
        score += int(20 * f["rank_pct"])
        reasons.append(f"central file (top {max(1, int(100 * (1 - f['rank_pct'])))}% by dependency rank)")
    n_dep = len(f["dependents"])
    if n_dep:
        score += min(15, int(3 * math.sqrt(n_dep)))
        if n_dep >= 5:
            reasons.append(f"{n_dep} dependent files outside the change")
    api = [c for c in f["symbols"] if c["change"] in ("signature", "removed", "renamed") and c.get("exported")]
    if api:
        score += 10
        reasons.append("public API changed: " + ", ".join(c["qualname"] for c in api[:3]))
    broken = [c for c in f["symbols"] if c.get("callers_outside")]
    if broken:
        score += min(15, 5 * len(broken))
        reasons.append(f"{len(broken)} change(s) with callers outside the diff")
    if f["path"] in untested:
        score += 10
        reasons.append("no tests reference it")
    elif f.get("tests_changed"):
        score -= 5
    if SENSITIVE.search(f["path"]):
        score += 12
        reasons.append("sensitive area (auth, data, infra or CI)")
    if f["is_test"]:
        score = min(score, 25)
    if f["lang"] == "markdown" or f["lang"] is None and not SENSITIVE.search(f["path"]):
        score = min(score, 15)
    score = max(0, min(100, score))
    return score, _level(score), reasons


def _graph(store, files, changed_paths) -> dict:
    """Nodes: changed files (by risk) + most important impacted files; edges from the index."""
    db = store.db
    nodes = []
    for f in [f for f in sorted(files, key=lambda f: -f["risk"]) if not f["generated"] and not f["is_test"]
              and f["lang"] != "markdown"][:30]:
        nodes.append({"id": f["path"], "status": f["status"], "risk": f["risk"], "level": f["level"],
                      "added": f["added"], "deleted": f["deleted"], "impacted": False})
    ids = {n["id"] for n in nodes}
    impacted = {}
    for f in files:
        for p in f["dependents"][:8]:
            if p not in ids:
                impacted[p] = impacted.get(p, 0) + 1
    for p, _ in sorted(impacted.items(), key=lambda t: -t[1])[:12]:
        nodes.append({"id": p, "status": "impacted", "risk": 0, "level": "none", "added": 0, "deleted": 0, "impacted": True})
        ids.add(p)
    id_rows = {r[1]: r[0] for r in db.execute(
        f"SELECT id, path FROM files WHERE path IN ({','.join('?' * len(ids))})", tuple(ids))} if ids else {}
    rev = {v: k for k, v in id_rows.items()}
    edges = []
    if id_rows:
        idl = ",".join(map(str, id_rows.values()))
        seen = set()
        for s, d in db.execute(f"SELECT src, dst FROM edges WHERE src IN ({idl}) AND dst IN ({idl}) AND weight >= 0.5 "
                               f"UNION SELECT file_id, target_id FROM imports WHERE file_id IN ({idl}) AND target_id IN ({idl})"):
            if s != d and (s, d) not in seen:
                seen.add((s, d))
                edges.append({"from": rev[s], "to": rev[d]})
    return {"nodes": nodes, "edges": edges[:80]}


def estimate_baseline_tokens(root, analysis: dict) -> int:
    """What a reviewer would otherwise read: the full patch plus every changed file."""
    patch = sum(len(l[1]) + 2 for f in analysis["files"] for h in f["hunks"] for l in h["lines"])
    files = sum(f["tokens"] or 0 for f in analysis["files"] if not f["generated"])
    return est_tokens(patch) + files
