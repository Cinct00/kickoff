"""Extract definitions, imports and identifier references from source files.

Python uses the stdlib `ast` module (exact). Other languages use a lexer that
masks comments and strings, then per-language definition/import patterns, with
brace matching (or indentation) for symbol extents. Identifier references are
collected language-agnostically from the masked text, as in tags-based repo maps.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

MAX_SIG = 160
MAX_LINES_PER_IDENT = 20


@dataclass
class Sym:
    name: str
    kind: str
    line: int
    end_line: int
    signature: str
    doc: str = ""
    parent: int | None = None  # index into FileFacts.symbols
    exported: bool = True
    bases: list = field(default_factory=list)
    qualname: str = ""


@dataclass
class Imp:
    raw: str
    line: int
    names: list = field(default_factory=list)  # imported names (python from-imports, JS named imports)
    level: int = 0  # python relative-import level


@dataclass
class FileFacts:
    symbols: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    idents: dict = field(default_factory=dict)  # name -> [count, [lines]]
    package: str = ""  # java/kotlin/scala package, c# namespace, go package


def _add_ident(idents: dict, name: str, line: int) -> None:
    entry = idents.get(name)
    if entry is None:
        idents[name] = [1, [line]]
    else:
        entry[0] += 1
        if len(entry[1]) < MAX_LINES_PER_IDENT and entry[1][-1] != line:
            entry[1].append(line)


def _clip(sig: str) -> str:
    sig = re.sub(r"\s+", " ", sig).strip()
    return sig if len(sig) <= MAX_SIG else sig[: MAX_SIG - 1] + "…"


def _first_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    m = re.match(r"(.{1,100}?[.!?])(\s|$)", text)
    out = m.group(1) if m else text[:100]
    return out


def _qualify(syms: list, sep: str = ".") -> None:
    for s in syms:
        parts, p = [s.name], s.parent
        while p is not None:
            parts.append(syms[p].name)
            p = syms[p].parent
        s.qualname = sep.join(reversed(parts))


# --------------------------------------------------------------------------- python

class _PyVisitor(ast.NodeVisitor):
    def __init__(self, facts: FileFacts):
        self.f = facts
        self.stack: list[int] = []

    def _sym(self, node, name, kind, sig, doc="", bases=()):
        parent = self.stack[-1] if self.stack else None
        self.f.symbols.append(Sym(
            name=name, kind=kind, line=node.lineno, end_line=getattr(node, "end_lineno", node.lineno) or node.lineno,
            signature=_clip(sig), doc=_first_sentence(doc), parent=parent, exported=not name.startswith("_"),
            bases=list(bases),
        ))
        return len(self.f.symbols) - 1

    @staticmethod
    def _decorators(node) -> str:
        decs = []
        for d in node.decorator_list:
            try:
                txt = "@" + ast.unparse(d)
            except Exception:
                continue
            if len(txt) <= 60:
                decs.append(txt)
        return " ".join(decs) + " " if decs else ""

    def visit_ClassDef(self, node):
        bases = []
        for b in node.bases:
            try:
                bases.append(ast.unparse(b))
            except Exception:
                pass
        sig = f"{self._decorators(node)}class {node.name}" + (f"({', '.join(bases)})" if bases else "")
        idx = self._sym(node, node.name, "class", sig, ast.get_docstring(node) or "", [b.split("[")[0].split(".")[-1] for b in bases])
        self.stack.append(idx)
        self.generic_visit(node)
        self.stack.pop()

    def _func(self, node, is_async):
        in_class = bool(self.stack) and self.f.symbols[self.stack[-1]].kind == "class"
        try:
            args = ast.unparse(node.args)
        except Exception:
            args = "…"
        ret = ""
        if node.returns is not None:
            try:
                ret = " -> " + ast.unparse(node.returns)
            except Exception:
                pass
        sig = f"{self._decorators(node)}{'async ' if is_async else ''}def {node.name}({args}){ret}"
        idx = self._sym(node, node.name, "method" if in_class else "function", sig, ast.get_docstring(node) or "")
        self.stack.append(idx)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node):
        self._func(node, False)

    def visit_AsyncFunctionDef(self, node):
        self._func(node, True)

    def _assign(self, node, targets, value):
        if self.stack:  # only module-level and class-level names
            if self.f.symbols[self.stack[-1]].kind != "class":
                self.generic_visit(node)
                return
        for t in targets:
            if isinstance(t, ast.Name):
                name = t.id
                kind = "const" if name.isupper() and len(name) > 1 else ("field" if self.stack else "var")
                try:
                    val = ast.unparse(value) if value is not None else ""
                except Exception:
                    val = ""
                sig = f"{name} = {val[:50]}{'…' if len(val) > 50 else ''}" if val else name
                self._sym(node, name, kind, sig)
        self.generic_visit(node)

    def visit_Assign(self, node):
        self._assign(node, node.targets, node.value)

    def visit_AnnAssign(self, node):
        self._assign(node, [node.target], node.value)

    def visit_Import(self, node):
        for a in node.names:
            self.f.imports.append(Imp(raw=a.name, line=node.lineno))
            _add_ident(self.f.idents, (a.asname or a.name).split(".")[0], node.lineno)

    def visit_ImportFrom(self, node):
        names = [a.name for a in node.names]
        self.f.imports.append(Imp(raw=node.module or "", line=node.lineno, names=names, level=node.level or 0))
        for a in node.names:
            _add_ident(self.f.idents, a.asname or a.name, node.lineno)

    def visit_Name(self, node):
        _add_ident(self.f.idents, node.id, node.lineno)

    def visit_Attribute(self, node):
        _add_ident(self.f.idents, node.attr, node.lineno)
        self.generic_visit(node)


def extract_python(text: str) -> FileFacts:
    facts = FileFacts()
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return extract_generic(text, "python_fallback")
    _PyVisitor(facts).visit(tree)
    _qualify(facts.symbols)
    return facts


# --------------------------------------------------------------------------- masking

_MASKERS: dict = {}


def _masker(lang: str):
    if lang in _MASKERS:
        return _MASKERS[lang]
    dq = r'"(?:\\.|[^"\\\n])*"'
    sq = r"'(?:\\.|[^'\\\n])*'"
    if lang in ("javascript", "typescript"):
        pat = r"//[^\n]*|/\*.*?\*/|" + dq + "|" + sq + r"|`(?:\\.|[^`\\])*`"
    elif lang == "go":
        pat = r"//[^\n]*|/\*.*?\*/|" + dq + r"|`[^`]*`|'(?:\\.|[^'\\\n])+'"
    elif lang == "rust":
        pat = r"//[^\n]*|/\*.*?\*/|r#*\"(?:.|\n)*?\"#*|" + dq + r"|'(?:\\.|[^'\\\n])'"
    elif lang == "csharp":
        pat = r"//[^\n]*|/\*.*?\*/|@\"(?:\"\"|[^\"])*\"|\"\"\"(?:.|\n)*?\"\"\"|" + dq + r"|'(?:\\.|[^'\\\n])+'"
    elif lang in ("java", "kotlin", "scala", "swift"):
        pat = r"//[^\n]*|/\*.*?\*/|\"\"\"(?:.|\n)*?\"\"\"|" + dq + r"|'(?:\\.|[^'\\\n])+'"
    elif lang in ("c", "cpp"):
        pat = r"//[^\n]*|/\*.*?\*/|" + dq + r"|'(?:\\.|[^'\\\n])+'"
    elif lang == "php":
        pat = r"//[^\n]*|#(?!\[)[^\n]*|/\*.*?\*/|" + dq + "|" + sq
    elif lang in ("ruby", "python_fallback"):
        pat = r"#[^\n]*|\"\"\"(?:.|\n)*?\"\"\"|'''(?:.|\n)*?'''|" + dq + "|" + sq
    else:
        pat = dq + "|" + sq
    rx = re.compile(pat, re.S)
    _MASKERS[lang] = rx
    return rx


def _blank(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


def mask(text: str, lang: str) -> tuple[str, str]:
    """Return (code_only, code_and_strings): comments+strings blanked, and comments only blanked."""
    rx = _masker(lang)
    full, partial = [], []
    last = 0
    for m in rx.finditer(text):
        s = m.group(0)
        full.append(text[last:m.start()])
        partial.append(text[last:m.start()])
        is_comment = s.startswith(("//", "/*", "#"))
        if is_comment:
            b = _blank(s)
            full.append(b)
            partial.append(b)
        else:
            q = s[0] if s[0] in "\"'`" else s[: s.find('"') + 1] if '"' in s else s[0]
            full.append(s[: len(q)] + _blank(s[len(q):-1]) + s[-1:] if len(s) >= 2 else s)
            partial.append(s)
        last = m.end()
    full.append(text[last:])
    partial.append(text[last:])
    return "".join(full), "".join(partial)


def _brace_ends(masked: str) -> dict:
    """Map offset of each '{' to offset of its matching '}'."""
    ends, stack = {}, []
    for m in re.finditer(r"[{}]", masked):
        i = m.start()
        if masked[i] == "{":
            stack.append(i)
        elif stack:
            ends[stack.pop()] = i
    return ends


# --------------------------------------------------------------------------- language specs

KEYWORDS = set("""
if else elif for while do switch case default break continue return function func fn def class interface struct enum
trait impl type var let const val new delete this self super null nil none true false undefined void import export from
package module namespace using use require include public private protected internal static final abstract override
virtual async await yield try catch except finally throw throws raise with as in is not and or of typeof instanceof
extends implements sizeof lambda pass global nonlocal assert match where when get set readonly sealed partial unsafe
mut pub crate mod ref out params object extern inline goto unless until then begin end elsif rescue ensure module
int long short float double char bool boolean byte string str uint usize isize i32 i64 u32 u64 f32 f64 any unknown never
println printf print echo err error ok Self Some None Ok Err String Vec Option Result Box self_ cls args kwargs
""".split())

_MODS = (r"(?:(?:public|private|protected|internal|static|final|abstract|sealed|partial|virtual|override|async|"
         r"synchronized|native|extern|unsafe|readonly|new|default|open|data|inner|inline|suspend|operator|infix|"
         r"tailrec|external|lateinit|const|implicit|lazy|case|transient|volatile|strictfp|required|convenience|"
         r"mutating|nonmutating|fileprivate|dynamic|@\w+(?:\([^)]*\))?)\s+)*")

CONTAINER_KINDS = {"class", "interface", "struct", "enum", "trait", "impl", "object", "record", "module",
                   "namespace", "protocol", "extension", "actor", "union"}

# (regex, kind, name_group, flags) — applied to masked text with re.M
SPECS: dict = {
    "javascript": [
        (r"^[ \t]*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)", "class", 1),
        (r"^[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)", "function", 1),
        (r"^[ \t]*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=\s*(?:async\s+)?"
         r"(?:function\b|\([^)]*\)\s*(?::[^=\n]+)?=>|[A-Za-z_$][\w$]*\s*=>)", "function", 1),
        (r"^export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)", "const", 1),
        (r"^[ \t]+(?:(?:public|private|protected|static|async|readonly|override|abstract|get|set|declare)\s+)*\*?"
         r"(#?[A-Za-z_$][\w$]*)\s*(?:<[^>\n]*>)?\s*\([^;{}]*\)\s*(?::\s*[^{;=]+)?\{", "method?", 1),
        (r"^[ \t]+(?:(?:public|private|protected|static|readonly|override)\s+)*(#?[A-Za-z_$][\w$]*)\s*[?!]?\s*"
         r"(?::[^=\n]+)?=\s*(?:async\s+)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=>", "method?", 1),
    ],
    "typescript": [
        (r"^[ \t]*(?:export\s+)?(?:declare\s+)?interface\s+([A-Za-z_$][\w$]*)", "interface", 1),
        (r"^[ \t]*(?:export\s+)?(?:declare\s+)?type\s+([A-Za-z_$][\w$]*)\s*(?:<[^=\n]*>)?\s*=", "type", 1),
        (r"^[ \t]*(?:export\s+)?(?:declare\s+)?(?:const\s+)?enum\s+([A-Za-z_$][\w$]*)", "enum", 1),
        (r"^[ \t]*(?:export\s+)?(?:declare\s+)?namespace\s+([A-Za-z_$][\w$.]*)", "namespace", 1),
    ],
    "go": [
        (r"^func\s+\(\s*\w*\s*\*?\s*(\w+)(?:\[[^\]]*\])?\s*\)\s*(\w+)", "method:go", 2),
        (r"^func\s+(\w+)", "function", 1),
        (r"^type\s+(\w+)(?:\[[^\]]*\])?\s+struct\b", "struct", 1),
        (r"^type\s+(\w+)(?:\[[^\]]*\])?\s+interface\b", "interface", 1),
        (r"^type\s+(\w+)\s+(?!struct\b|interface\b)", "type", 1),
        (r"^\t?(?:const|var)\s+([A-Z]\w*)\s", "const", 1),
    ],
    "java": [
        (r"^[ \t]*" + _MODS + r"(class|interface|enum|record|@interface)\s+(\w+)", "decl", 2),
        (r"^[ \t]+" + _MODS + r"(?:<[^>\n]+>\s+)?(?:[\w<>\[\],.?]+(?:\s*<[^>\n]*>)?\s+)?(\w+)\s*\([^;{}]*\)\s*"
         r"(?:throws\s+[\w.,\s]+)?\{", "method?", 1),
    ],
    "kotlin": [
        (r"^[ \t]*" + _MODS + r"(class|interface|object|enum\s+class|annotation\s+class|sealed\s+class|data\s+class)\s+(\w+)", "decl", 2),
        (r"^[ \t]*" + _MODS + r"fun\s+(?:<[^>\n]+>\s+)?(?:[\w.<>?]+\.)?(\w+)\s*\(", "function", 1),
        (r"^[ \t]*" + _MODS + r"typealias\s+(\w+)", "type", 1),
    ],
    "scala": [
        (r"^[ \t]*" + _MODS + r"(class|trait|object|enum)\s+(\w+)", "decl", 2),
        (r"^[ \t]*" + _MODS + r"def\s+(\w+)", "function", 1),
    ],
    "csharp": [
        (r"^[ \t]*" + _MODS + r"(class|interface|enum|struct|record(?:\s+struct|\s+class)?)\s+(\w+)", "decl", 2),
        (r"^[ \t]*namespace\s+([\w.]+)", "namespace", 1),
        (r"^[ \t]+" + _MODS + r"(?:[\w<>\[\],.?]+(?:\s*<[^>\n]*>)?\s+)?(\w+)\s*(?:<[^>\n]+>)?\s*\([^;{}]*\)\s*"
         r"(?:where[^{;\n]+)?(?:\{|=>)", "method?", 1),
    ],
    "rust": [
        (r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?(?:default\s+)?(?:const\s+)?(?:async\s+)?(?:unsafe\s+)?"
         r"(?:extern\s+\"[^\"]*\"\s+)?fn\s+(\w+)", "function", 1),
        (r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?(struct|enum|trait|union)\s+(\w+)", "decl", 2),
        (r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?type\s+(\w+)", "type", 1),
        (r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*\{", "module", 1),
        (r"^[ \t]*(?:unsafe\s+)?impl(?:\s*<[^{]*?>)?\s+(?:[\w:<>,\s&']+?\s+for\s+)?([\w:]+)", "impl", 1),
        (r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?(?:const|static)\s+([A-Z_][A-Z0-9_]*)\s*:", "const", 1),
        (r"^[ \t]*macro_rules!\s*(\w+)", "macro", 1),
    ],
    "c": [
        (r"^[ \t]*(?:typedef\s+)?(struct|union|enum)\s+(\w+)\s*\{", "decl", 2),
        (r"^(?!\s)(?:[\w*&\s]+?[\s*&])(\w+)\s*\([^;{}]*\)\s*\{", "function", 1),
        (r"^[ \t]*#\s*define\s+(\w+)", "macro", 1),
    ],
    "cpp": [
        (r"^[ \t]*(?:template\s*<[^>]*>\s*)?(class|struct|union|enum(?:\s+class)?)\s+(?:\w+\s+)*?(\w+)\s*(?:final\s*)?(?::[^{;]*)?\{", "decl", 2),
        (r"^[ \t]*namespace\s+([\w:]+)\s*\{", "namespace", 1),
        (r"^[ \t]*(?:template\s*<[^>]*>\s*)?(?:[\w:*&<>,\s~]+?[\s*&])?((?:\w+::)*~?\w+)\s*\([^;{}]*\)\s*"
         r"(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?(?:->\s*[\w:<>*&]+\s*)?\{", "function", 1),
        (r"^[ \t]*#\s*define\s+(\w+)", "macro", 1),
    ],
    "php": [
        (r"^[ \t]*(?:(?:abstract|final|readonly)\s+)*(class|interface|trait|enum)\s+(\w+)", "decl", 2),
        (r"^[ \t]*(?:(?:public|private|protected|static|abstract|final)\s+)*function\s+&?(\w+)", "function", 1),
        (r"^[ \t]*namespace\s+([\w\\]+)", "namespace", 1),
    ],
    "ruby": [
        (r"^[ \t]*(class|module)\s+([A-Z][\w:]*)", "decl", 2),
        (r"^[ \t]*def\s+(?:self\.)?([\w]+[?!=]?)", "function", 1),
    ],
    "swift": [
        (r"^[ \t]*" + _MODS + r"(class|struct|enum|protocol|extension|actor)\s+(\w+)", "decl", 2),
        (r"^[ \t]*" + _MODS + r"func\s+(\w+)", "function", 1),
        (r"^[ \t]*" + _MODS + r"typealias\s+(\w+)", "type", 1),
    ],
    "python_fallback": [
        (r"^[ \t]*class\s+(\w+)", "class", 1),
        (r"^[ \t]*(?:async\s+)?def\s+(\w+)", "function", 1),
    ],
}
SPECS["typescript"] = SPECS["typescript"] + SPECS["javascript"]
INDENT_LANGS = {"ruby", "python_fallback"}

IMPORT_SPECS: dict = {
    "javascript": [
        r"^\s*import\s+(?:type\s+)?(?:[\w*{}\s,$]+\s+from\s+)?['\"]([^'\"]+)['\"]",
        r"^\s*export\s+(?:type\s+)?(?:\*|\{[^}]*\})(?:\s+as\s+\w+)?\s+from\s+['\"]([^'\"]+)['\"]",
        r"\brequire\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"\bimport\(\s*['\"]([^'\"]+)['\"]\s*\)",
    ],
    "go": [r"^\s*import\s+(?:\w+\s+|\.\s+|_\s+)?\"([^\"]+)\"", r"^\s+(?:\w+\s+|\.\s+|_\s+)?\"([^\"]+)\"\s*$"],
    "java": [r"^\s*import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;"],
    "kotlin": [r"^\s*import\s+([\w.]+(?:\.\*)?)"],
    "scala": [r"^\s*import\s+([\w.]+)"],
    "csharp": [r"^\s*(?:global\s+)?using\s+(?:static\s+)?(?:\w+\s*=\s*)?([\w.]+)\s*;"],
    "rust": [r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+([\w:]+)", r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;"],
    "c": [r"^\s*#\s*include\s*[\"<]([^\">]+)[\">]"],
    "php": [r"^\s*use\s+(?:function\s+|const\s+)?([\w\\]+)", r"\b(?:require|include)(?:_once)?\s*\(?\s*['\"]([^'\"]+)['\"]"],
    "ruby": [r"^\s*require(?:_relative)?\s*\(?\s*['\"]([^'\"]+)['\"]"],
    "swift": [r"^\s*(?:@testable\s+)?import\s+(\w+)"],
}
IMPORT_SPECS["typescript"] = IMPORT_SPECS["javascript"]
IMPORT_SPECS["cpp"] = IMPORT_SPECS["c"]

PACKAGE_RX = {
    "java": re.compile(r"^\s*package\s+([\w.]+)", re.M),
    "kotlin": re.compile(r"^\s*package\s+([\w.]+)", re.M),
    "scala": re.compile(r"^\s*package\s+([\w.]+)", re.M),
    "go": re.compile(r"^\s*package\s+(\w+)", re.M),
    "csharp": re.compile(r"^\s*namespace\s+([\w.]+)", re.M),
    "php": re.compile(r"^\s*namespace\s+([\w\\]+)", re.M),
}

_COMPILED: dict = {}
IDENT_RX = re.compile(r"[A-Za-z_$][\w$]*")
CONTROL = {"if", "for", "while", "switch", "catch", "foreach", "using", "lock", "fixed", "return", "new", "else",
           "do", "try", "synchronized", "await", "throw", "function", "typeof", "sizeof", "when", "elif", "with"}


def _compiled(lang: str):
    if lang not in _COMPILED:
        _COMPILED[lang] = (
            [(re.compile(p, re.M), k, g) for p, k, g in SPECS.get(lang, [])],
            [re.compile(p, re.M) for p in IMPORT_SPECS.get(lang, [])],
        )
    return _COMPILED[lang]


def _line_starts(text: str) -> list:
    return [0] + [m.end() for m in re.finditer("\n", text)]


def _line_of(starts: list, offset: int) -> int:
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


def _body_brace(code: str, j: int, kind: str):
    """Offset of the '{' opening this definition's body, or None.

    Skips braces inside generic parameter lists (`<S = {}>`) and parameter lists,
    stops at ';' or a blank line, and for one-line kinds (type/const/macro) only
    follows the statement while the line visibly continues.
    """
    limit = min(len(code), j + 1500)
    angle = paren = 0
    one_line = kind in ("type", "const", "var", "macro")
    while j < limit:
        ch = code[j]
        if ch == "\n":
            if code.startswith("\n", j + 1) or code[j + 1:j + 2] == "\r":
                return None
            if one_line:
                prev = code[:j].rstrip()[-1:]
                if prev not in ("=", "(", "<", ",", "|", "&", ":") and angle == 0 and paren == 0:
                    return None
        elif ch == "(":
            paren += 1
        elif ch == ")":
            paren = max(0, paren - 1)
        elif ch == "<" and paren == 0:
            angle += 1
        elif ch == ">" and angle and code[j - 1] != "=":
            angle -= 1
        elif ch == ";" and paren == 0:
            return None
        elif ch == "{" and angle == 0 and paren == 0:
            return j
        j += 1
    return None


_NOT_COMMENT = re.compile(r"^#\s*(if|ifdef|ifndef|elif|else|endif|region|endregion|pragma|define|undef|include|nullable|line|error|warning)\b")


def _doc_above(lines: list, line_no: int) -> str:
    """First sentence of the comment block directly above a definition (1-based line_no)."""
    i = line_no - 2
    block = []
    while i >= 0 and len(block) < 200:
        s = lines[i].strip()
        if not s:
            break
        if _NOT_COMMENT.match(s):
            i -= 1
            continue
        if s.startswith(("//", "#", "*", "/*", "///", "--")) and not s.startswith(("#[", "#![", "//!")):
            block.append(re.sub(r"^(/\*\*?|\*/|\*|///?|#+|--)\s?", "", s).rstrip("*/ ").strip())
            i -= 1
            continue
        if s.startswith(("@", "[", "#[", "#![")):  # annotations / attributes between doc and def
            i -= 1
            continue
        break
    text = " ".join(t for t in reversed(block) if t and not t.startswith("@"))
    text = re.sub(r"\{@\w+\s+([^}]*)\}", r"\1", text)  # {@code x} / {@link Y}
    text = re.sub(r"<(?:see|seealso|paramref|typeparamref)\s+\w+=\"(?:[A-Z]:)?([^\"]+)\"\s*/>", r"\1", text)  # xml doc refs
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)  # html tags in javadoc / xml doc
    return _first_sentence(text) if text else ""


def _indent_end(lines: list, line_no: int, lang: str) -> int:
    base = len(lines[line_no - 1]) - len(lines[line_no - 1].lstrip())
    last = line_no
    for j in range(line_no, len(lines)):
        s = lines[j]
        if not s.strip():
            continue
        ind = len(s) - len(s.lstrip())
        if ind <= base:
            if lang == "ruby" and s.strip().startswith("end"):
                return j + 1
            return last
        last = j + 1
    return last


def extract_generic(text: str, lang: str) -> FileFacts:
    facts = FileFacts()
    code, code_str = mask(text, lang)
    lines = text.split("\n")
    starts = _line_starts(code)
    brace = {} if lang in INDENT_LANGS else _brace_ends(code)
    defs_rx, imp_rx = _compiled(lang)

    found = []  # (start_offset, line, name, kind, sig_end, recv)
    seen = set()
    for rx, kind, group in defs_rx:
        for m in rx.finditer(code):
            if kind == "decl":
                kind_eff = m.group(1).split()[-1].replace("@interface", "interface")
                name = m.group(group)
            elif kind == "method:go":
                kind_eff, name = "method", m.group(2)
            else:
                kind_eff, name = kind, m.group(group)
            if not name:
                continue
            bare = name.split("::")[-1].split(".")[-1].lstrip("#")
            if kind_eff in ("method?", "function") and bare in CONTROL:
                continue
            if kind_eff == "method?" and bare in KEYWORDS:
                continue
            if kind_eff in ("method?", "function") and re.search(
                    r"\b(new|return|throw|else|await|yield|case|in|of|typeof)\s+$", code[max(0, m.start(group) - 12):m.start(group)]):
                continue  # `new Foo() {` (anonymous class), `return foo() {…}` etc. are not definitions
            line = _line_of(starts, m.start(group))
            key = (line, bare)
            if key in seen:
                continue
            seen.add(key)
            recv = m.group(1) if kind == "method:go" else None
            found.append((m.start(), line, bare if kind_eff != "impl" else name.split("::")[-1], kind_eff, m.end(), recv))
    found.sort(key=lambda t: (t[0], t[1]))

    syms: list[Sym] = []
    ranges = []  # (start_line, end_line, idx) for containers
    for start, line, name, kind, mend, recv in found:
        # Extent: matching brace of the first '{' after the match (before ';'), else indentation, else one line.
        end_line = line
        if lang in INDENT_LANGS:
            end_line = _indent_end(lines, line, lang)
        else:
            j = _body_brace(code, mend - 1, kind)
            if j is not None and j in brace:
                end_line = _line_of(starts, brace[j])
        sig_src = code_str[starts[line - 1]: starts[line - 1] + 400]
        cut = len(sig_src)
        for stop in ("{", ";", "=>", "\n\n"):
            k = sig_src.find(stop)
            if k != -1 and (stop != "=>" or kind in ("function", "method?", "method")):
                cut = min(cut, k)
        if lang in INDENT_LANGS or lang == "go" and kind in ("type",):
            cut = min(cut, sig_src.find("\n") if "\n" in sig_src else cut)
        if kind in ("const", "type", "macro") and "\n" in sig_src[:cut]:
            cut = sig_src.find("\n")
        sig = _clip(sig_src[:cut])
        exported = True
        if lang == "go":
            exported = name[:1].isupper()
        elif lang in ("javascript", "typescript"):
            exported = sig.startswith("export") or kind in ("method?",) and not name.startswith("#")
        elif lang == "rust":
            exported = sig.startswith("pub") or kind == "impl"
        elif lang in ("java", "csharp", "kotlin", "swift", "php", "scala"):
            exported = "private" not in sig.split("(")[0]
        syms.append(Sym(name=name, kind=kind, line=line, end_line=max(end_line, line), signature=sig,
                        doc=_doc_above(lines, line), exported=exported))
        if recv:
            syms[-1].qualname = f"{recv}.{name}"

    # Nesting: innermost container whose range strictly contains the symbol.
    order = sorted(range(len(syms)), key=lambda i: (syms[i].line, -(syms[i].end_line)))
    stack: list[int] = []
    keep = [True] * len(syms)
    for i in order:
        s = syms[i]
        while stack and not (syms[stack[-1]].line <= s.line <= syms[stack[-1]].end_line and stack[-1] != i):
            stack.pop()
        if stack:
            s.parent = stack[-1]
        if s.kind == "method?":
            parent_kind = syms[s.parent].kind if s.parent is not None else None
            if parent_kind in CONTAINER_KINDS:
                s.kind = "method"
            else:
                keep[i] = False
                continue
        elif s.kind == "function" and s.parent is not None and syms[s.parent].kind in CONTAINER_KINDS:
            s.kind = "method"
        if s.kind in CONTAINER_KINDS or s.end_line > s.line:
            stack.append(i)

    # Drop rejected candidates and remap parents.
    remap, out = {}, []
    for i, s in enumerate(syms):
        if keep[i]:
            remap[i] = len(out)
            out.append(s)
    for s in out:
        p = s.parent
        while p is not None and p not in remap:
            p = syms[p].parent
        s.parent = remap.get(p) if p is not None else None
    for s in out:
        if not s.qualname:
            parts, p = [s.name], s.parent
            while p is not None:
                parts.append(out[p].name)
                p = out[p].parent
            s.qualname = ".".join(reversed(parts))
        if s.kind in ("class", "struct", "interface", "record", "trait") and (":" in s.signature or " extends " in s.signature
                                                                             or " implements " in s.signature):
            s.bases = [b for b in re.findall(r"\b([A-Z]\w+)", s.signature.split(s.name, 1)[-1]) if b != s.name][:6]
    facts.symbols = out

    for rx in imp_rx:
        for m in rx.finditer(code_str):
            raw = m.group(1)
            if raw:
                facts.imports.append(Imp(raw=raw, line=_line_of(starts, m.start(1))))
    prx = PACKAGE_RX.get(lang)
    if prx:
        m = prx.search(code)
        if m:
            facts.package = m.group(1)

    idents = facts.idents
    for ln, line_text in enumerate(code.split("\n"), 1):
        for name in IDENT_RX.findall(line_text):
            if len(name) >= 3 and name not in KEYWORDS:
                _add_ident(idents, name, ln)
    return facts


def extract_markdown(text: str) -> FileFacts:
    facts = FileFacts()
    lines = text.split("\n")
    in_fence = False
    heads = []
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
        for lm in re.finditer(r"\]\(([^)\s#]+)", line):  # relative links act as imports
            target = lm.group(1)
            if "://" not in target and not target.startswith("mailto:"):
                facts.imports.append(Imp(raw=target, line=i))
    stack: list[int] = []
    for n, (line, level, title) in enumerate(heads):
        end = len(lines)
        for line2, level2, _ in heads[n + 1:]:
            if level2 <= level:
                end = line2 - 1
                break
        while stack and heads[stack[-1]][1] >= level:
            stack.pop()
        parent = stack[-1] if stack else None
        facts.symbols.append(Sym(name=title[:80], kind=f"h{level}", line=line, end_line=end,
                                 signature="#" * level + " " + title[:120], parent=parent))
        stack.append(n)
    for s in facts.symbols:
        s.qualname = s.name
    return facts


def extract(text: str, lang: str) -> FileFacts:
    if lang == "python":
        return extract_python(text)
    if lang in ("csharp", "rust"):
        try:
            if lang == "csharp":
                from .lang_cs import extract_csharp
                return extract_csharp(text)
            from .lang_rs import extract_rust
            return extract_rust(text)
        except (RecursionError, IndexError, KeyError, ImportError):
            return extract_generic(text, lang)  # structural parser failed: fall back to patterns
    if lang == "markdown":
        return extract_markdown(text)
    if lang in SPECS:
        return extract_generic(text, lang)
    return FileFacts()
