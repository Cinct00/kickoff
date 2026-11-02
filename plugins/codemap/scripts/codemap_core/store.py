"""SQLite-backed index: schema, incremental refresh, ranking."""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import time
from pathlib import Path

from . import SCHEMA_VERSION, VERSION
from .extract import extract
from .graph import pagerank
from .manifests import is_manifest, parse_manifest
from .resolve import Resolver
from .util import CODE_LANGS, content_hash, est_tokens, git, is_test_path, lang_of, list_files, read_text, split_words

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS files(
  id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, lang TEXT, size INT, mtime REAL, hash TEXT,
  lines INT, tokens INT, is_test INT DEFAULT 0, package TEXT, rank REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS symbols(
  id INTEGER PRIMARY KEY, file_id INT NOT NULL, name TEXT NOT NULL, qualname TEXT, kind TEXT, line INT, end_line INT,
  signature TEXT, doc TEXT, parent_id INT, exported INT, rank REAL DEFAULT 0);
CREATE INDEX IF NOT EXISTS sym_name ON symbols(name);
CREATE INDEX IF NOT EXISTS sym_file ON symbols(file_id, line);
CREATE TABLE IF NOT EXISTS bases(symbol_id INT, base TEXT);
CREATE INDEX IF NOT EXISTS bases_base ON bases(base);
CREATE TABLE IF NOT EXISTS idents(file_id INT, name TEXT, count INT, lines TEXT, PRIMARY KEY(file_id, name)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idents_name ON idents(name);
CREATE TABLE IF NOT EXISTS imports(
  file_id INT, raw TEXT, names TEXT, level INT, line INT, target_id INT, external TEXT);
CREATE INDEX IF NOT EXISTS imp_file ON imports(file_id);
CREATE INDEX IF NOT EXISTS imp_target ON imports(target_id);
CREATE INDEX IF NOT EXISTS imp_ext ON imports(external);
CREATE TABLE IF NOT EXISTS deps(manifest TEXT, ecosystem TEXT, name TEXT, version TEXT, scope TEXT);
CREATE TABLE IF NOT EXISTS edges(src INT, dst INT, weight REAL, kind TEXT, PRIMARY KEY(src, dst, kind)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS edges_dst ON edges(dst);
CREATE TABLE IF NOT EXISTS usage(ts REAL, cmd TEXT, out_tokens INT, avoided_tokens INT);
CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
  name, words, qualname, signature, path, tokenize = "unicode61 tokenchars '_'");
"""

RANK_MAX_AGE = 600  # seconds before a lazy refresh also recomputes ranks
LAZY_MIN_GAP = 3  # seconds between lazy refreshes


class Store:
    def __init__(self, root: Path, db_path: Path):
        self.root = root
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db_path), timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("PRAGMA temp_store=MEMORY")
        ver = self._meta_raw("schema")
        if ver is not None and ver != str(SCHEMA_VERSION):
            self._reset()
        self.db.executescript(SCHEMA)
        self.set_meta("schema", str(SCHEMA_VERSION))
        self.set_meta("root", str(root))

    # ------------------------------------------------------------------ meta
    def _meta_raw(self, key):
        try:
            row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        except sqlite3.OperationalError:
            return None
        return row[0] if row else None

    def meta(self, key, default=None):
        v = self._meta_raw(key)
        return default if v is None else v

    def set_meta(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, str(value)))

    def _reset(self):
        for t in ("meta", "files", "symbols", "bases", "idents", "imports", "deps", "edges", "usage", "symbols_fts"):
            self.db.execute(f"DROP TABLE IF EXISTS {t}")

    def log_usage(self, cmd: str, out_tokens: int, avoided: int):
        try:
            self.db.execute("INSERT INTO usage VALUES(?,?,?,?)", (time.time(), cmd, out_tokens, max(0, avoided)))
        except sqlite3.OperationalError:
            pass

    # ------------------------------------------------------------------ refresh
    def refresh(self, lazy: bool = False, force_ranks: bool = False, progress=None) -> dict:
        """Bring the index in line with the working tree. Returns change stats."""
        now = time.time()
        if lazy and now - float(self.meta("last_refresh", 0)) < LAZY_MIN_GAP and not force_ranks:
            return {"skipped": True}
        try:
            self.db.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            if lazy:
                return {"busy": True}
            raise
        try:
            stats = self._refresh_locked(lazy, force_ranks, progress)
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return stats

    def _refresh_locked(self, lazy, force_ranks, progress):
        t0 = time.time()
        paths = list_files(self.root)
        existing = {r["path"]: r for r in self.db.execute("SELECT id, path, size, mtime, hash, lang FROM files")}
        current = set(paths)
        deleted = [r["id"] for p, r in existing.items() if p not in current]
        for fid in deleted:
            self._delete_file_rows(fid, also_file=True)

        added, changed, manifests_touched = 0, [], bool(deleted and any(is_manifest(p) for p in existing if p not in current))
        packages_changed = False
        for i, p in enumerate(paths):
            if progress and i % 500 == 0:
                progress(i, len(paths))
            full = self.root / p
            try:
                st = full.stat()
            except OSError:
                continue
            old = existing.get(p)
            if old is not None and old["size"] == st.st_size and abs((old["mtime"] or 0) - st.st_mtime) < 1e-6:
                continue
            lang = lang_of(p)
            if is_manifest(p):
                manifests_touched = True
            if lang is None:
                # Non-code file: record it for tree/files queries without reading it.
                if old is None:
                    self.db.execute("INSERT INTO files(path, lang, size, mtime, lines, tokens, is_test) VALUES(?,?,?,?,?,?,?)",
                                    (p, None, st.st_size, st.st_mtime, None, est_tokens(st.st_size), int(is_test_path(p))))
                    added += 1
                else:
                    self.db.execute("UPDATE files SET size=?, mtime=?, tokens=? WHERE id=?",
                                    (st.st_size, st.st_mtime, est_tokens(st.st_size), old["id"]))
                continue
            text = read_text(full)
            if text is None:
                continue
            h = content_hash(text)
            if old is not None and old["hash"] == h:
                self.db.execute("UPDATE files SET mtime=?, size=? WHERE id=?", (st.st_mtime, st.st_size, old["id"]))
                continue
            facts = extract(text, lang)
            if old is not None:
                fid = old["id"]
                self._delete_file_rows(fid, also_file=False)
                prev_pkg = self.db.execute("SELECT package FROM files WHERE id=?", (fid,)).fetchone()[0]
                packages_changed |= (prev_pkg or "") != (facts.package or "")
                self.db.execute("UPDATE files SET lang=?, size=?, mtime=?, hash=?, lines=?, tokens=?, is_test=?, package=? WHERE id=?",
                                (lang, st.st_size, st.st_mtime, h, text.count("\n") + 1, est_tokens(text), int(is_test_path(p)),
                                 facts.package, fid))
            else:
                cur = self.db.execute(
                    "INSERT INTO files(path, lang, size, mtime, hash, lines, tokens, is_test, package) VALUES(?,?,?,?,?,?,?,?,?)",
                    (p, lang, st.st_size, st.st_mtime, h, text.count("\n") + 1, est_tokens(text), int(is_test_path(p)), facts.package))
                fid = cur.lastrowid
                added += 1
                packages_changed |= bool(facts.package)
            self._store_facts(fid, p, facts)
            changed.append(fid)

        structure_changed = bool(added or deleted or packages_changed)
        if structure_changed or changed:
            self._resolve_imports(None if structure_changed else changed)
        if manifests_touched or self.meta("deps_done") is None:
            self._index_deps()
            self.set_meta("deps_done", 1)

        dirty = bool(changed or deleted or added)
        last_rank = float(self.meta("last_rank", 0))
        need_ranks = force_ranks or (dirty and (not lazy or structure_changed or time.time() - last_rank > RANK_MAX_AGE)) \
            or last_rank == 0
        if need_ranks:
            self._compute_ranks()
            self.set_meta("last_rank", time.time())
        elif dirty:
            self.set_meta("ranks_stale", 1)
        self.set_meta("last_refresh", time.time())
        head = git(["rev-parse", "--short", "HEAD"], self.root)
        if head:
            self.set_meta("git_head", head.strip())
        self.set_meta("version", VERSION)
        return {"files": len(paths), "added": added, "updated": len(changed), "deleted": len(deleted),
                "ranked": need_ranks, "seconds": round(time.time() - t0, 2)}

    def _delete_file_rows(self, fid: int, also_file: bool):
        sym_ids = [r[0] for r in self.db.execute("SELECT id FROM symbols WHERE file_id=?", (fid,))]
        if sym_ids:
            self.db.executemany("DELETE FROM symbols_fts WHERE rowid=?", [(s,) for s in sym_ids])
            self.db.executemany("DELETE FROM bases WHERE symbol_id=?", [(s,) for s in sym_ids])
        self.db.execute("DELETE FROM symbols WHERE file_id=?", (fid,))
        self.db.execute("DELETE FROM idents WHERE file_id=?", (fid,))
        self.db.execute("DELETE FROM imports WHERE file_id=?", (fid,))
        self.db.execute("DELETE FROM edges WHERE src=?", (fid,))
        if also_file:
            self.db.execute("UPDATE imports SET target_id=NULL WHERE target_id=?", (fid,))
            self.db.execute("DELETE FROM edges WHERE dst=?", (fid,))
            self.db.execute("DELETE FROM files WHERE id=?", (fid,))

    def _store_facts(self, fid: int, path: str, facts):
        ids = []
        for s in facts.symbols:
            parent_id = ids[s.parent] if s.parent is not None and s.parent < len(ids) else None
            cur = self.db.execute(
                "INSERT INTO symbols(file_id, name, qualname, kind, line, end_line, signature, doc, parent_id, exported) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (fid, s.name, s.qualname or s.name, s.kind, s.line, s.end_line, s.signature, s.doc, parent_id, int(s.exported)))
            sid = cur.lastrowid
            ids.append(sid)
            self.db.execute("INSERT INTO symbols_fts(rowid, name, words, qualname, signature, path) VALUES(?,?,?,?,?,?)",
                            (sid, s.name, split_words(s.name), s.qualname, s.signature, path))
            for b in s.bases:
                self.db.execute("INSERT INTO bases VALUES(?,?)", (sid, b))
        self.db.executemany("INSERT OR REPLACE INTO idents VALUES(?,?,?,?)",
                            [(fid, n, c, ",".join(map(str, ls))) for n, (c, ls) in facts.idents.items()])
        self.db.executemany("INSERT INTO imports(file_id, raw, names, level, line) VALUES(?,?,?,?,?)",
                            [(fid, i.raw, json.dumps(i.names) if i.names else None, i.level, i.line) for i in facts.imports])

    def _resolve_imports(self, only_files):
        rows = list(self.db.execute("SELECT id, path, lang, package FROM files WHERE lang IS NOT NULL"))
        paths = [r["path"] for r in self.db.execute("SELECT path FROM files")]
        resolver = Resolver(self.root, paths, {r["path"]: r["package"] for r in rows if r["package"]})
        path_id = {r["path"]: r["id"] for r in self.db.execute("SELECT id, path FROM files")}
        by_id = {r["id"]: r for r in rows}
        if only_files is None:  # drop fan-out rows from the previous resolution before re-resolving
            self.db.execute("DELETE FROM imports WHERE rowid NOT IN (SELECT MIN(rowid) FROM imports GROUP BY file_id, raw, line)")
        q = "SELECT rowid, file_id, raw, names, level, line FROM imports"
        if only_files is not None:
            q += f" WHERE file_id IN ({','.join('?' * len(only_files))})"
        imports = list(self.db.execute(q, tuple(only_files or ())))
        updates, extra = [], []
        for imp in imports:
            f = by_id.get(imp["file_id"])
            if f is None:
                continue
            names = json.loads(imp["names"]) if imp["names"] else []
            targets, external = resolver.resolve(f["path"], f["lang"], imp["raw"], names, imp["level"] or 0)
            tids = [path_id[t] for t in targets if t in path_id and path_id[t] != imp["file_id"]]
            updates.append((tids[0] if tids else None, external, imp["rowid"]))
            for t in tids[1:]:
                extra.append((imp["file_id"], imp["raw"], imp["names"], imp["level"], imp["line"], t, None))
        self.db.executemany("UPDATE imports SET target_id=?, external=? WHERE rowid=?", updates)
        self.db.executemany("INSERT INTO imports(file_id, raw, names, level, line, target_id, external) VALUES(?,?,?,?,?,?,?)", extra)

    def _index_deps(self):
        self.db.execute("DELETE FROM deps")
        for (path,) in list(self.db.execute("SELECT path FROM files")):
            if is_manifest(path):
                for eco, name, ver, scope in parse_manifest(self.root, path):
                    self.db.execute("INSERT INTO deps VALUES(?,?,?,?,?)", (path, eco, name, ver, scope))

    # ------------------------------------------------------------------ ranking
    def _compute_ranks(self):
        """Aider-style: weighted def/ref file graph -> PageRank -> per-symbol scores."""
        defs: dict = {}
        for r in self.db.execute("SELECT DISTINCT name, file_id FROM symbols WHERE kind NOT LIKE 'h_' AND kind != 'field'"):
            defs.setdefault(r[0], set()).add(r[1])
        code_files = [r[0] for r in self.db.execute("SELECT id FROM files WHERE lang IS NOT NULL")]
        edges: dict = {}
        ref_pairs = []  # (src, name, weight)
        for fid, name, count in self.db.execute(
                "SELECT i.file_id, i.name, i.count FROM idents i WHERE i.name IN (SELECT name FROM symbols)"):
            dfiles = defs.get(name)
            if not dfiles:
                continue
            mul = 1.0
            if len(name) >= 8 and (("_" in name.strip("_")) or re.search(r"[a-z][A-Z]", name)):
                mul *= 10
            if name.startswith("_"):
                mul *= 0.1
            if len(dfiles) > 5:
                mul *= 0.1
            w = mul * math.sqrt(count)
            targets = [d for d in dfiles if d != fid]
            if not targets:
                continue
            ref_pairs.append((fid, name, w, targets))
            for d in targets:
                row = edges.setdefault(fid, {})
                row[d] = row.get(d, 0.0) + w / len(dfiles)
        for src, dst in self.db.execute("SELECT DISTINCT file_id, target_id FROM imports WHERE target_id IS NOT NULL"):
            row = edges.setdefault(src, {})
            row[dst] = row.get(dst, 0.0) + 0.5
        rank = pagerank(code_files, edges)

        self.db.execute("DELETE FROM edges")
        self.db.executemany("INSERT INTO edges VALUES(?,?,?,?)",
                            [(s, d, w, "ref") for s, ds in edges.items() for d, w in ds.items()])
        self.db.executemany("UPDATE files SET rank=? WHERE id=?", [(v, k) for k, v in rank.items()])

        out_w = {s: sum(ds.values()) for s, ds in edges.items()}
        sym_score: dict = {}
        for src, name, w, targets in ref_pairs:
            ow = out_w.get(src)
            if not ow:
                continue
            share = rank.get(src, 0.0) * w / len(targets) / ow
            for d in targets:
                sym_score[(d, name)] = sym_score.get((d, name), 0.0) + share
        updates = []
        for sid, fid, name, exported in self.db.execute("SELECT id, file_id, name, exported FROM symbols"):
            base = rank.get(fid, 0.0) * (0.02 if exported else 0.005)
            updates.append((sym_score.get((fid, name), 0.0) + base, sid))
        self.db.executemany("UPDATE symbols SET rank=? WHERE id=?", updates)
        self.set_meta("ranks_stale", 0)


def open_store(root: Path, db_path: Path) -> Store:
    return Store(root, db_path)


def db_exists(db_path: Path) -> bool:
    return db_path.exists() and os.path.getsize(db_path) > 0
