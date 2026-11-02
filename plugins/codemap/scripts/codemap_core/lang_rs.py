"""Structural Rust extractor: items with scopes, expanded `use` trees and identifiers (stdlib only)."""
from __future__ import annotations

import re

from .extract import IDENT_RX, KEYWORDS, FileFacts, Imp, Sym, _add_ident, _clip, _doc_above
from .lexer import mask_rust, tokenize

QUALIFIERS = {"pub", "default", "const", "async", "unsafe", "extern", "safe"}
ITEM_KW = {"fn", "struct", "enum", "union", "trait", "impl", "mod", "type", "const", "static", "macro_rules", "use"}
RS_KEYWORDS = KEYWORDS | {"move", "dyn", "where", "loop", "box", "unsized", "virtual", "yield", "try", "macro"}
IDENT = re.compile(r"(?:r#)?[A-Za-z_]\w*$")


class _P:
    def __init__(self, text: str):
        self.code, self.cstr = mask_rust(text)
        self.lines = text.split("\n")
        self.tk = tokenize(self.code)
        self.t = self.tk.text
        self.n = len(self.t)
        self.syms: list = []
        self.imports: list = []
        self.mod_depth = 0  # inline `mod x { … }` nesting, so `super::` can be resolved correctly

    def close(self, i):
        return self.tk.match.get(i, self.n - 1)

    def sig(self, a, b):
        s = self.tk.start[a]
        e = self.tk.start[b] if b < self.n else len(self.cstr)
        return _clip(self.cstr[s:e])

    def add(self, name, kind, name_i, start_i, end_i, sig_end_i, parent, exported, bases=()):
        line = self.tk.line[name_i]
        self.syms.append(Sym(name=name, kind=kind, line=line, end_line=max(line, self.tk.line[min(end_i, self.n - 1)]),
                             signature=self.sig(start_i, sig_end_i), doc=_doc_above(self.lines, self.tk.line[start_i]),
                             parent=parent, exported=exported, bases=list(bases)))
        return len(self.syms) - 1

    def skip_generics(self, i):
        """i at '<' -> index after the matching '>' (handles '->' / '=>' tokens)."""
        depth = 0
        while i < self.n:
            t = self.t[i]
            if t == "<":
                depth += 1
            elif t == ">":
                depth -= 1
                if depth == 0:
                    return i + 1
            elif t in "([":
                i = self.close(i)
            elif t in ("{", ";"):
                return i
            i += 1
        return i

    def to_body(self, i):
        """Advance to the '{' or ';' that ends an item header (brackets and generics balanced)."""
        depth = 0
        while i < self.n:
            t = self.t[i]
            if t in "([":
                i = self.close(i) + 1
                continue
            if t == "<":
                depth += 1
            elif t == ">" and depth:
                depth -= 1
            elif depth == 0 and t in ("{", ";"):
                return i
            elif t == "}":
                return i
            i += 1
        return self.n - 1

    def to_semicolon(self, i):
        while i < self.n:
            t = self.t[i]
            if t in "({[":
                i = self.close(i) + 1
                continue
            if t == ";":
                return i
            if t == "}":
                return i - 1
            i += 1
        return self.n - 1

    # ------------------------------------------------------------------ scan
    def scan(self, i, end, parent, parent_kind):
        at_start = True
        while i < end:
            t = self.t[i]
            if at_start:
                j = self.item(i, end, parent, parent_kind)
                if j is not None:
                    i = j
                    at_start = True
                    continue
            at_start = t in ("{", "}", ";")
            i += 1

    def item(self, i, end, parent, parent_kind):
        """Try to parse an item at i. Returns the index after it, or None."""
        start = i
        while i < end and self.t[i] == "#":  # attributes #[...] / #![...]
            j = i + 1
            if j < end and self.t[j] == "!":
                j += 1
            if j < end and self.t[j] == "[":
                i = self.close(j) + 1
                start = i
            else:
                return None
        pub = False
        head = i
        while i < end:
            t = self.t[i]
            if t == "pub":
                pub = True
                i += 1
                if i < end and self.t[i] == "(":
                    i = self.close(i) + 1
                continue
            if t == "extern" and i + 1 < end and self.t[i + 1] == '"':  # extern "C"
                i += 3
                continue
            if t in ("default", "async", "unsafe", "safe", "extern") and i + 1 < end and self.t[i + 1] in (
                    "fn", "impl", "trait", "unsafe", "async", "extern", "const", "{", "mod", "crate", '"'):
                if t == "extern" and self.t[i + 1] == "{":
                    body = self.close(i + 1)
                    self.scan(i + 2, body, parent, parent_kind)
                    return body + 1
                if t == "extern" and self.t[i + 1] == "crate":
                    k = self.to_semicolon(i)
                    self.imports.append(Imp(raw=self.t[i + 2], line=self.tk.line[i]))
                    return k + 1
                i += 1
                continue
            if t == "const" and i + 1 < end and self.t[i + 1] in ("fn", "unsafe", "async", "extern"):
                i += 1
                continue
            break
        if i >= end:
            return None
        kw = self.t[i]
        exported = pub or parent_kind == "trait"
        if kw == "fn" and i + 1 < end and IDENT.match(self.t[i + 1]):
            name_i = i + 1
            k = self.to_body(i + 2)
            kind = "method" if parent_kind in ("impl", "trait") else "function"
            if k < end and self.t[k] == "{":
                body = self.close(k)
                idx = self.add(self.t[name_i], kind, name_i, head, body, k, parent, exported)
                self.scan(k + 1, body, idx, "fn")
                return body + 1
            self.add(self.t[name_i], kind, name_i, head, k, k, parent, exported)
            return k + 1
        if kw in ("struct", "enum", "union", "trait") and i + 1 < end and IDENT.match(self.t[i + 1]):
            if kw == "union" and not (i + 2 < end and self.t[i + 2] in ("<", "{", "where")):
                return None
            name_i = i + 1
            k = i + 2
            if k < end and self.t[k] == "<":
                k = self.skip_generics(k)
            if k < end and self.t[k] == "(":  # tuple struct
                k = self.close(k) + 1
            bases = []
            if kw == "trait" and k < end and self.t[k] == ":":
                j = k + 1
                while j < end and self.t[j] not in ("{", ";", "where"):
                    if self.t[j] == "<":
                        j = self.skip_generics(j)
                        continue
                    if IDENT.match(self.t[j]) and (j + 1 >= end or self.t[j + 1] != "::"):
                        bases.append(self.t[j])
                    j += 1
            k = self.to_body(k)
            if k < end and self.t[k] == "{":
                body = self.close(k)
                idx = self.add(self.t[name_i], kw, name_i, head, body, k, parent, exported, bases)
                if kw == "trait":
                    self.scan(k + 1, body, idx, "trait")
                return body + 1
            self.add(self.t[name_i], kw, name_i, head, k, k, parent, exported, bases)
            return k + 1
        if kw == "impl":
            k = i + 1
            if k < end and self.t[k] == "<":
                k = self.skip_generics(k)
            seg_start = k
            trait = None
            j = k
            depth = 0
            while j < end:
                t = self.t[j]
                if t == "<":
                    depth += 1
                elif t == ">" and depth:
                    depth -= 1
                elif t in "([":
                    j = self.close(j) + 1
                    continue
                elif depth == 0 and t == "for":
                    trait = _last_ident(self.t[seg_start:j])
                    seg_start = j + 1
                elif depth == 0 and t in ("{", ";", "where"):
                    break
                j += 1
            type_toks = self.t[seg_start:j]
            name = _last_ident(type_toks) or "?"
            name_i = seg_start if seg_start < end else i
            k = self.to_body(j)
            if k < end and self.t[k] == "{":
                body = self.close(k)
                idx = self.add(name, "impl", name_i, head, body, k, parent, True, [trait] if trait else [])
                self.scan(k + 1, body, idx, "impl")
                return body + 1
            return k + 1
        if kw == "mod" and i + 1 < end and IDENT.match(self.t[i + 1]):
            name_i = i + 1
            k = i + 2
            if k < end and self.t[k] == "{":
                body = self.close(k)
                idx = self.add(self.t[name_i], "module", name_i, head, body, k, parent, exported)
                self.mod_depth += 1
                self.scan(k + 1, body, idx, "mod")
                self.mod_depth -= 1
                return body + 1
            if k < end and self.t[k] == ";":
                self.add(self.t[name_i], "module", name_i, head, k, k, parent, exported)
                self.imports.append(Imp(raw=self.t[name_i], line=self.tk.line[name_i]))
                return k + 1
            return None
        if kw == "type" and i + 1 < end and IDENT.match(self.t[i + 1]):
            k = self.to_semicolon(i + 2)
            self.add(self.t[i + 1], "type", i + 1, head, k, k, parent, exported)
            return k + 1
        if kw in ("const", "static") and i + 1 < end:
            j = i + 1
            if kw == "static" and self.t[j] == "mut":
                j += 1
            if j + 1 < end and (IDENT.match(self.t[j]) or self.t[j] == "_") and self.t[j + 1] == ":":
                k = self.to_semicolon(j + 2)
                if self.t[j] != "_":
                    self.add(self.t[j], "const", j, head, k, j + 1, parent, exported)
                return k + 1
            return None
        if kw == "macro_rules" and i + 2 < end and self.t[i + 1] == "!" and IDENT.match(self.t[i + 2]):
            k = i + 3
            if k < end and self.t[k] in "({[":
                body = self.close(k)
                if body + 1 < end and self.t[body + 1] == ";":
                    body += 1
                self.add(self.t[i + 2], "macro", i + 2, head, body, k, parent, True)
                return body + 1
            return None
        if kw == "use":
            k = self.to_semicolon(i)
            for path in _use_paths(self.t[i + 1:k]):
                self.imports.append(Imp(raw=path, line=self.tk.line[i], level=self.mod_depth))
            return k + 1
        if IDENT.match(kw) and i + 1 < end and self.t[i + 1] == "!" and i + 2 < end and self.t[i + 2] in "({[" \
                and head == i:  # item-position macro invocation: its contents are not items we can see
            body = self.close(i + 2)
            return body + 2 if body + 1 < end and self.t[body + 1] == ";" else body + 1
        return None


