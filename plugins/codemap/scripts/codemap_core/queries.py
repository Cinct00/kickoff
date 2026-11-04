"""Query commands. Each returns (text, avoided_tokens) — compact, line-oriented output."""
from __future__ import annotations

import fnmatch
import math
import posixpath
import re
import sqlite3
import time
from collections import Counter, defaultdict

from .graph import pagerank, strongly_connected
from .manifests import PY_IMPORT_ALIASES, norm_pkg
from .util import est_tokens, fmt_tokens

PACKAGE_SCOPED = {"go", "java", "kotlin", "scala", "csharp", "swift"}
MAP_KINDS_EXCLUDE = ("var", "field", "h3", "h4", "h5", "h6")
MAP_CANDIDATE_FILES = 300
FOCUS_MAX_NODES = 3000
ENTRY_RE = re.compile(r"(^|/)(main|__main__|cli|app|server|index|manage|program|wsgi|asgi)\.(py|js|ts|go|rs|cs|java|kt|rb|php)$", re.I)


class QueryError(Exception):
    pass


class Q:
    def __init__(self, store):
        self.s = store
        self.db = store.db

    # ------------------------------------------------------------------ helpers
    def _file(self, arg: str):
        arg = arg.strip().lstrip("./").replace("\\", "/")
        row = self.db.execute("SELECT * FROM files WHERE path=?", (arg,)).fetchone()
        if row:
            return row
        rows = self.db.execute("SELECT * FROM files WHERE path LIKE ? ORDER BY length(path) LIMIT 6", ("%/" + arg,)).fetchall()
        if len(rows) == 1:
            return rows[0]
        if not rows:
            rows = self.db.execute("SELECT * FROM files WHERE path LIKE ? ORDER BY rank DESC LIMIT 6", (f"%{arg}%",)).fetchall()
            if len(rows) == 1:
                return rows[0]
        if rows:
            raise QueryError(f"ambiguous path '{arg}': " + ", ".join(r["path"] for r in rows))
        raise QueryError(f"no indexed file matches '{arg}'")

    def _path(self, fid: int) -> str:
        r = self.db.execute("SELECT path FROM files WHERE id=?", (fid,)).fetchone()
        return r[0] if r else "?"

    def _symbols(self, target: str, limit: int = 20):
        """Resolve 'Name', 'Class.method', 'path:Name' or 'path::Name' to symbol rows (best first)."""
        target = target.strip()
        path = None
        m = re.match(r"^(.+?\.\w+)::?(.+)$", target)
        if m and "/" in m.group(1) or (m and "." in m.group(1) and not m.group(2).isdigit()):
            try:
                path = self._file(m.group(1))
                target = m.group(2)
            except QueryError:
                path = None
        where, args = [], []
        if "." in target or "::" in target:
            q = target.replace("::", ".")
            where.append("(s.qualname = ? OR s.qualname LIKE ?)")
            args += [q, "%." + q]
        else:
            where.append("s.name = ?")
            args.append(target)
        if path is not None:
            where.append("s.file_id = ?")
            args.append(path["id"])
        rows = self.db.execute(
            f"SELECT s.*, f.path, f.tokens AS ftokens FROM symbols s JOIN files f ON f.id = s.file_id "
            f"WHERE {' AND '.join(where)} ORDER BY (s.kind LIKE 'h_'), s.rank DESC LIMIT ?", (*args, limit)).fetchall()
        if not rows and "." not in target:
            rows = self.db.execute(
                "SELECT s.*, f.path, f.tokens AS ftokens FROM symbols s JOIN files f ON f.id = s.file_id "
                "WHERE s.name = ? COLLATE NOCASE ORDER BY s.rank DESC LIMIT ?", (target, limit)).fetchall()
        return rows

    def _enclosing(self, fid: int, line: int):
        """Innermost function/class containing a line (None at module level)."""
        return self.db.execute(
            "SELECT name, qualname, kind, line FROM symbols WHERE file_id=? AND line<=? AND end_line>=? "
            "AND kind NOT LIKE 'h_' AND kind NOT IN ('var','field','const') ORDER BY (end_line - line) LIMIT 1",
            (fid, line, line)).fetchone()

    @staticmethod
    def _more(total: int, shown: int, hint: str = "--limit") -> str:
        return f"(+{total - shown} more; {hint})" if total > shown else ""

    def _depth(self, sym_row, cache: dict) -> int:
        d, p = 0, sym_row["parent_id"]
        while p is not None and d < 6:
            if p not in cache:
                r = self.db.execute("SELECT parent_id FROM symbols WHERE id=?", (p,)).fetchone()
                cache[p] = r[0] if r else None
            p = cache[p]
            d += 1
        return d

    def _defs_ndefs(self, names):
        out = {}
        names = list(names)
        for i in range(0, len(names), 500):
            chunk = names[i:i + 500]
            for n, c in self.db.execute(
                    f"SELECT name, COUNT(DISTINCT file_id) FROM symbols WHERE name IN ({','.join('?' * len(chunk))}) "
                    "AND kind NOT LIKE 'h_' GROUP BY name", chunk):
                out[n] = c
        return out

    # ------------------------------------------------------------------ overview / status
    def overview(self, **_):
        db = self.db
        root = posixpath.basename(self.s.meta("root", "repo").rstrip("/"))
        head = self.s.meta("git_head", "")
        age = time.time() - float(self.s.meta("last_refresh", time.time()))
        langs = db.execute("SELECT lang, COUNT(*), SUM(tokens) FROM files WHERE lang IS NOT NULL GROUP BY lang ORDER BY 2 DESC").fetchall()
        n_code = sum(r[1] for r in langs if r[0] != "markdown")
        tok_code = sum(r[2] or 0 for r in langs if r[0] != "markdown")
        n_other = db.execute("SELECT COUNT(*) FROM files WHERE lang IS NULL").fetchone()[0]
        n_sym = db.execute("SELECT COUNT(*) FROM symbols WHERE kind NOT LIKE 'h_'").fetchone()[0]
        n_int = db.execute("SELECT COUNT(DISTINCT file_id || '>' || target_id) FROM imports WHERE target_id IS NOT NULL").fetchone()[0]
        n_tests = db.execute("SELECT COUNT(*) FROM files WHERE is_test=1 AND lang IS NOT NULL AND lang!='markdown'").fetchone()[0]
        code_langs = [(l, c) for l, c, _ in langs if l != "markdown"]
        n_md = sum(c for l, c, _ in langs if l == "markdown")
        lines = [f"{root}{' @' + head if head else ''} · indexed {int(age)}s ago",
                 f"code: {n_code} files ({', '.join(f'{l} {c}' for l, c in code_langs[:7]) or '-'}) ~{fmt_tokens(tok_code)} tokens; "
                 f"{n_tests} test files; {n_md} markdown; {n_other} other files",
                 f"symbols {n_sym} · internal import links {n_int}"]
        dirs = Counter()
        for (p,) in db.execute("SELECT path FROM files WHERE lang IS NOT NULL AND lang != 'markdown'"):
            dirs[p.split("/")[0] + "/" if "/" in p else "./"] += 1
        if dirs:
            lines.append("dirs: " + " · ".join(f"{d} {c}" for d, c in dirs.most_common(8)))
        entries = [p for (p,) in db.execute("SELECT path FROM files WHERE lang IS NOT NULL AND lang != 'markdown' ORDER BY length(path)")
                   if ENTRY_RE.search(p) and p.count("/") <= 3][:6]
        if entries:
            lines.append("entry points: " + ", ".join(entries))
        central = db.execute("SELECT path FROM files WHERE lang IS NOT NULL AND lang != 'markdown' AND is_test=0 "
                             "AND generated=0 ORDER BY rank DESC LIMIT 10").fetchall()
        if central:
            lines.append("central files: " + ", ".join(r[0] for r in central))
        ext = db.execute("SELECT external, COUNT(DISTINCT file_id) c FROM imports WHERE external IS NOT NULL "
                         "AND external NOT LIKE 'stdlib:%' AND external NOT LIKE 'node:%' GROUP BY external ORDER BY c DESC LIMIT 10").fetchall()
        if ext:
            lines.append("most-imported packages: " + ", ".join(f"{e} {c}" for e, c in ext))
        n_deps = db.execute("SELECT COUNT(DISTINCT name) FROM deps").fetchone()[0]
        if n_deps:
            lines.append(f"declared dependencies: {n_deps} (codemap packages)")
        lines.append("next: map [--focus <path|symbol>] · find <terms> · outline <path> · show <symbol> · refs <name> · impact <path>")
        text = "\n".join(lines)
        avoided = sum(r[0] or 0 for r in db.execute("SELECT tokens FROM files WHERE lang IS NOT NULL ORDER BY rank DESC LIMIT 5"))
        return text, avoided

    def status(self, **_):
        db = self.db
        last = float(self.s.meta("last_refresh", 0))
        rows = [
            f"repo: {self.s.meta('root')}",
            f"db: {self.s.db_path} ({self.s.db_path.stat().st_size // 1024} KB)" if self.s.db_path.exists() else f"db: {self.s.db_path}",
            f"files: {db.execute('SELECT COUNT(*) FROM files').fetchone()[0]} · symbols: {db.execute('SELECT COUNT(*) FROM symbols').fetchone()[0]}"
            f" · imports: {db.execute('SELECT COUNT(*) FROM imports').fetchone()[0]} · deps: {db.execute('SELECT COUNT(*) FROM deps').fetchone()[0]}",
            f"refreshed: {int(time.time() - last)}s ago · git {self.s.meta('git_head', '?')} · ranks {'stale' if self.s.meta('ranks_stale') == '1' else 'current'}",
        ]
        s = self._savings_totals()
        if s[0]:
            rows.append(f"usage: {s[0]} queries, {fmt_tokens(s[1])} tokens returned, ~{fmt_tokens(s[2])} tokens avoided")
        return "\n".join(rows), 0

    def _savings_totals(self):
        r = self.db.execute("SELECT COUNT(*), COALESCE(SUM(out_tokens),0), COALESCE(SUM(avoided_tokens),0) FROM usage").fetchone()
        return r[0], r[1], r[2]

    def savings(self, **_):
        n, out, avoided = self._savings_totals()
        if not n:
            return "no queries logged yet", 0
        lines = [f"{n} queries · returned {fmt_tokens(out)} tokens · avoided ~{fmt_tokens(avoided)} tokens "
                 f"(≈{(avoided / max(out, 1)):.0f}× less than opening the files)",
                 "avoided = tokens of the files a query stood in for (outline/show: that file; find/refs/map: files listed)."]
        for cmd, c, o, a in self.db.execute("SELECT cmd, COUNT(*), SUM(out_tokens), SUM(avoided_tokens) FROM usage GROUP BY cmd ORDER BY 4 DESC"):
            lines.append(f"  {cmd:9} {c:5}×  out {fmt_tokens(o):>6}  avoided {fmt_tokens(a):>7}")
        return "\n".join(lines), 0

    # ------------------------------------------------------------------ map
    def map(self, budget: int = 1024, focus=(), include_focus: bool = False, **_):
        db = self.db
        focus_files, focus_names = set(), set()
        for f in focus or ():
            try:
                focus_files.add(self._file(f)["id"])
            except QueryError:
                syms = self._symbols(f, 5)
                for s in syms:
                    focus_files.add(s["file_id"])
                    focus_names.add(s["name"])
        file_rank = {r[0]: r[1] for r in db.execute("SELECT id, rank FROM files WHERE lang IS NOT NULL")}
        if focus_files:
            # Personalised PageRank on the focus neighbourhood only (2 hops, strongest edges first): on a
            # 35k-file repo the whole graph takes seconds, the neighbourhood milliseconds.
            edges = defaultdict(dict)
            nodes, frontier = set(focus_files), set(focus_files)
            for _hop in range(2):
                if not frontier or len(nodes) >= FOCUS_MAX_NODES:
                    break
                ids = ",".join(map(str, frontier))
                found = db.execute(f"SELECT src, dst, weight FROM edges WHERE src IN ({ids}) "
                                   f"UNION ALL SELECT src, dst, weight FROM edges WHERE dst IN ({ids}) "
                                   f"ORDER BY weight DESC LIMIT {FOCUS_MAX_NODES * 4}").fetchall()
                nxt = set()
                for s, d, w in found:
                    edges[s][d] = w
                    edges[d].setdefault(s, w * 0.5)  # let focus flow to both dependencies and dependents
                    for n in (s, d):
                        if n not in nodes and len(nodes) + len(nxt) < FOCUS_MAX_NODES:
                            nxt.add(n)
                nodes |= nxt
                frontier = nxt
            sub = {s: {d: w for d, w in ds.items() if d in nodes} for s, ds in edges.items() if s in nodes}
            pers = {f: 1.0 for f in focus_files}
            local = pagerank(sorted(nodes), sub, pers)
            file_rank = {f: local.get(f, 0.0) for f in nodes}
        kinds = ",".join(f"'{k}'" for k in MAP_KINDS_EXCLUDE)
        # Only the highest-ranked files can make it into a token-budgeted map; don't score the whole repo.
        hidden = {r[0] for r in db.execute("SELECT id FROM files WHERE generated=1 OR is_test=1")}
        top_files = [f for f in sorted(file_rank, key=lambda f: -file_rank[f]) if f not in hidden][:MAP_CANDIDATE_FILES]
        cand = ",".join(str(f) for f in set(top_files) | focus_files) or "0"
        rows = db.execute(
            f"SELECT s.id, s.file_id, s.name, s.kind, s.line, s.signature, s.parent_id, s.rank, f.path, f.tokens, "
            f"p.kind AS pkind, p.line AS pline, p.signature AS psig "
            f"FROM symbols s JOIN files f ON f.id=s.file_id LEFT JOIN symbols p ON p.id=s.parent_id "
            f"WHERE s.file_id IN ({cand}) AND s.kind NOT IN ({kinds}) AND f.is_test=0 "
            f"AND (p.kind IS NULL OR p.kind NOT IN ('function','method'))").fetchall()
        max_by_file = defaultdict(float)
        for r in rows:
            max_by_file[r["file_id"]] = max(max_by_file[r["file_id"]], r["rank"] or 0)
        scored = []
        for r in rows:
            if not include_focus and r["file_id"] in focus_files and not focus_names:
                continue
            rel = (r["rank"] or 0) / (max_by_file[r["file_id"]] or 1)
            score = file_rank.get(r["file_id"], 0) * (0.15 + rel)
            if r["name"] in focus_names:
                score *= 10
            if r["kind"].startswith("h"):
                score *= 0.3
            elif r["kind"] in ("const", "macro"):
                score *= 0.3
            scored.append((score, r))
        scored.sort(key=lambda t: -t[0])
        cache: dict = {}

        def render(k):
            chosen = [r for _, r in scored[:k]]
            by_file = defaultdict(list)
            order = []
            for r in chosen:
                if r["file_id"] not in by_file:
                    order.append(r["file_id"])
                by_file[r["file_id"]].append(r)
            out = []
            for fid in order:
                syms = sorted(by_file[fid], key=lambda r: r["line"])
                out.append(syms[0]["path"] + ":")
                chosen_ids = {r["id"] for r in syms}
                shown_parents = set()
                for r in syms:
                    depth = 1 + min(self._depth(r, cache), 3)
                    # Keep the enclosing class line so a method never appears without its type.
                    if r["parent_id"] and r["parent_id"] not in chosen_ids and r["parent_id"] not in shown_parents and r["psig"] \
                            and r["pkind"] != "namespace":
                        shown_parents.add(r["parent_id"])
                        out.append("  " * (depth - 1) + f"{r['pline']}: {r['psig']}")
                    sig = r["signature"]
                    if r["kind"] in ("const", "var") and " = " in sig:
                        sig = sig.split(" = ", 1)[0] + " = …"
                    out.append("  " * depth + f"{r['line']}: {sig}")
            return "\n".join(out), {fid for fid in order}

        lo, hi, best = 1, len(scored), ("", set())
        while lo <= hi:
            mid = (lo + hi) // 2
            text, files = render(mid)
            if est_tokens(text) <= budget:
                best = (text, files)
                lo = mid + 1
            else:
                hi = mid - 1
        text, files = best
        if not text:
            return "(map is empty: nothing indexed with symbols)", 0
        avoided = sum(r[0] or 0 for r in db.execute(
            f"SELECT tokens FROM files WHERE id IN ({','.join(map(str, files))})")) if files else 0
        return text, avoided

    # ------------------------------------------------------------------ tree / files
    def tree(self, path: str = "", depth: int = 2, **_):
        prefix = path.strip("/").replace("\\", "/")
        rows = self.db.execute("SELECT path, lang, tokens FROM files WHERE path LIKE ?", (prefix + "%" if prefix else "%",)).fetchall()
        if prefix:
            rows = [r for r in rows if r[0] == prefix or r[0].startswith(prefix + "/")]
        if not rows:
            raise QueryError(f"nothing indexed under '{prefix}'")
        base_depth = prefix.count("/") + 1 if prefix else 0
        agg = defaultdict(lambda: [0, Counter(), 0])
        direct = []
        for p, lang, tok in rows:
            parts = p.split("/")
            if len(parts) - 1 == base_depth:
                direct.append((p, lang, tok))
            for d in range(base_depth + 1, min(len(parts), base_depth + depth + 1)):
                key = "/".join(parts[:d])
                a = agg[key]
                a[0] += 1
                a[2] += tok or 0
                if lang:
                    a[1][lang] += 1
        out = []
        for key in sorted(agg):
            a = agg[key]
            lvl = key.count("/") - base_depth
            langs = ", ".join(f"{l} {c}" for l, c in a[1].most_common(3))
            out.append("  " * lvl + f"{key.split('/')[-1]}/ {a[0]} files" + (f" ({langs})" if langs else "") + f" ~{fmt_tokens(a[2])}t")
        if len(direct) <= 40:
            for p, lang, tok in sorted(direct):
                out.append(f"{posixpath.basename(p)}  {lang or '-'} ~{fmt_tokens(tok or 0)}t")
        else:
            out.append(f"({len(direct)} files directly here; use: files {prefix + '/' if prefix else ''}*)")
        return "\n".join(out), 0

    def files(self, pattern: str, limit: int = 50, **_):
        pat = pattern.replace("\\", "/")
        if not any(ch in pat for ch in "*?["):
            pat = f"*{pat}*"
        rows = [r for r in self.db.execute("SELECT path, lang, lines, tokens, rank FROM files ORDER BY path")
                if fnmatch.fnmatch(r[0], pat) or fnmatch.fnmatch(r[0].lower(), pat.lower())]
        out = [f"{r[0]}  {r[1] or '-'} {r[2] or '?'}L ~{fmt_tokens(r[3] or 0)}t" for r in rows[:limit]]
        more = self._more(len(rows), limit)
        return ("\n".join(out) + ("\n" + more if more else "")) if out else "no files match", 0

    # ------------------------------------------------------------------ search
    def find(self, query: str, kind: str | None = None, limit: int = 20, path: str | None = None, **_):
        terms = [t for t in re.split(r"[\s,]+", query) if t]
        if not terms:
            raise QueryError("empty query")
        clauses = []
        for t in terms:
            words = [w for w in re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", t).replace("_", " ").replace(".", " ").lower().split() if w]
            word_q = " AND ".join(f'words:"{w}"*' for w in words) if words else ""
            esc = t.replace('"', '""')
            clauses.append(f'(name:"{esc}"* OR qualname:"{esc}"*' + (f" OR ({word_q})" if word_q else "") + ")")
        match = " AND ".join(clauses)
        match_any = " OR ".join(clauses)
        sql = ("SELECT s.id, s.name, s.qualname, s.kind, s.line, s.end_line, s.signature, s.rank, f.path, f.tokens, "
               "bm25(symbols_fts, 10.0, 6.0, 4.0, 1.0, 0.5) AS score "
               "FROM symbols_fts JOIN symbols s ON s.id = symbols_fts.rowid JOIN files f ON f.id = s.file_id "
               "WHERE symbols_fts MATCH ?")
        args = [match]
        if kind:
            sql += " AND s.kind = ?"
            args.append(kind)
        if path:
            sql += " AND f.path LIKE ?"
            args.append(f"%{path}%")
        sql += " ORDER BY score LIMIT 300"
        try:
            rows = self.db.execute(sql, args).fetchall()
            if not rows and len(clauses) > 1:  # no symbol matches every term: rank by any term instead
                rows = self.db.execute(sql, [match_any] + args[1:]).fetchall()
        except sqlite3.OperationalError:
            rows = []
        if not rows:
            rows = self.db.execute(
                "SELECT s.id, s.name, s.qualname, s.kind, s.line, s.end_line, s.signature, s.rank, f.path, f.tokens, 0 AS score "
                "FROM symbols s JOIN files f ON f.id=s.file_id WHERE s.name LIKE ? OR s.signature LIKE ? LIMIT 300",
                (f"%{query}%", f"%{query}%")).fetchall()
        exact = {t.lower() for t in terms}
        joined = "".join(terms).lower().replace("_", "")
        type_kinds = ("class", "interface", "struct", "trait", "enum", "record", "type", "protocol", "object")

        def relevance(r):
            rel = (-r["score"] if r["score"] else 0.5) + 0.1
            nm = r["name"].lower()
            if nm.replace("_", "") == joined:
                rel *= 6
            elif nm in exact:
                rel *= 3
            if r["kind"] in type_kinds:
                rel *= 1.5
            if r["kind"].startswith("h"):
                rel *= 0.3
            if "/test" in r["path"].lower() or "test" in r["path"].rsplit("/", 1)[-1].lower():
                rel *= 0.5
            return rel * (1 + min((r["rank"] or 0) * 200, 2))
        rows = sorted(rows, key=relevance, reverse=True)
        shown = rows[:limit]
        by_file, order = defaultdict(list), []
        for r in shown:
            if r["path"] not in by_file:
                order.append(r["path"])
            by_file[r["path"]].append(r)
        out = []
        for p in order:
            out.append(p)
            for r in sorted(by_file[p], key=lambda r: r["line"]):
                span = f"{r['line']}-{r['end_line']}" if r["end_line"] and r["end_line"] > r["line"] else str(r["line"])
                out.append(f"  {span} {r['signature']}")
        if not out:
            return f"no symbols match '{query}' (try: files {query} · or grep for strings/comments)", 0
        more = self._more(len(rows), len(shown))
        if more:
            out.append(more)
        avoided = sum({r["path"]: r["tokens"] or 0 for r in shown}.values())
        return "\n".join(out), avoided

    def define(self, name: str, limit: int = 10, **_):
        rows = self._symbols(name, limit + 1)
        if not rows:
            raise QueryError(f"no definition of '{name}' (try: find {name})")
        type_kinds = ("class", "interface", "struct", "trait", "enum", "record", "type", "protocol", "object")
        rows = sorted(rows, key=lambda r: (r["kind"] not in type_kinds, -(r["rank"] or 0)))
        out = []
        for r in rows[:limit]:
            doc = f"  — {r['doc']}" if r["doc"] else ""
            out.append(f"{r['path']}:{r['line']}-{r['end_line']} {r['kind']} {r['qualname']}\n  {r['signature']}{doc}")
            bases = [b[0] for b in self.db.execute("SELECT base FROM bases WHERE symbol_id=?", (r["id"],))]
            if bases:
                out.append("  extends: " + ", ".join(bases))
            if r["kind"] in type_kinds:
                n_sub = self.db.execute("SELECT COUNT(*) FROM bases WHERE base=?", (r["name"],)).fetchone()[0]
                if n_sub:
                    subs = [s[0] for s in self.db.execute(
                        "SELECT s.name FROM bases b JOIN symbols s ON s.id=b.symbol_id WHERE b.base=? LIMIT 6", (r["name"],))]
                    out.append(f"  subtypes ({n_sub}): " + ", ".join(subs) + (f" … (hierarchy {r['name']})" if n_sub > 6 else ""))
        more = self._more(len(rows), limit)
        if more:
            out.append(more)
        return "\n".join(out), sum({r["path"]: r["ftokens"] or 0 for r in rows[:limit]}.values())

    # ------------------------------------------------------------------ reading
    def outline(self, path: str, doc: bool = True, **_):
        f = self._file(path)
        syms = self.db.execute("SELECT * FROM symbols WHERE file_id=? ORDER BY line", (f["id"],)).fetchall()
        head = f"{f['path']}  {f['lang'] or '-'} {f['lines'] or '?'}L ~{fmt_tokens(f['tokens'] or 0)}t" + ("  [test]" if f["is_test"] else "")
        out = [head]
        internal = []
        for raw, n, tid in self.db.execute(
                "SELECT raw, COUNT(DISTINCT target_id), MIN(target_id) FROM imports WHERE file_id=? AND target_id IS NOT NULL "
                "GROUP BY raw ORDER BY MIN(line) LIMIT 15", (f["id"],)):
            internal.append(raw if n > 1 else self._path(tid))  # namespace/package imports: show the namespace
        external = [r[0] for r in self.db.execute(
            "SELECT DISTINCT external FROM imports WHERE file_id=? AND external IS NOT NULL LIMIT 12", (f["id"],))]
        if internal:
            out.append("imports: " + ", ".join(internal))
        if external:
            out.append("external: " + ", ".join(e.replace("stdlib:", "") for e in external))
        cache: dict = {}
        for s in syms:
            if s["kind"] == "var" and s["parent_id"] is None and len(syms) > 40:
                continue
            span = f"{s['line']}-{s['end_line']}" if s["end_line"] > s["line"] else str(s["line"])
            d = f"  # {s['doc']}" if doc and s["doc"] else ""
            out.append("  " * (1 + min(self._depth(s, cache), 4)) + f"{span} {s['signature']}{d}")
        if not syms:
            out.append("  (no symbols extracted)")
        text = "\n".join(out)
        return text, max(0, (f["tokens"] or 0) - est_tokens(text))

    def show(self, target: str, context: int = 0, max_lines: int = 250, numbers: bool = False, **_):
        m = re.match(r"^(.+?):(\d+)(?:-(\d+))?$", target.strip())
        if m:
            f = self._file(m.group(1))
            start, end = int(m.group(2)), int(m.group(3) or m.group(2))
            others = []
        else:
            rows = self._symbols(target, 6)
            if not rows:
                raise QueryError(f"no symbol '{target}' (try: find {target})")
            r = rows[0]
            f = self._file(r["path"])
            start, end = r["line"], r["end_line"] or r["line"]
            others = [f"{o['path']}:{o['line']} {o['qualname']}" for o in rows[1:]]
            # Include decorators / doc comment directly above.
        start = max(1, start - context)
        end = end + context
        try:
            lines = (self.s.root / f["path"]).read_text(encoding="utf-8", errors="replace").split("\n")
        except OSError as e:
            raise QueryError(f"cannot read {f['path']}: {e}")
        if not m:
            while start > 1 and re.match(r"^\s*(@|#\[|\[[A-Z])", lines[start - 2]):
                start -= 1
        end = min(end, len(lines))
        truncated = end - start + 1 > max_lines
        if truncated:
            end = start + max_lines - 1
        body = lines[start - 1:end]
        if numbers:
            body = [f"{start + i}|{l}" for i, l in enumerate(body)]
        out = [f"{f['path']}:{start}-{end}"] + body
        if truncated:
            out.append(f"… truncated at {max_lines} lines; use outline {f['path']} then show a member, or show {f['path']}:{end + 1}-…")
        if others:
            out.append("also: " + "; ".join(others))
        text = "\n".join(out)
        return text, max(0, (f["tokens"] or 0) - est_tokens(text))

    # ------------------------------------------------------------------ references
    def _ref_rows(self, name: str):
        defs = self._symbols(name, 50)
        bare = name.replace("::", ".").split(".")[-1]
        def_files = {d["file_id"] for d in defs}
        def_lines = {(d["file_id"], d["line"]) for d in defs}
        importers = set()
        if def_files:
            importers = {r[0] for r in self.db.execute(
                f"SELECT DISTINCT file_id FROM imports WHERE target_id IN ({','.join(map(str, def_files))})")}
        def_dirs = {posixpath.dirname(d["path"]) for d in defs}
        rows = self.db.execute("SELECT i.file_id, i.count, i.lines, f.path, f.lang, f.tokens, f.is_test FROM idents i "
                               "JOIN files f ON f.id=i.file_id WHERE i.name=? ORDER BY i.count DESC", (bare,)).fetchall()
        sure, weak = [], []
        for r in rows:
            lines = [int(x) for x in (r["lines"] or "").split(",") if x]
            lines = [l for l in lines if (r["file_id"], l) not in def_lines]
            if not lines and r["file_id"] in def_files:
                continue
            confident = (not defs or r["file_id"] in def_files or r["file_id"] in importers
                         or (r["lang"] in PACKAGE_SCOPED and posixpath.dirname(r["path"]) in def_dirs))
            (sure if confident else weak).append((r, lines))
        return defs, sure, weak

    def refs(self, name: str, limit: int = 25, **_):
        defs, sure, weak = self._ref_rows(name)
        if not sure and not weak:
            return f"no references to '{name}' found", 0
        loc = ", ".join(f"{d['path']}:{d['line']}" for d in defs[:3]) or "not defined in repo"
        total = sum(r["count"] for r, _ in sure)
        out = [f"{name}  defined: {loc}  ·  {len(sure)} files, {total} uses"]
        for r, lines in sure[:limit]:
            parts = []
            for l in lines[:4]:
                enc = self._enclosing(r["file_id"], l)
                parts.append(f"{l}" + (f" in {enc['qualname']}" if enc and enc["line"] != l else ""))
            out.append(f"  {r['path']} ×{r['count']}: " + ", ".join(parts) + (" …" if len(lines) > 4 else ""))
        more = self._more(len(sure), limit)
        if more:
            out.append("  " + more)
        if weak:
            out.append(f"  name-only matches (no import link; may be unrelated): {len(weak)} files: "
                       + ", ".join(r["path"] for r, _ in weak[:8]) + (" …" if len(weak) > 8 else ""))
        avoided = sum(r["tokens"] or 0 for r, _ in sure[:limit])
        return "\n".join(out), avoided

    def callers(self, name: str, limit: int = 30, **_):
        defs, sure, weak = self._ref_rows(name)
        callers = Counter()
        where = {}
        for r, lines in sure:
            for l in lines:
                enc = self._enclosing(r["file_id"], l)
                key = enc["qualname"] if enc else "<module>"
                callers[(r["path"], key)] += 1
                where.setdefault((r["path"], key), l)
        if not callers:
            return f"no callers of '{name}' found" + (f" (name-only matches in {len(weak)} files: refs {name})" if weak else ""), 0
        out = [f"callers of {name} ({len(callers)}):"]
        for (p, k), c in callers.most_common(limit):
            out.append(f"  {k}  {p}:{where[(p, k)]}" + (f" ×{c}" if c > 1 else ""))
        more = self._more(len(callers), limit)
        if more:
            out.append("  " + more)
        return "\n".join(out), sum(r["tokens"] or 0 for r, _ in sure[:limit])

    def callees(self, target: str, limit: int = 30, **_):
        rows = self._symbols(target, 1)
        if not rows:
            raise QueryError(f"no symbol '{target}'")
        s = rows[0]
        names = []
        for name, lines in self.db.execute("SELECT name, lines FROM idents WHERE file_id=?", (s["file_id"],)):
            ls = [int(x) for x in (lines or "").split(",") if x]
            if any(s["line"] < l <= s["end_line"] for l in ls) and name != s["name"]:
                names.append(name)
        if not names:
            return f"{s['qualname']} references no indexed symbols", 0
        found = []
        for i in range(0, len(names), 400):
            chunk = names[i:i + 400]
            found += self.db.execute(
                f"SELECT s.name, s.qualname, s.kind, s.line, s.rank, f.path FROM symbols s JOIN files f ON f.id=s.file_id "
                f"WHERE s.name IN ({','.join('?' * len(chunk))}) AND s.kind IN ('function','method','class','struct','interface','type','const','enum','trait','record') "
                f"ORDER BY s.rank DESC", chunk).fetchall()
        seen, out = set(), [f"{s['qualname']} ({s['path']}:{s['line']}) uses:"]
        for r in found:
            if r["name"] in seen:
                continue
            seen.add(r["name"])
            out.append(f"  {r['qualname']}  {r['kind']}  {r['path']}:{r['line']}")
            if len(seen) >= limit:
                break
        return "\n".join(out), 0

    # ------------------------------------------------------------------ dependencies
    def _dependents(self, fid: int) -> set:
        """Files that depend on fid: resolved importers + files referencing its distinctive exported names."""
        out = self._dependents_raw(fid)
        target_is_md = self.db.execute("SELECT lang FROM files WHERE id=?", (fid,)).fetchone()
        if not (target_is_md and target_is_md[0] == "markdown") and out:
            md = {r[0] for r in self.db.execute(
                f"SELECT id FROM files WHERE lang='markdown' AND id IN ({','.join(map(str, out))})")}
            out -= md
        return out

    def _dependents_raw(self, fid: int) -> set:
        out = {r[0] for r in self.db.execute("SELECT DISTINCT file_id FROM imports WHERE target_id=?", (fid,))}
        names = [r[0] for r in self.db.execute(
            "SELECT DISTINCT name FROM symbols WHERE file_id=? AND exported=1 AND kind NOT LIKE 'h_' "
            "AND kind NOT IN ('var','field') AND length(name)>=4", (fid,))]
        nd = self._defs_ndefs(names)
        good = [n for n in names if nd.get(n, 1) <= 2]
        for i in range(0, len(good), 400):
            chunk = good[i:i + 400]
            for (f,) in self.db.execute(f"SELECT DISTINCT file_id FROM idents WHERE name IN ({','.join('?' * len(chunk))})", chunk):
                out.add(f)
        out.discard(fid)
        return out

    def _dependencies(self, fid: int) -> set:
        out = {r[0] for r in self.db.execute("SELECT DISTINCT target_id FROM imports WHERE file_id=? AND target_id IS NOT NULL", (fid,))}
        out |= {r[0] for r in self.db.execute("SELECT dst FROM edges WHERE src=? AND weight >= 1.0", (fid,))}
        out.discard(fid)
        return out

    def deps(self, path: str, depth: int = 1, limit: int = 25, **_):
        f = self._file(path)
        out = [f"{f['path']}"]
        uses = sorted(self._dependencies(f["id"]), key=lambda i: self._path(i))
        ext = [r[0] for r in self.db.execute(
            "SELECT DISTINCT external FROM imports WHERE file_id=? AND external IS NOT NULL", (f["id"],))]
        used_by = sorted(self._dependents(f["id"]), key=lambda i: self._path(i))
        out.append(f" uses ({len(uses)}): " + (", ".join(self._path(i) for i in uses[:limit]) or "-") + (" …" if len(uses) > limit else ""))
        if ext:
            out.append(" external: " + ", ".join(e.replace("stdlib:", "") for e in ext[:limit]))
        out.append(f" used by ({len(used_by)}): " + (", ".join(self._path(i) for i in used_by[:limit]) or "-") + (" …" if len(used_by) > limit else ""))
        if depth > 1:
            seen = {f["id"]} | set(uses)
            frontier = set(uses)
            for d in range(2, depth + 1):
                nxt = set()
                for i in frontier:
                    nxt |= self._dependencies(i)
                nxt -= seen
                if not nxt:
                    break
                seen |= nxt
                out.append(f" uses, depth {d} ({len(nxt)}): " + ", ".join(sorted(self._path(i) for i in nxt)[:limit]))
                frontier = nxt
        return "\n".join(out), 0

    def impact(self, target: str, depth: int = 2, limit: int = 30, **_):
        start_files, label = set(), target
        try:
            f = self._file(target)
            start_files = {f["id"]}
            level1 = self._dependents(f["id"])
            label = f["path"]
        except QueryError:
            defs, sure, _ = self._ref_rows(target)
            if not defs:
                raise QueryError(f"'{target}' is neither an indexed file nor a defined symbol")
            start_files = {d["file_id"] for d in defs}
            level1 = {r["file_id"] for r, _ in sure} - start_files
        seen = set(start_files) | level1
        levels = [level1]
        frontier = level1
        for _d in range(2, depth + 1):
            nxt = set()
            for i in frontier:
                nxt |= self._dependents(i)
            nxt -= seen
            if not nxt:
                break
            seen |= nxt
            levels.append(nxt)
            frontier = nxt
        all_files = set().union(*levels) if levels else set()
        info = {r[0]: (r[1], r[2]) for r in self.db.execute(
            f"SELECT id, path, is_test FROM files WHERE id IN ({','.join(map(str, all_files | start_files)) or '0'})")}
        out = [f"impact of {label}: {len(all_files)} dependent files within depth {len(levels)}"]
        for d, lvl in enumerate(levels, 1):
            names = sorted(info[i][0] for i in lvl if not info[i][1])
            if names:
                out.append(f" d{d} ({len(names)}): " + ", ".join(names[:limit]) + (" …" if len(names) > limit else ""))
        tests = sorted(info[i][0] for i in all_files if info[i][1])
        stems = {posixpath.basename(info[i][0]).rsplit(".", 1)[0] for i in start_files}
        for (p,) in self.db.execute("SELECT path FROM files WHERE is_test=1 AND lang IS NOT NULL"):
            b = posixpath.basename(p).rsplit(".", 1)[0].lower()
            if any(s.lower() in b and len(s) > 2 for s in stems) and p not in tests:
                tests.append(p)
        out.append(f" tests ({len(tests)}): " + (", ".join(tests[:limit]) if tests else "none found") + (" …" if len(tests) > limit else ""))
        return "\n".join(out), 0

    def tests(self, target: str, **kw):
        text, _ = self.impact(target, depth=kw.get("depth", 2), limit=kw.get("limit", 40))
        line = next((l for l in text.split("\n") if l.startswith(" tests")), " tests: none found")
        return line.strip(), 0

    def hierarchy(self, name: str, **_):
        rows = self._symbols(name, 3)
        if not rows:
            raise QueryError(f"no type '{name}'")
        out = []
        for r in rows:
            out.append(f"{r['qualname']}  {r['path']}:{r['line']}")
            parents = [b[0] for b in self.db.execute("SELECT base FROM bases WHERE symbol_id=?", (r["id"],))]
            if parents:
                out.append("  extends: " + ", ".join(parents))

            def kids(n, lvl, seen):
                res = self.db.execute("SELECT s.name, s.qualname, f.path, s.line FROM bases b JOIN symbols s ON s.id=b.symbol_id "
                                      "JOIN files f ON f.id=s.file_id WHERE b.base=? LIMIT 25", (n,)).fetchall()
                for k in res:
                    if k["qualname"] in seen:
                        continue
                    seen.add(k["qualname"])
                    out.append("  " * lvl + f"└ {k['qualname']}  {k['path']}:{k['line']}")
                    if lvl < 3:
                        kids(k["name"], lvl + 1, seen)
            kids(r["name"], 1, set())
        return "\n".join(out), 0

    def packages(self, name: str | None = None, limit: int = 40, **_):
        deps = self.db.execute("SELECT DISTINCT ecosystem, name, version, scope, manifest FROM deps ORDER BY ecosystem, name").fetchall()
        usage = Counter()
        files_by_ext = defaultdict(set)
        for ext, fid in self.db.execute("SELECT external, file_id FROM imports WHERE external IS NOT NULL"):
            usage[ext] += 0
            files_by_ext[ext].add(fid)

        def matches(dep_name, ext):
            e = ext.replace("stdlib:", "").replace("node:", "")
            dn = norm_pkg(dep_name.split(":")[-1])
            return (norm_pkg(e) == dn or norm_pkg(PY_IMPORT_ALIASES.get(e, "")) == dn or dep_name == ext
                    or dep_name.endswith("/" + e) or ext.startswith(dep_name))
        if name:
            exts = [e for e in files_by_ext if matches(name, e) or norm_pkg(e) == norm_pkg(name)]
            fids = set().union(*(files_by_ext[e] for e in exts)) if exts else set()
            declared = [d for d in deps if norm_pkg(d["name"].split(":")[-1]) == norm_pkg(name) or d["name"] == name]
            out = [f"{name}: " + (", ".join(f"{d['ecosystem']} {d['version'] or ''} ({d['scope']}, {d['manifest']})".strip() for d in declared)
                                  if declared else "not declared in any manifest")]
            out.append(f" imported by {len(fids)} files: " + ", ".join(sorted(self._path(i) for i in fids)[:limit]))
            return "\n".join(out), 0
        out = []
        used_exts = set()
        by_eco = defaultdict(list)
        for d in deps:
            exts = [e for e in files_by_ext if matches(d["name"], e)]
            used_exts.update(exts)
            n = len(set().union(*(files_by_ext[e] for e in exts))) if exts else 0
            by_eco[d["ecosystem"]].append((d["name"], d["version"], d["scope"], n))
        for eco, items in by_eco.items():
            items.sort(key=lambda t: -t[3])
            out.append(f"{eco} ({len(items)}): " + ", ".join(
                f"{n}{'@' + v if v and len(v) < 14 else ''}{'' if s in ('prod', 'dependencies') else ' [' + s + ']'} ×{c}" for n, v, s, c in items[:limit]))
        undeclared = sorted(((e, len(fs)) for e, fs in files_by_ext.items()
                             if e not in used_exts and not e.startswith(("stdlib:", "node:"))), key=lambda t: -t[1])
        if undeclared:
            out.append("imported but not declared (or name differs): " + ", ".join(f"{e} ×{c}" for e, c in undeclared[:limit]))
        return "\n".join(out) if out else "no manifests or external imports found", 0

    def cycles(self, limit: int = 10, **_):
        edges = defaultdict(dict)
        nodes = set()
        for s, d in self.db.execute("SELECT DISTINCT file_id, target_id FROM imports WHERE target_id IS NOT NULL"):
            if s != d:
                edges[s][d] = 1
                nodes |= {s, d}
        comps = strongly_connected(sorted(nodes), edges)
        if not comps:
            return "no import cycles", 0
        out = [f"{len(comps)} import cycle groups:"]
        for c in comps[:limit]:
            paths = sorted(self._path(i) for i in c)
            out.append(f"  ({len(c)}) " + " ↔ ".join(paths[:8]) + (" …" if len(paths) > 8 else ""))
        return "\n".join(out), 0

    def sql(self, query: str, limit: int = 100, **_):
        if not re.match(r"^\s*(SELECT|WITH|PRAGMA\s+table_info)\b", query, re.I):
            raise QueryError("only read-only SELECT/WITH queries are allowed")
        ro = sqlite3.connect(f"file:{self.s.db_path}?mode=ro", uri=True)
        try:
            cur = ro.execute(query)
            cols = [c[0] for c in cur.description or []]
            rows = cur.fetchmany(limit + 1)
        except sqlite3.Error as e:
            raise QueryError(f"sql error: {e}")
        finally:
            ro.close()
        out = ["\t".join(cols)] + ["\t".join("" if v is None else str(v) for v in r) for r in rows[:limit]]
        if len(rows) > limit:
            out.append(f"(+more rows; add LIMIT/OFFSET)")
        return "\n".join(out), 0

    def schema(self, **_):
        return ("tables (codemap sql \"SELECT …\"):\n"
                " files(id, path, lang, size, lines, tokens, is_test, package, rank)\n"
                " symbols(id, file_id, name, qualname, kind, line, end_line, signature, doc, parent_id, exported, rank)\n"
                " bases(symbol_id, base) · idents(file_id, name, count, lines) — identifier occurrences per file\n"
                " imports(file_id, raw, names, level, line, target_id, external) · deps(manifest, ecosystem, name, version, scope)\n"
                " edges(src, dst, weight, kind) — file graph used for ranking · symbols_fts — full-text over symbols"), 0
