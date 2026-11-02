"""Resolve raw import strings to repository files, or to external package names."""
from __future__ import annotations

import json
import posixpath
import re
import sys
from pathlib import Path

JS_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".d.ts")
NODE_BUILTINS = set("""assert async_hooks buffer child_process cluster console constants crypto dgram diagnostics_channel dns
domain events fs http http2 https inspector module net os path perf_hooks process punycode querystring readline repl
stream string_decoder sys timers tls trace_events tty url util v8 vm wasi worker_threads zlib test""".split())
PY_STDLIB = set(getattr(sys, "stdlib_module_names", ())) or set("""abc argparse array ast asyncio base64 bisect builtins
collections contextlib copy csv dataclasses datetime decimal enum functools glob hashlib heapq hmac html http importlib
inspect io itertools json logging math multiprocessing operator os pathlib pickle platform pprint queue random re shutil
signal socket sqlite3 ssl stat string struct subprocess sys tempfile textwrap threading time timeit traceback types
typing unittest urllib uuid warnings weakref xml zipfile zlib""".split())
MAX_TARGETS = 8  # cap fan-out for package/namespace imports


def _strip_jsonc(text: str) -> str:
    text = re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', lambda m: m.group(1) or "", text, flags=re.S)
    return re.sub(r",(\s*[}\]])", r"\1", text)


