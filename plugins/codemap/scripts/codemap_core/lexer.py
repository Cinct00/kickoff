"""Language-aware masking and tokenizing for the structural C# and Rust parsers.

`mask_*` return (code, code_str): `code` has comments and string/char contents
blanked (newlines kept, so offsets and lines are preserved); `code_str` blanks
comments only (for signatures and import strings). `tokenize` turns `code`
into tokens with line numbers and bracket matches.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


def _blank(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


class _Buf:
    """Two output buffers built from slices of the source."""

    def __init__(self, text: str):
        self.text = text
        self.code: list = []
        self.cstr: list = []

    def keep(self, a: int, b: int) -> None:
        s = self.text[a:b]
        self.code.append(s)
        self.cstr.append(s)

    def comment(self, a: int, b: int) -> None:
        s = _blank(self.text[a:b])
        self.code.append(s)
        self.cstr.append(s)

    def string(self, a: int, b: int, open_len: int, close_len: int) -> None:
        s = self.text[a:b]
        inner = s[open_len:len(s) - close_len] if close_len else s[open_len:]
        self.code.append(s[:open_len] + _blank(inner) + (s[len(s) - close_len:] if close_len else ""))
        self.cstr.append(s)

    def result(self) -> tuple:
        return "".join(self.code), "".join(self.cstr)


# --------------------------------------------------------------------------- C#

_CS_DIRECTIVE = re.compile(r"^[ \t]*#[ \t]*(if|elif|else|endif|region|endregion|pragma|define|undef|line|nullable|error|warning)\b.*$", re.M)


def _cs_preprocess(text: str) -> str:
    """Keep the first branch of every #if/#elif/#else group; blank directives and the other branches."""
    lines = text.split("\n")
    out = []
    stack = []  # per #if: [taken_a_branch, currently_active]
    active = True
    for line in lines:
        m = re.match(r"^[ \t]*#[ \t]*(\w+)", line)
        d = m.group(1) if m else None
        if d == "if":
            stack.append([active, active])  # [parent_active, this branch active]
            active = active and True
            out.append(_blank(line))
            continue
        if d in ("elif", "else") and stack:
            parent_active, _ = stack[-1]
            stack[-1][1] = False
            active = False  # only the first branch is kept
            out.append(_blank(line))
            continue
        if d == "endif" and stack:
            parent_active, _ = stack.pop()
            active = parent_active
            out.append(_blank(line))
            continue
        if d in ("region", "endregion", "pragma", "define", "undef", "line", "nullable", "error", "warning"):
            out.append(_blank(line))
            continue
        out.append(line if active else _blank(line))
    return "\n".join(out)


_CS_NEXT = re.compile(r"//|/\*|[$@]*\"|'")


def mask_csharp(text: str) -> tuple:
    text = _cs_preprocess(text)
    buf = _Buf(text)
    i, n = 0, len(text)
    while i < n:
        m = _CS_NEXT.search(text, i)
        if not m:
            buf.keep(i, n)
            break
        j = m.start()
        buf.keep(i, j)
        tok = m.group(0)
        if tok == "//":
            e = text.find("\n", j)
            e = n if e == -1 else e
            buf.comment(j, e)
            i = e
        elif tok == "/*":
            e = text.find("*/", j + 2)
            e = n if e == -1 else e + 2
            buf.comment(j, e)
            i = e
        elif tok == "'":
            cm = re.compile(r"'(?:\\.[^'\n]{0,8}?|[^'\\\n])'").match(text, j)
            if cm:
                buf.string(j, cm.end(), 1, 1)
                i = cm.end()
            else:
                buf.keep(j, j + 1)
                i = j + 1
        else:
            e, open_len, close_len = _cs_string(text, j)
            buf.string(j, e, open_len, close_len)
            i = e
    return buf.result()


def _cs_string_end(text: str, j: int) -> int:
    return _cs_string(text, j)[0]


def _cs_string(text: str, j: int) -> tuple:
    """(end, open_len, close_len) of a C# string literal at j: $, @, raw \"\"\" and interpolation holes."""
    n = len(text)
    q = text.find('"', j)
    prefix = text[j:q]
    dollars = prefix.count("$")
    verbatim = "@" in prefix
    if text.startswith('"""', q) and not verbatim:  # raw literal (never @-prefixed): closes with as many quotes
        k = q
        while k < n and text[k] == '"':
            k += 1
        quotes = k - q
        e = text.find('"' * quotes, k)
        if e == -1:
            return n, k - j, 0
        return e + quotes, k - j, quotes
    end = _cs_simple_end(text, q + 1, dollars, verbatim)
    closed = end <= n and end > q + 1 and text[end - 1] == '"'
    return end, q + 1 - j, 1 if closed else 0


