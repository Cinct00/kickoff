"""Structural C# extractor: scope-aware declarations, imports and identifiers (stdlib only)."""
from __future__ import annotations

import re

from .extract import IDENT_RX, KEYWORDS, FileFacts, Imp, Sym, _add_ident, _clip, _doc_above
from .lexer import mask_csharp, tokenize

MODIFIERS = {"public", "private", "protected", "internal", "static", "abstract", "sealed", "partial", "virtual",
             "override", "readonly", "new", "extern", "unsafe", "async", "const", "volatile", "required", "file",
             "fixed", "implicit", "explicit", "ref", "scoped"}
TYPE_KW = {"class", "struct", "interface", "enum", "record"}
CS_KEYWORDS = KEYWORDS | {"get", "set", "init", "add", "remove", "value", "var", "dynamic", "nameof", "yield", "where",
                          "decimal", "sbyte", "ushort", "ulong", "uint", "nint", "nuint", "checked", "unchecked",
                          "lock", "foreach", "goto", "operator", "event", "delegate", "params", "base", "this", "is"}
IMPORT_RX = re.compile(r"^\s*(global\s+)?using\s+(?:static\s+)?(?:\w+\s*=\s*)?([\w.]+)\s*;", re.M)


class _P:
    def __init__(self, text: str):
        self.code, self.cstr = mask_csharp(text)
        self.lines = text.split("\n")
        self.tk = tokenize(self.code)
        self.t = self.tk.text
        self.n = len(self.t)
        self.syms: list = []

    # ------------------------------------------------------------------ helpers
    def close(self, i):
        return self.tk.match.get(i, self.n - 1)

    def skip_angles(self, i):
        """i at '<': return index after the matching '>' (generic argument lists)."""
        depth = 0
        while i < self.n:
            t = self.t[i]
            if t == "<":
                depth += 1
            elif t == ">":
                depth -= 1
                if depth == 0:
                    return i + 1
            elif t in "({[":
                i = self.close(i)
            elif t in (";", "{", "}"):
                return i
            i += 1
        return i

    def skip_to_semicolon(self, i):
        """Skip an expression/initializer to the ';' that ends it (brackets balanced)."""
        while i < self.n:
            t = self.t[i]
            if t in "({[":
                i = self.close(i) + 1
                continue
            if t == ";":
                return i
            if t == "}":  # unbalanced: stop before the enclosing '}'
                return i - 1
            i += 1
        return self.n - 1

    def sig(self, a, b):
        start = self.tk.start[a]
        end = self.tk.start[b] if b < self.n else len(self.cstr)
        return _clip(self.cstr[start:end])

    def add(self, name, kind, name_i, start_i, end_i, sig_end_i, parent, exported, bases=()):
        line = self.tk.line[name_i]
        sym = Sym(name=name, kind=kind, line=line, end_line=max(line, self.tk.line[min(end_i, self.n - 1)]),
                  signature=self.sig(start_i, sig_end_i), doc=_doc_above(self.lines, self.tk.line[start_i]),
                  parent=parent, exported=exported, bases=list(bases))
        self.syms.append(sym)
        return len(self.syms) - 1

    # ------------------------------------------------------------------ declarations
    def members(self, i, end, parent, scope):
        """scope: 'unit' | 'namespace' | 'type' | 'interface'."""
        while i < end:
            t = self.t[i]
            if t in (";", "}"):
                i += 1
                continue
            if t == "[":  # attribute
                i = self.close(i) + 1
                continue
            start = i
            mods = []
            while i < end and self.t[i] in MODIFIERS:
                mods.append(self.t[i])
                i += 1
            if i >= end:
                break
            t = self.t[i]
            if t == "namespace":
                i = self.namespace(start, i, end, parent)
                continue
            if t in ("using", "extern") or (t == "global" and i + 1 < end and self.t[i + 1] == "using"):
                i = self.skip_to_semicolon(i) + 1
                continue
            if t in TYPE_KW and i + 1 < end and (re.match(r"[A-Za-z_]", self.t[i + 1]) and
                                                 (t != "record" or self.t[i + 1] not in ("=", "(", ";", ",", ")"))):
                i = self.type_decl(start, i, end, parent, mods)
                continue
            if t == "delegate" and i + 1 < end and self.t[i + 1] != "(" and self.t[i + 1] != "{":
                i = self.delegate(start, i, end, parent, mods)
                continue
            if scope in ("type", "interface"):
                i = self.member(start, i, end, parent, mods, scope)
                continue
            # compilation unit / namespace level: top-level statements, local functions, stray tokens
            if t == "{":
                i = self.close(i) + 1
            else:
                k = i
                while k < end and self.t[k] not in (";", "{"):
                    k = self.close(k) + 1 if self.t[k] in "([" else k + 1
                i = (self.close(k) + 1) if k < end and self.t[k] == "{" else k + 1
        return i

    def namespace(self, start, i, end, parent):
        j = i + 1
        parts = []
        while j < end and (re.match(r"[A-Za-z_]", self.t[j]) or self.t[j] == "."):
            parts.append(self.t[j])
            j += 1
        name = "".join(parts)
        if not name:
            return j
        if j < end and self.t[j] == "{":
            body_end = self.close(j)
            idx = self.add(name, "namespace", i + 1, start, body_end, j, parent, True)
            self.members(j + 1, body_end, idx, "namespace")
            return body_end + 1
        # file-scoped namespace: everything after it, to the end of the file
        idx = self.add(name, "namespace", i + 1, start, self.n - 1, j, parent, True)
        self.syms[idx].end_line = self.tk.line[self.n - 1] if self.n else self.syms[idx].line
        self.members(j + 1, end, idx, "namespace")
        return end

    def type_decl(self, start, i, end, parent, mods):
        kw = self.t[i]
        j = i + 1
        if kw == "record" and self.t[j] in ("class", "struct"):
            j += 1
        name_i = j
        name = self.t[j]
        j += 1
        if j < end and self.t[j] == "<":
            j = self.skip_angles(j)
        if j < end and self.t[j] == "(":  # primary constructor
            j = self.close(j) + 1
        bases = []
        if j < end and self.t[j] == ":":
            j += 1
            cur = []
            while j < end and self.t[j] not in ("{", ";", "where"):
                tj = self.t[j]
                if tj == "<":
                    j = self.skip_angles(j)
                    continue
                if tj == "(":
                    j = self.close(j) + 1
                    continue
                if tj == ",":
                    if cur:
                        bases.append(cur[-1])
                    cur = []
                elif re.match(r"[A-Za-z_]", tj):
                    cur.append(tj)
                j += 1
            if cur:
                bases.append(cur[-1])
        while j < end and self.t[j] not in ("{", ";"):
            j = self.close(j) + 1 if self.t[j] in "([" else j + 1
        kind = {"class": "class", "struct": "struct", "interface": "interface", "enum": "enum", "record": "record"}[kw]
        exported = "private" not in mods
        if j < end and self.t[j] == "{":
            body_end = self.close(j)
            k = body_end + 1 if body_end + 1 < end and self.t[body_end + 1] == ";" else body_end
            idx = self.add(name, kind, name_i, start, k, j, parent, exported, bases)
            if kind != "enum":
                self.members(j + 1, body_end, idx, "interface" if kind == "interface" else "type")
            return k + 1
        idx = self.add(name, kind, name_i, start, j, j, parent, exported, bases)  # `record R(int X);`
        return j + 1

    def delegate(self, start, i, end, parent, mods):
        j = i + 1
        name_i = None
        while j < end and self.t[j] != ";":
            if self.t[j] == "(" and name_i is None:
                k = j - 1
                if self.t[k] == ">":
                    depth = 0
                    while k > i:
                        if self.t[k] == ">":
                            depth += 1
                        elif self.t[k] == "<":
                            depth -= 1
                            if depth == 0:
                                k -= 1
                                break
                        k -= 1
                name_i = k
                j = self.close(j)
            j += 1
        if name_i is None:
            return j + 1
        self.add(self.t[name_i], "delegate", name_i, start, j, j, parent, "private" not in mods)
        return j + 1

    def member(self, start, i, end, parent, mods, scope):
        """A member of a class/struct/interface/record: method, ctor, property, indexer, event, field, operator."""
        j = i
        angle = 0
        first_group = None  # index of the first top-level '(' preceded by a name
        has_this_indexer = None
        has_operator = False
        is_event = False
        where_at = None
        while j < end:
            tj = self.t[j]
            if tj == "<":
                angle += 1
            elif tj == ">" and angle:
                angle -= 1
            elif tj == "(":
                prev = self.t[j - 1] if j > i else ""
                if angle == 0 and first_group is None and where_at is None and (
                        re.match(r"[A-Za-z_]", prev) and prev not in ("where", "new") or prev == ">" or has_operator):
                    first_group = j
                j = self.close(j) + 1
                continue
            elif tj == "[":
                if angle == 0 and j > i and self.t[j - 1] == "this":
                    has_this_indexer = j
                j = self.close(j) + 1
                continue
            elif angle == 0 and tj in ("{", ";", "=>") or (angle == 0 and tj in ("=", ",") and first_group is None):
                break  # after a parameter list, ',' and '=' belong to a where-clause or default values
            elif tj == "operator":
                has_operator = True
            elif tj == "event":
                is_event = True
            elif tj == "where" and angle == 0 and first_group is not None:
                where_at = j
            elif tj == ":" and angle == 0 and first_group is not None:
                # constructor initializer `: base(...)` / `: this(...)`
                k = j + 1
                if k < end and self.t[k] in ("base", "this") and k + 1 < end and self.t[k + 1] == "(":
                    j = self.close(k + 1) + 1
                    continue
            elif tj == "}":
                break
            j += 1
        if j >= end:
            return end
        term = self.t[j]
        exported = bool({"public", "protected", "internal"} & set(mods)) or scope == "interface"

        if has_operator:
            name_i = next((k for k in range(i, j) if self.t[k] == "operator"), i)
            body_end = self.body_end(j)
            self.add("operator " + "".join(self.t[name_i + 1:(first_group or j)]).strip(), "operator", name_i, start,
                     body_end, j, parent, exported)
            return body_end + 1
        if has_this_indexer is not None:
            body_end = self.body_end(j)
            self.add("this", "indexer", has_this_indexer - 1, start, body_end, j, parent, exported)
            return body_end + 1
        if first_group is not None:
            k = first_group - 1
            if self.t[k] == ">":  # generic method: walk back over <...>
                depth = 0
                while k > i:
                    if self.t[k] == ">":
                        depth += 1
                    elif self.t[k] == "<":
                        depth -= 1
                        if depth == 0:
                            k -= 1
                            break
                    k -= 1
            name = self.t[k]
            if not re.match(r"[A-Za-z_]", name) or name in ("if", "while", "for", "switch", "return", "new"):
                return self.skip_statement(j, end)
            body_end = self.body_end(j)
            self.add(name, "method", k, start, body_end, j, parent, exported)
            return body_end + 1
        # property / event (accessor form) / field / const / event field
        if term in ("{", "=>"):
            name_i = j - 1
            while name_i > i and not re.match(r"[A-Za-z_]", self.t[name_i]):
                name_i -= 1
            body_end = self.body_end(j)
            if term == "{" and body_end + 1 < end and self.t[body_end + 1] == "=":  # `{ get; } = init;`
                body_end = self.skip_to_semicolon(body_end + 1)
            self.add(self.t[name_i], "event" if is_event else "property", name_i, start, body_end, j, parent, exported)
            return body_end + 1
        # field-like: one or more declarators, separated by ',' at depth 0
        kind = "const" if "const" in mods else "field"
        names = []
        k = j
        name_i = j - 1
        while True:
            if re.match(r"[A-Za-z_]", self.t[name_i]):
                names.append(name_i)
            if self.t[k] == "=":
                k = self._skip_init(k + 1, end)
            if k >= end or self.t[k] == ";":
                break
            if self.t[k] == ",":
                name_i = k + 1
                k = k + 2
                while k < end and self.t[k] not in (",", ";", "="):
                    k = self.close(k) + 1 if self.t[k] in "([" else k + 1
                continue
            break
        for ni in names:
            self.add(self.t[ni], kind, ni, start, k, j, parent, exported)
        return k + 1

    def _skip_init(self, k, end):
        while k < end:
            t = self.t[k]
            if t in "({[":
                k = self.close(k) + 1
                continue
            if t == "<":  # generic arguments (`new Dictionary<string, object>()`), not a comparison
                g = self.skip_angles(k)
                if g < end and self.t[g - 1] == ">" and self.t[g] in ("(", "[", "{", ";", ",", ")", ".", ">"):
                    k = g
                    continue
            if t in (",", ";", "}"):
                return k
            k += 1
        return k

    def body_end(self, j):
        t = self.t[j]
        if t == "{":
            return self.close(j)
        if t in ("=>", "="):
            return self.skip_to_semicolon(j + 1)
        return j  # ';'

    def skip_statement(self, j, end):
        return self.skip_to_semicolon(j) + 1 if self.t[j] != "{" else self.close(j) + 1


def extract_csharp(text: str) -> FileFacts:
    p = _P(text)
    p.members(0, p.n, None, "unit")
    facts = FileFacts()
    syms = p.syms
    for s in syms:  # qualnames
        parts, q = [s.name], s.parent
        while q is not None:
            parts.append(syms[q].name)
            q = syms[q].parent
        s.qualname = ".".join(reversed(parts))
    facts.symbols = syms
    starts = [0] + [m.end() for m in re.finditer("\n", p.cstr)]
    import bisect
    for m in IMPORT_RX.finditer(p.cstr):
        line = bisect.bisect_right(starts, m.start())
        # `global using` applies to the whole project; the store widens its scope accordingly.
        facts.imports.append(Imp(raw=m.group(2), line=line, names=["global"] if m.group(1) else []))
    ns = next((s for s in syms if s.kind == "namespace"), None)
    facts.package = ns.name if ns else ""
    for ln, line_text in enumerate(p.code.split("\n"), 1):
        for name in IDENT_RX.findall(line_text):
            if len(name) >= 3 and name not in CS_KEYWORDS:
                _add_ident(facts.idents, name, ln)
    return facts