class Resolver:
    def __init__(self, root: Path, paths: list, packages: dict):
        """paths: repo-relative POSIX paths; packages: path -> declared package/namespace."""
        self.root = root
        self.paths = set(paths)
        self.by_dir: dict = {}
        self.by_name: dict = {}
        for p in paths:
            d, n = posixpath.split(p)
            self.by_dir.setdefault(d, []).append(p)
            self.by_name.setdefault(n, []).append(p)
        self.py_mod: dict = {}
        for p in paths:
            if p.endswith((".py", ".pyi")):
                parts = p.rsplit(".", 1)[0].split("/")
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                for i in range(len(parts)):
                    self.py_mod.setdefault(".".join(parts[i:]), []).append((i, p))
        self.pkg_files: dict = {}  # java/kotlin/c#/php package -> files
        self.fqcn: dict = {}
        for p, pkg in packages.items():
            if not pkg:
                continue
            self.pkg_files.setdefault(pkg, []).append(p)
            stem = posixpath.basename(p).rsplit(".", 1)[0]
            self.fqcn[f"{pkg}.{stem}"] = p
        self.go_mods = self._go_modules()
        self.ts_configs = self._ts_configs()
        self.cargo_roots = sorted({posixpath.dirname(p) for p in paths if posixpath.basename(p) == "Cargo.toml"},
                                  key=len, reverse=True)
        self.crates = self._cargo_crates()
        self.npm_pkgs = self._npm_packages()
        self.pkg_roots = {k.split(".")[0] for k in self.pkg_files} | {".".join(k.split(".")[:2]) for k in self.pkg_files}

    # ------------------------------------------------------------------ configs
    def _read(self, rel: str) -> str:
        try:
            return (self.root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def _go_modules(self) -> list:
        mods = []
        for p in self.paths:
            if posixpath.basename(p) == "go.mod":
                m = re.search(r"^module\s+(\S+)", self._read(p), re.M)
                if m:
                    mods.append((m.group(1), posixpath.dirname(p)))
        return sorted(mods, key=lambda t: len(t[0]), reverse=True)

    def _cargo_crates(self) -> dict:
        crates = {}
        for d in self.cargo_roots:
            text = self._read(posixpath.join(d, "Cargo.toml") if d else "Cargo.toml")
            m = re.search(r"^\[package\][^\[]*?^\s*name\s*=\s*\"([^\"]+)\"", text, re.M | re.S)
            if m:
                crates[m.group(1).replace("-", "_")] = d
        return crates

    def _npm_packages(self) -> dict:
        pkgs = {}
        for p in self.paths:
            if posixpath.basename(p) == "package.json" and "node_modules/" not in p:
                try:
                    data = json.loads(self._read(p))
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(data, dict) and isinstance(data.get("name"), str):
                    pkgs[data["name"]] = (posixpath.dirname(p), data)
        return pkgs

    def _ts_configs(self) -> dict:
        configs = {}
        for p in self.paths:
            base = posixpath.basename(p)
            if base in ("tsconfig.json", "jsconfig.json") or (base.startswith("tsconfig.") and base.endswith(".json")):
                try:
                    data = json.loads(_strip_jsonc(self._read(p)))
                except (json.JSONDecodeError, ValueError):
                    continue
                opts = data.get("compilerOptions") or {}
                d = posixpath.dirname(p)
                base_url = posixpath.normpath(posixpath.join(d, opts.get("baseUrl", "."))) if opts.get("baseUrl") or opts.get("paths") else None
                if base_url == ".":
                    base_url = ""
                entry = configs.setdefault(d, {"baseUrl": base_url, "paths": {}})
                if base_url is not None and entry["baseUrl"] is None:
                    entry["baseUrl"] = base_url
                entry["paths"].update(opts.get("paths") or {})
        return configs

    def _nearest_ts(self, path: str):
        d = posixpath.dirname(path)
        while True:
            if d in self.ts_configs:
                return self.ts_configs[d]
            if not d:
                return None
            d = posixpath.dirname(d)

    # ------------------------------------------------------------------ helpers
    def _try_files(self, base: str, exts) -> str | None:
        base = posixpath.normpath(base)
        if base.startswith("../"):
            return None
        if base in self.paths:
            return base
        for e in exts:
            if base + e in self.paths:
                return base + e
        for e in exts:
            cand = f"{base}/index{e}"
            if cand in self.paths:
                return cand
        return None

    def _suffix(self, suffix: str, limit: int = MAX_TARGETS) -> list:
        name = posixpath.basename(suffix)
        cands = [p for p in self.by_name.get(name, []) if p == suffix or p.endswith("/" + suffix)]
        return sorted(cands, key=len)[:limit]

    # ------------------------------------------------------------------ main entry
    def resolve(self, path: str, lang: str, raw: str, names=(), level: int = 0):
        """Return (list_of_target_paths, external_name_or_None)."""
        fn = getattr(self, f"_r_{lang}", None)
        if fn is None:
            return [], None
        try:
            return fn(path, raw, names, level)
        except Exception:
            return [], None

    def _r_python(self, path, raw, names, level):
        if level:
            pkg = posixpath.dirname(path).split("/") if posixpath.dirname(path) else []
            if level > 1:
                pkg = pkg[: len(pkg) - (level - 1)]
            base = "/".join(pkg)
            mod_path = posixpath.join(base, raw.replace(".", "/")) if raw else base
            hits = []
            for n in names or [""]:
                for cand in ([posixpath.join(mod_path, n)] if n and n != "*" else []) + [mod_path]:
                    f = self._try_files(cand, (".py", ".pyi")) or self._try_files(cand + "/__init__", (".py",))
                    if f:
                        hits.append(f)
                        break
            return sorted(set(hits)), None
        full = [f"{raw}.{n}" for n in names if n != "*"] + [raw]
        hits = []
        for mod in full:
            cands = self.py_mod.get(mod)
            if cands:
                cands = sorted(cands, key=lambda t: (t[0], len(t[1])))
                hits.append(cands[0][1])
                if mod == raw:
                    break
        if hits:
            return sorted(set(hits)), None
        top = raw.split(".")[0]
        return [], ("stdlib:" + top if top in PY_STDLIB else top)

    def _r_javascript(self, path, raw, names, level):
        if raw.startswith("."):
            f = self._try_files(posixpath.join(posixpath.dirname(path), raw), JS_EXTS)
            return ([f] if f else []), None
        cfg = self._nearest_ts(path)
        if cfg and cfg.get("paths"):
            for pat, targets in cfg["paths"].items():
                prefix = pat[:-1] if pat.endswith("*") else pat
                if (pat.endswith("*") and raw.startswith(prefix)) or raw == pat:
                    rest = raw[len(prefix):] if pat.endswith("*") else ""
                    for t in targets:
                        cand = posixpath.join(cfg.get("baseUrl") or "", t.replace("*", rest))
                        f = self._try_files(cand, JS_EXTS)
                        if f:
                            return [f], None
        if cfg and cfg.get("baseUrl") is not None:
            f = self._try_files(posixpath.join(cfg["baseUrl"], raw), JS_EXTS)
            if f:
                return [f], None
        pkg_name = "/".join(raw.split("/")[:2]) if raw.startswith("@") else raw.split("/")[0]
        if pkg_name in self.npm_pkgs:
            d, data = self.npm_pkgs[pkg_name]
            sub = raw[len(pkg_name):].lstrip("/")
            cands = [posixpath.join(d, "src", sub), posixpath.join(d, sub)] if sub else []
            for field in ("source", "module", "main"):
                v = data.get(field)
                if not sub and isinstance(v, str):
                    cands.append(posixpath.join(d, re.sub(r"^(dist|lib|build)/", "src/", v.lstrip("./")).rsplit(".", 1)[0]))
            if not sub:
                cands += [posixpath.join(d, "src", "index"), posixpath.join(d, "index")]
            for c in cands:
                f = self._try_files(c, JS_EXTS)
                if f:
                    return [f], None
            return [], None  # internal workspace package, entry not found
        if raw.startswith("node:") or raw.split("/")[0] in NODE_BUILTINS:
            return [], "node:" + raw.replace("node:", "").split("/")[0]
        if raw.startswith(("@/", "~/")):
            f = self._try_files("src/" + raw[2:], JS_EXTS)
            return ([f] if f else []), None
        parts = raw.split("/")
        return [], "/".join(parts[:2]) if raw.startswith("@") else parts[0]

    _r_typescript = _r_javascript

    def _r_go(self, path, raw, names, level):
        for mod, d in self.go_mods:
            if raw == mod or raw.startswith(mod + "/"):
                rel = posixpath.join(d, raw[len(mod) + 1:]) if raw != mod else d
                files = [p for p in self.by_dir.get(posixpath.normpath(rel) if rel else "", [])
                         if p.endswith(".go") and not p.endswith("_test.go")]
                return sorted(files)[:MAX_TARGETS], None
        if "." not in raw.split("/")[0]:
            return [], "stdlib:" + raw
        return [], "/".join(raw.split("/")[:3])

    def _r_java(self, path, raw, names, level):
        if raw.endswith(".*"):
            files = self.pkg_files.get(raw[:-2])
            return (sorted(files)[:MAX_TARGETS], None) if files else ([], raw[:-2])
        cur = raw
        while "." in cur:
            if cur in self.fqcn:
                return [self.fqcn[cur]], None
            cur = cur.rsplit(".", 1)[0]
        if any(raw.startswith(r + ".") for r in self.pkg_roots if "." in r):
            return [], None
        segs = raw.split(".")
        pkg = []
        for s in segs[:-1] if len(segs) > 1 else segs:  # package part = lowercase segments
            if s[:1].isupper() or s == "*":
                break
            pkg.append(s)
        pkg = pkg[:3] or segs[:1]
        if pkg[0] in ("java", "javax", "kotlin", "scala", "android", "jdk"):
            return [], "stdlib:" + ".".join(pkg[:2])
        return [], ".".join(pkg)

    _r_kotlin = _r_java
    _r_scala = _r_java

    def _r_csharp(self, path, raw, names, level):
        files = self.pkg_files.get(raw)
        if files:
            return sorted(f for f in files if f != path)[:MAX_TARGETS], None
        if raw in self.fqcn:  # using X = Namespace.Type; / using static Namespace.Type;
            return [self.fqcn[raw]], None
        if any(raw == r or raw.startswith(r + ".") for r in self.pkg_roots if "." in r):
            return [], None
        if raw == "System" or raw.startswith("System."):
            return [], "stdlib:" + ".".join(raw.split(".")[:2])
        return [], ".".join(raw.split(".")[:2])

    def _rust_crate_root(self, path):
        """Directory holding the crate root (lib.rs / main.rs) that owns `path`."""
        d = posixpath.dirname(path)
        while True:
            for root_file in ("lib.rs", "main.rs"):
                if (f"{d}/{root_file}" if d else root_file) in self.paths:
                    return d
            if (f"{d}/Cargo.toml" if d else "Cargo.toml") in self.paths or not d:
                return posixpath.join(d, "src") if d else "src"
            d = posixpath.dirname(d)

    def _rust_module_dir(self, path):
        """Directory where child modules of `path`'s module live (foo.rs -> foo/, mod.rs/lib.rs -> same dir)."""
        d, stem = posixpath.dirname(path), posixpath.basename(path).rsplit(".", 1)[0]
        return d if stem in ("mod", "lib", "main") else posixpath.join(d, stem)

    def _rust_walk(self, base, rest, path):
        for k in range(len(rest), 0, -1):
            stem = posixpath.normpath(posixpath.join(base, *rest[:k])) if base else posixpath.join(*rest[:k])
            for cand in (stem + ".rs", stem + "/mod.rs"):
                if cand in self.paths:
                    return [cand]
        return []

    def _r_rust(self, path, raw, names, level):
        if "::" not in raw and raw not in ("self", "super", "crate"):  # `mod x;` declaration
            d = self._rust_module_dir(path)
            for cand in (f"{d}/{raw}.rs", f"{d}/{raw}/mod.rs"):
                if posixpath.normpath(cand) in self.paths:
                    return [posixpath.normpath(cand)], None
            return [], None
        parts = raw.split("::")
        head = parts[0]
        if head == "crate":
            hits = self._rust_walk(self._rust_crate_root(path), parts[1:], path)
            if hits:
                return hits, None
            root = self._rust_crate_root(path)
            for f in ("lib.rs", "main.rs"):
                cand = posixpath.join(root, f) if root else f
                if cand in self.paths:
                    return [cand], None  # item defined (or re-exported) at the crate root
            return [], None
        if head in ("self", "super"):
            supers = 0
            while supers < len(parts) and parts[supers] == "super":
                supers += 1
            rest = parts[supers:] if head == "super" else parts[1:]
            # Inside inline modules, the first `level` supers stay within this file.
            if supers <= level:
                return [path], None
            supers -= level
            d = self._rust_module_dir(path)
            for _ in range(supers):
                d = posixpath.dirname(d)
            hits = self._rust_walk(d, rest, path)
            if hits:
                return hits, None
            if head == "self" or not rest:
                return [path] if head == "self" else [], None
            for f in ("mod.rs", "lib.rs", "main.rs"):  # item defined in the parent module's file
                cand = posixpath.join(d, f) if d else f
                if cand in self.paths:
                    return [cand], None
            parent_file = d + ".rs"
            return ([parent_file], None) if parent_file in self.paths else ([], None)
        if head in ("std", "core", "alloc"):
            return [], "stdlib:" + head
        if head in self.crates:
            base = posixpath.join(self.crates[head], "src") if self.crates[head] else "src"
            hits = self._rust_walk(base, parts[1:], path)
            if hits:
                return hits, None
            for cand in (base + "/lib.rs", base + "/main.rs"):
                if cand in self.paths:
                    return [cand], None
            return [], None
        return [], head

    def _r_c(self, path, raw, names, level):
        local = posixpath.normpath(posixpath.join(posixpath.dirname(path), raw))
        if local in self.paths:
            return [local], None
        hits = self._suffix(raw, 1)
        return (hits, None) if hits else ([], raw)

    _r_cpp = _r_c

    def _r_php(self, path, raw, names, level):
        if raw.endswith(".php"):
            local = posixpath.normpath(posixpath.join(posixpath.dirname(path), raw))
            return ([local], None) if local in self.paths else (self._suffix(raw.lstrip("./"), 1), None)
        parts = raw.strip("\\").split("\\")
        for k in range(min(len(parts), 3), 0, -1):
            hits = self._suffix("/".join(parts[-k:]) + ".php", 1)
            if hits:
                return hits, None
        return [], parts[0]

    def _r_ruby(self, path, raw, names, level):
        rel = raw if raw.endswith(".rb") else raw + ".rb"
        local = posixpath.normpath(posixpath.join(posixpath.dirname(path), rel))
        if local in self.paths:
            return [local], None
        hits = self._suffix(rel, 1)
        return (hits, None) if hits else ([], raw.split("/")[0])

    def _r_swift(self, path, raw, names, level):
        files = [p for d, ps in self.by_dir.items() if d.endswith("Sources/" + raw) for p in ps if p.endswith(".swift")]
        return (sorted(files)[:MAX_TARGETS], None) if files else ([], raw)

    def _r_markdown(self, path, raw, names, level):
        target = posixpath.normpath(posixpath.join(posixpath.dirname(path), raw.split("?")[0]))
        if target in self.paths:
            return [target], None
        if target + "/README.md" in self.paths:
            return [target + "/README.md"], None
        return [], None
