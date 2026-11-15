#!/usr/bin/env python3
"""Measure codemap's C# and Rust extraction against tree-sitter (dev tool, not a test).

    pip install tree-sitter tree-sitter-c-sharp tree-sitter-rust   # in a venv
    python tests/eval_extraction.py path/to/repo [more repos …] [--show-misses N] [--legacy]

For every .cs / .rs file it compares declarations (category, name, name line) and
reports recall, precision, end-line accuracy and parent accuracy per category.
tree-sitter is used only as the oracle here; codemap itself stays stdlib-only.
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins" / "codemap" / "scripts"))
from codemap_core.extract import extract  # noqa: E402

import tree_sitter as ts  # noqa: E402
import tree_sitter_c_sharp as ts_cs  # noqa: E402
import tree_sitter_rust as ts_rs  # noqa: E402

CS_TYPES = {"class_declaration", "struct_declaration", "interface_declaration", "enum_declaration",
            "record_declaration", "record_struct_declaration", "delegate_declaration"}
CS_METHODS = {"method_declaration", "constructor_declaration", "destructor_declaration"}
CS_PROPS = {"property_declaration", "indexer_declaration", "event_declaration"}
CS_FIELDS = {"field_declaration", "event_field_declaration"}
CS_NS = {"namespace_declaration", "file_scoped_namespace_declaration"}
CS_BODYLESS_STOP = {"block", "arrow_expression_clause", "accessor_list", "lambda_expression", "local_function_statement"}

RS_FN = {"function_item", "function_signature_item"}
RS_TYPES = {"struct_item", "enum_item", "union_item", "trait_item", "type_item", "associated_type"}
RS_OTHER = {"const_item": "const", "static_item": "const", "mod_item": "module", "macro_definition": "macro",
            "impl_item": "impl"}
RS_STOP = {"closure_expression", "macro_invocation", "token_tree"}

CODEMAP_CATEGORY = {
    "csharp": {"class": "type", "struct": "type", "interface": "type", "enum": "type", "record": "type",
               "delegate": "type", "method": "method", "function": "method", "property": "property",
               "indexer": "property", "event": "property", "field": "field", "const": "field",
               "namespace": "namespace"},
    "rust": {"function": "fn", "method": "fn", "struct": "type", "enum": "type", "union": "type", "trait": "type",
             "type": "type", "const": "const", "module": "module", "macro": "macro", "impl": "impl"},
}


def _text(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")


def ts_defs_cs(root, src):
    out = []

    def walk(node, parent_name):
        t = node.type
        name = None
        if t in CS_TYPES | CS_METHODS | CS_PROPS | CS_NS:
            nn = node.child_by_field_name("name")
            if t == "indexer_declaration":
                name, line = "this", node.start_point[0] + 1
                for c in node.children:
                    if c.type == "this":
                        line = c.start_point[0] + 1
            elif t == "event_declaration" and nn is None:
                nn = node.child_by_field_name("name")
            if nn is not None:
                name, line = _text(nn, src).split(".")[-1], nn.start_point[0] + 1
            if name:
                cat = ("type" if t in CS_TYPES else "method" if t in CS_METHODS else "property" if t in CS_PROPS
                       else "namespace")
                if t == "namespace_declaration" or t == "file_scoped_namespace_declaration":
                    name = _text(nn, src)
                out.append((cat, name, line, node.end_point[0] + 1, parent_name))
        elif t in CS_FIELDS:
            for d in _descend(node, "variable_declarator"):
                nn = d.child_by_field_name("name") or next((c for c in d.children if c.type == "identifier"), None)
                if nn is not None:
                    out.append(("field", _text(nn, src), nn.start_point[0] + 1, node.end_point[0] + 1, parent_name))
            return
        if t in CS_BODYLESS_STOP:
            return
        child_parent = name if name and t in CS_TYPES | CS_NS else parent_name
        if t == "file_scoped_namespace_declaration":  # members are siblings in the tree
            pass
        for c in node.children:
            walk(c, child_parent)

    walk(root, None)
    # file-scoped namespace: members appear as siblings; give them the namespace as parent
    ns = next((d for d in out if d[0] == "namespace"), None)
    if ns and any(n.type == "file_scoped_namespace_declaration" for n in root.children):
        out = [(c, n, l, e, p if p is not None else ns[1]) if c != "namespace" else (c, n, l, e, p) for c, n, l, e, p in out]
    return out


def _descend(node, typ):
    for c in node.children:
        if c.type == typ:
            yield c
        else:
            yield from _descend(c, typ)


def ts_defs_rs(root, src):
    out = []

    def walk(node, parent_name):
        t = node.type
        if t in RS_STOP:
            return
        if t in RS_FN | RS_TYPES | set(RS_OTHER):
            if t == "impl_item":
                tn = node.child_by_field_name("type")
                txt = _text(tn, src) if tn is not None else "?"
                depth, name = 0, "?"
                for tok in re.findall(r"[<>]|(?:r#)?[A-Za-z_]\w*", txt):  # last identifier outside <...>
                    if tok == "<":
                        depth += 1
                    elif tok == ">":
                        depth = max(0, depth - 1)
                    elif depth == 0 and tok not in ("mut", "dyn", "for", "impl", "const"):
                        name = tok
                line = tn.start_point[0] + 1 if tn is not None else node.start_point[0] + 1
            else:
                nn = node.child_by_field_name("name")
                if nn is None:
                    for c in node.children:
                        walk(c, parent_name)
                    return
                name, line = _text(nn, src), nn.start_point[0] + 1
            cat = "fn" if t in RS_FN else "type" if t in RS_TYPES else RS_OTHER[t]
            out.append((cat, name, line, node.end_point[0] + 1, parent_name))
            if t in ("impl_item", "trait_item", "mod_item", "function_item"):
                for c in node.children:
                    walk(c, name)
            return
        for c in node.children:
            walk(c, parent_name)

    walk(root, None)
    return out


LEGACY = False


def codemap_defs(text, lang):
    if LEGACY:  # the pre-parser pattern extractor, for before/after comparisons
        from codemap_core.extract import extract_generic
        facts = extract_generic(text, lang)
    else:
        facts = extract(text, lang)
    syms = facts.symbols
    cmap = CODEMAP_CATEGORY[lang]
    out = []
    for s in syms:
        cat = cmap.get(s.kind)
        if not cat:
            continue
        parent = syms[s.parent].name if s.parent is not None else None
        name = s.name
        out.append((cat, name, s.line, s.end_line, parent))
    return out


def main(argv):
    global LEGACY
    if "--legacy" in argv:
        LEGACY = True
        argv = [a for a in argv if a != "--legacy"]
    show = 0
    if "--show-misses" in argv:
        i = argv.index("--show-misses")
        show = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    parsers = {"csharp": ts.Parser(ts.Language(ts_cs.language())), "rust": ts.Parser(ts.Language(ts_rs.language()))}
    stats = defaultdict(lambda: Counter())
    misses = defaultdict(list)
    for repo in argv:
        repo = Path(repo)
        files = subprocess.run(["git", "ls-files", "*.cs", "*.rs"], cwd=repo, capture_output=True, text=True).stdout.split()
        for rel in files:
            lang = "csharp" if rel.endswith(".cs") else "rust"
            try:
                src = (repo / rel).read_bytes()
                text = src.decode("utf-8-sig", "replace")
            except OSError:
                continue
            src = text.encode("utf-8")
            tree = parsers[lang].parse(src)
            truth = (ts_defs_cs if lang == "csharp" else ts_defs_rs)(tree.root_node, src)
            ours = codemap_defs(text, lang)
            tk = {(c, n, l): (e, p) for c, n, l, e, p in truth}
            ok = {(c, n, l): (e, p) for c, n, l, e, p in ours}
            for key, (e, p) in tk.items():
                st = stats[(lang, key[0])]
                st["truth"] += 1
                if key in ok:
                    st["hit"] += 1
                    st["end_ok"] += int(ok[key][0] == e)
                    st["parent_ok"] += int((ok[key][1] or None) == (p or None))
                    if ok[key][0] != e and len(misses[(lang, key[0], "end")]) < 200:
                        misses[(lang, key[0], "end")].append(f"{repo.name}/{rel}:{key[2]} {key[1]} end ours={ok[key][0]} ts={e}")
                    if (ok[key][1] or None) != (p or None) and len(misses[(lang, key[0], "parent")]) < 200:
                        misses[(lang, key[0], "parent")].append(f"{repo.name}/{rel}:{key[2]} {key[1]} parent ours={ok[key][1]} ts={p}")
                elif len(misses[(lang, key[0], "missed")]) < 400:
                    misses[(lang, key[0], "missed")].append(f"{repo.name}/{rel}:{key[2]} {key[1]}")
            for key in ok:
                stats[(lang, key[0])]["ours"] += 1
                if key not in tk and len(misses[(lang, key[0], "extra")]) < 400:
                    misses[(lang, key[0], "extra")].append(f"{repo.name}/{rel}:{key[2]} {key[1]}")
    print("| Lang | Category | Declarations | Recall | Precision | End line | Parent |")
    print("|---|---|---:|---:|---:|---:|---:|")
    tot = defaultdict(Counter)
    for (lang, cat), st in sorted(stats.items()):
        if not st["truth"]:
            continue
        r = st["hit"] / st["truth"]
        pr = st["hit"] / st["ours"] if st["ours"] else 0
        e = st["end_ok"] / st["hit"] if st["hit"] else 0
        pa = st["parent_ok"] / st["hit"] if st["hit"] else 0
        print(f"| {lang} | {cat} | {st['truth']:,} | {r:.1%} | {pr:.1%} | {e:.1%} | {pa:.1%} |")
        for k in ("truth", "hit", "ours", "end_ok", "parent_ok"):
            tot[lang][k] += st[k]
    for lang, st in tot.items():
        print(f"| **{lang}** | **all** | {st['truth']:,} | **{st['hit'] / st['truth']:.1%}** | **{st['hit'] / max(st['ours'], 1):.1%}** | "
              f"{st['end_ok'] / max(st['hit'], 1):.1%} | {st['parent_ok'] / max(st['hit'], 1):.1%} |")
    if show:
        for key, items in sorted(misses.items()):
            print(f"\n## {key} ({len(items)}{'+' if len(items) >= 200 else ''})")
            for it in items[:show]:
                print("  " + it)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