def _cs_simple_end(text: str, k: int, dollars: int, verbatim: bool) -> int:
    n = len(text)
    while k < n:
        c = text[k]
        if verbatim:
            if c == '"':
                if k + 1 < n and text[k + 1] == '"':
                    k += 2
                    continue
                return k + 1
        else:
            if c == "\\":
                k += 2
                continue
            if c == '"':
                return k + 1
            if c == "\n":
                return k
        if dollars and c == "{":
            if k + 1 < n and text[k + 1] == "{" and dollars == 1:
                k += 2
                continue
            k = _cs_skip_hole(text, k + 1)
            continue
        k += 1
    return n


def _cs_skip_hole(text: str, k: int) -> int:
    depth, n = 1, len(text)
    while k < n and depth:
        c = text[k]
        if c == '"' or (c in "$@" and k + 1 < n and text[k + 1] in '"$@'):
            k = _cs_string_end(text, k)
            continue
        if c == "'":
            m = re.compile(r"'(?:\\.[^'\n]{0,8}?|[^'\\\n])'").match(text, k)
            if m:
                k = m.end()
                continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        k += 1
    return k


# --------------------------------------------------------------------------- Rust

_RS_NEXT = re.compile(r"//|/\*|\b(?:br|cr|r)#*\"|\b[bc]\"|\"|\bb'|'")
_RS_CHAR = re.compile(r"b?'(?:\\(?:u\{[0-9a-fA-F_]{1,8}\}|x[0-9a-fA-F]{2}|.)|[^'\\\n])'")


def mask_rust(text: str) -> tuple:
    buf = _Buf(text)
    i, n = 0, len(text)
    while i < n:
        m = _RS_NEXT.search(text, i)
        if not m:
            buf.keep(i, n)
            break
        j = m.start()
        buf.keep(i, j)
        tok = m.group(0)
        if tok == "//":
            e = text.find("\n", j)
            e = n if e == -1 else e
            buf.comment(j, e)
            i = e
        elif tok == "/*":
            depth, k = 1, j + 2
            while k < n and depth:
                if text.startswith("/*", k):
                    depth += 1
                    k += 2
                elif text.startswith("*/", k):
                    depth -= 1
                    k += 2
                else:
                    k += 1
            buf.comment(j, k)
            i = k
        elif tok in ("'", "b'"):
            cm = _RS_CHAR.match(text, j)
            if cm:
                buf.string(j, cm.end(), len(tok), 1)
                i = cm.end()
            else:  # lifetime or label: keep as code
                buf.keep(j, j + len(tok))
                i = j + len(tok)
        elif re.match(r'^(?:br|cr|r)#*"$', tok):  # raw string: closes with '"' plus the same number of '#'
            close = '"' + "#" * tok.count("#")
            e = text.find(close, j + len(tok))
            if e == -1:
                buf.string(j, n, len(tok), 0)
                i = n
            else:
                buf.string(j, e + len(close), len(tok), len(close))
                i = e + len(close)
        else:
            i = _rs_plain_string(buf, text, j, len(tok))
    return buf.result()


def _rs_plain_string(buf, text, j, open_len) -> int:
    n = len(text)
    k = j + open_len
    while k < n:
        if text[k] == "\\":
            k += 2
            continue
        if text[k] == '"':
            buf.string(j, k + 1, open_len, 1)
            return k + 1
        k += 1
    buf.string(j, n, open_len, 0)
    return n


# --------------------------------------------------------------------------- tokens

_TOKEN = re.compile(r"r#[A-Za-z_]\w*|[A-Za-z_]\w*|'[A-Za-z_]\w*|::|->|=>|\?\?=?|[{}()\[\]<>;,=:.!#&*?|+\-/%^~@$\"']")


@dataclass
class Tokens:
    text: list   # token strings
    start: list  # offsets
    line: list   # 1-based lines
    match: dict  # index of an opening bracket -> index of its closing bracket (and back)

    def __len__(self):
        return len(self.text)


def tokenize(code: str) -> Tokens:
    texts, starts, lines = [], [], []
    line, last = 1, 0
    for m in _TOKEN.finditer(code):
        s = m.start()
        line += code.count("\n", last, s)
        last = s
        texts.append(m.group(0))
        starts.append(s)
        lines.append(line)
    match, stack = {}, []
    pairs = {"}": "{", ")": "(", "]": "["}
    for i, t in enumerate(texts):
        if t in "{([":
            stack.append(i)
        elif t in pairs:
            # tolerate mismatches: pop until the right opener (or give up)
            k = len(stack) - 1
            while k >= 0 and texts[stack[k]] != pairs[t]:
                k -= 1
            if k >= 0:
                o = stack[k]
                del stack[k:]
                match[o] = i
                match[i] = o
    return Tokens(texts, starts, lines, match)