def _last_ident(tokens) -> str:
    """Last identifier of a type path outside generic arguments: `&'a mut foo::Bar<T>` -> 'Bar'."""
    depth, last = 0, ""
    for t in tokens:
        if t == "<":
            depth += 1
        elif t == ">" and depth:
            depth -= 1
        elif depth == 0 and IDENT.match(t) and t not in ("mut", "dyn", "for", "impl", "const"):
            last = t
    return last


def _use_paths(tokens) -> list:
    """Expand a use tree: `a::b::{self, c::{d, e as f}, *}` -> ['a::b', 'a::b::c::d', 'a::b::c::e']."""
    out = []

    def walk(toks, prefix):
        path = list(prefix)
        i = 0
        while i < len(toks):
            t = toks[i]
            if t == "{":
                depth, j, items, cur = 1, i + 1, [], []
                while j < len(toks):
                    if toks[j] == "{":
                        depth += 1
                    elif toks[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    if depth == 1 and toks[j] == ",":
                        items.append(cur)
                        cur = []
                    else:
                        cur.append(toks[j])
                    j += 1
                items.append(cur)
                for it in items:
                    if it:
                        walk(it, path)
                return
            if t == "as":
                break
            if t == "*":
                out.append("::".join(path))
                return
            if t not in ("::", ","):
                if t == "self" and path:
                    break
                path.append(t)
            i += 1
        if path:
            out.append("::".join(path))

    walk(list(tokens), [])
    return [p for p in dict.fromkeys(out) if p and p != "::"]


def extract_rust(text: str) -> FileFacts:
    p = _P(text)
    p.scan(0, p.n, None, "file")
    syms = p.syms
    for s in syms:
        parts, q = [s.name], s.parent
        while q is not None:
            parts.append(syms[q].name)
            q = syms[q].parent
        s.qualname = ".".join(reversed(parts))
    facts = FileFacts(symbols=syms, imports=p.imports)
    for ln, line_text in enumerate(p.code.split("\n"), 1):
        for name in IDENT_RX.findall(line_text):
            if len(name) >= 3 and name not in RS_KEYWORDS:
                _add_ident(facts.idents, name, ln)
    return facts
