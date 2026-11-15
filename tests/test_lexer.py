"""Unit tests for codemap's C#/Rust masking lexer and tokenizer. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "codemap" / "scripts"))

from codemap_core.lexer import mask_csharp, mask_rust, tokenize  # noqa: E402


class MaskInvariantsMixin:
    """Masking must keep offsets and line numbers identical to the source."""

    def assertSameShape(self, src, masked):
        self.assertEqual(len(src), len(masked))
        self.assertEqual([i for i, ch in enumerate(src) if ch == "\n"], [i for i, ch in enumerate(masked) if ch == "\n"])


class CSharpMaskTest(unittest.TestCase, MaskInvariantsMixin):
    def test_comments_and_strings_are_blanked(self):
        src = ('class A { // void Hidden() {}\n'
               '  /* class Fake {} */ string s = "class InString { }";\n'
               '  string v = @"multi ""quoted""\nline"; char c = \'{\';\n}\n')
        code, code_str = mask_csharp(src)
        self.assertSameShape(src, code)
        self.assertSameShape(src, code_str)
        for gone in ("Hidden", "Fake", "InString", "quoted"):
            self.assertNotIn(gone, code)
        self.assertNotIn("Hidden", code_str)          # comments blanked in both
        self.assertIn("class InString { }", code_str)  # strings kept in code_str
        self.assertEqual(code.count("{"), code.count("}"))  # braces inside strings/chars no longer count

    def test_interpolated_and_raw_strings(self):
        src = ('var a = $"x {Call("in{")} y";\n'
               'var b = """\n  raw { not code }\n  """;\nint after = 1;\n')
        code, _ = mask_csharp(src)
        self.assertSameShape(src, code)
        self.assertNotIn("not code", code)
        self.assertIn("int after = 1;", code)

    def test_preprocessor_directives_do_not_break_masking(self):
        src = "#region Stuff\n#if DEBUG\nclass Dbg {}\n#endif\n#endregion\nclass Real {}\n"
        code, _ = mask_csharp(src)
        self.assertEqual(code.count("\n"), src.count("\n"))
        self.assertIn("class Real {}", code)


class RustMaskTest(unittest.TestCase, MaskInvariantsMixin):
    def test_comments_strings_and_lifetimes(self):
        src = ('/// doc fn hidden()\n'
               'fn real<\'a>(x: &\'a str) -> char { let s = "fn fake() {"; let r = r#"raw "} fn x"#; \'{\' }\n'
               '/* outer /* nested fn inner() */ still comment */ fn after() {}\n')
        code, code_str = mask_rust(src)
        self.assertSameShape(src, code)
        self.assertSameShape(src, code_str)
        for gone in ("hidden", "fake", "raw ", "inner", "still comment"):
            self.assertNotIn(gone, code)
        self.assertIn("fn real<'a>(x: &'a str)", code)  # lifetimes are not char literals
        self.assertIn("fn after() {}", code)
        self.assertEqual(code.count("{"), code.count("}"))

    def test_byte_and_c_strings(self):
        src = 'let a = b"{"; let b = c"}"; let c = b\'{\'; fn ok() {}\n'
        code, _ = mask_rust(src)
        self.assertSameShape(src, code)
        self.assertIn("fn ok() {}", code)
        self.assertEqual(code.count("{"), code.count("}"))


class TokenizeTest(unittest.TestCase):
    def test_tokens_lines_and_bracket_matching(self):
        toks = tokenize("fn a() {\n  call(x[1]);\n}\n")
        self.assertEqual(toks.text[:3], ["fn", "a", "("])
        self.assertEqual(toks.line[toks.text.index("call")], 2)
        self.assertEqual(toks.line[len(toks) - 1], 3)
        open_brace = toks.text.index("{")
        self.assertEqual(toks.text[toks.match[open_brace]], "}")
        self.assertEqual(toks.match[toks.match[open_brace]], open_brace)

    def test_multi_char_operators_and_raw_identifiers(self):
        toks = tokenize("a::b -> c => d ?? e ??= f r#type 'life")
        for t in ("::", "->", "=>", "??", "??=", "r#type", "'life"):
            self.assertIn(t, toks.text)

    def test_mismatched_brackets_are_tolerated(self):
        toks = tokenize("{ ( ] }")
        self.assertEqual(toks.text[toks.match[0]], "}")
        self.assertNotIn(1, toks.match)  # the unclosed "(" stays unmatched


if __name__ == "__main__":
    unittest.main()
