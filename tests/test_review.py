"""Tests for `codemap review`. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

os.environ.setdefault("CODEMAP_BACKGROUND", "0")  # no detached re-index processes during tests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "codemap" / "scripts"))

from codemap_core.cli import run_line  # noqa: E402
from codemap_core.util import est_tokens  # noqa: E402

BASE = {
    "pkg/__init__.py": "",
    "pkg/core.py": '''
        def parse(text):
            return text.strip()

        def legacy():
            return "old"

        def helper_x(values):
            total = 0
            for v in values:
                total += v * 2
            return total

        class Store:
            def get(self, key):
                return self.data.get(key)
        ''',
    "pkg/api.py": '''
        from .core import parse, Store

        def handle(req):
            return parse(req)
        ''',
    "pkg/cli.py": '''
        from .core import parse, legacy

        def main(argv):
            print(parse(argv[0]), legacy())
        ''',
    "pkg/util_a.py": '''
        def slugify(s):
            out = s.lower().replace(" ", "-")
            return out.strip("-")
        ''',
    "pkg/util_b.py": "X = 1\n",
    "tests/test_api.py": '''
        from pkg.api import handle

        def test_handle():
            assert handle(" a ") == "a"
        ''',
    "requirements.txt": "requests==2.30.0\n",
    "web/util.ts": 'export function fmt(x: string): string {\n  return x.trim();\n}\n',
}

HEAD = {
    "pkg/core.py": '''
        def parse(text, strict=False):
            if strict and not text:
                raise ValueError("empty")
            return text.strip()

        def helper_y(values):
            total = 0
            for v in values:
                total += v * 2
            return total

        def validate(value):
            return bool(value)

        class Store:
            def get(self, key):
                return self.data.get(key, None)
        ''',
    "pkg/api.py": '''
        from .core import parse, Store

        def handle(req):
            return parse(req, strict=True)
        ''',
    "pkg/util_a.py": "Y = 2\n",
    "pkg/util_b.py": '''
        X = 1

        def slugify(s):
            out = s.lower().replace(" ", "-")
            return out.strip("-")
        ''',
    "pkg/auth/token.py": '''
        def issue_token(user):
            return f"tok-{user}"
        ''',
    "requirements.txt": "requests==2.31.0\npyyaml==6.0\n",
    "web/util.ts": 'export function fmt(x: string): string {\n  return x.trim() + "</script><script>alert(1)</script>";\n}\n',
    "docs/notes.md": "<!-- generated: keep -->\n# Notes & <tips>\n\u2028line\n",
}


def write(root: Path, files: dict) -> None:
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")


def git(root, *args):
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args], cwd=root, check=True,
                   capture_output=True)


class ReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="codemap-review-"))
        cls.repo = cls.tmp / "repo"
        cls.repo.mkdir()
        os.environ["CODEMAP_CACHE"] = str(cls.tmp / "cache")
        write(cls.repo, BASE)
        git(cls.repo, "init", "-q", "-b", "main")
        git(cls.repo, "add", "-A")
        git(cls.repo, "commit", "-q", "-m", "base")
        git(cls.repo, "checkout", "-q", "-b", "feature")
        write(cls.repo, HEAD)  # left uncommitted: the default head is the working tree
        cls.a = json.loads(cls.cm("review --base main --format json"))
        cls.files = {f["path"]: f for f in cls.a["files"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def cm(cls, line: str) -> str:
        out, err = io.StringIO(), io.StringIO()
        rc = run_line(f"--repo {cls.repo} {line}", out, err)
        if rc != 0:
            raise AssertionError(f"codemap {line} -> {rc}: {err.getvalue()}")
        return out.getvalue()

    def changes(self, path):
        return {(c["change"], c["qualname"]) for c in self.files[path]["symbols"]}

    def test_symbol_level_changes(self):
        ch = self.changes("pkg/core.py")
        self.assertIn(("signature", "parse"), ch)
        self.assertIn(("removed", "legacy"), ch)
        self.assertIn(("renamed", "helper_y"), ch)
        self.assertIn(("added", "validate"), ch)
        self.assertIn(("modified", "Store.get"), ch)
        self.assertNotIn(("modified", "Store"), ch, "a container is not modified when only its child changed")

    def test_move_across_files(self):
        moved = [c for c in self.files["pkg/util_b.py"]["symbols"] if c["change"] == "moved"]
        self.assertEqual(moved[0]["name"], "slugify")
        self.assertNotIn(("removed", "slugify"), self.changes("pkg/util_a.py"))

    def test_untracked_files_are_included(self):
        self.assertEqual(self.files["pkg/auth/token.py"]["status"], "A")

    def test_callers_outside_the_diff(self):
        sig = next(c for c in self.files["pkg/core.py"]["symbols"] if c["qualname"] == "parse")
        self.assertTrue(any(w.startswith("pkg/cli.py") for w in sig["callers_outside"]), sig)
        self.assertFalse(any(w.startswith("pkg/api.py") for w in sig["callers_outside"]), "api.py was updated in the diff")
        msgs = " ".join(a["message"] for a in self.a["attention"])
        self.assertIn("`legacy` removed", msgs)
        self.assertIn("`parse` signature changed", msgs)

    def test_tests_and_risk(self):
        self.assertIn("pkg/auth/token.py", self.a["tests"]["untested"])
        token = self.files["pkg/auth/token.py"]
        self.assertTrue(any("sensitive" in r for r in token["reasons"]))
        self.assertIn(self.files["pkg/core.py"]["level"], ("medium", "high"))
        self.assertEqual(self.a["files"][0]["risk"], max(f["risk"] for f in self.a["files"]))

    def test_dependency_changes(self):
        deps = {(d["change"], d["name"]) for d in self.a["deps"]}
        self.assertIn(("changed", "requests"), deps)
        self.assertIn(("added", "pyyaml"), deps)

    def test_markdown_has_mermaid_and_marker(self):
        md = self.cm("review --base main --format md")
        self.assertIn("<!-- codemap-change-map -->", md)
        self.assertIn("```mermaid\nflowchart LR", md)
        self.assertIn("pkg/core.py", md)
        self.assertLess(len(md), 65536)

    def test_html_escapes_diff_content(self):
        out = self.tmp / "report.html"
        self.cm(f"review --base main --format html --out {out}")
        html = out.read_text()
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertEqual(html.count("</script>"), 2, "only the data block and the app script may close")
        block = html.split('<script type="application/json" id="data">', 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<", block)
        data = json.loads(block)  # must stay valid JSON even with HTML comments in the diff
        self.assertIn("docs/notes.md", {f["path"] for f in data["files"]})
        self.assertIn("</script><script>alert(1)</script>", json.dumps(data, ensure_ascii=False))

    def test_context_pack_respects_budget(self):
        for budget in (300, 1500):
            ctx = self.cm(f"review --base main --format context --budget {budget}")
            self.assertLessEqual(est_tokens(ctx), budget * 1.15, f"budget {budget}")
            self.assertIn("ATTENTION", ctx)
        self.assertIn("@@", self.cm("review --base main --format context --budget 6000"))

    def test_committed_head_ref(self):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "feature")
        try:
            a = json.loads(self.cm("review --base main --head HEAD --format json"))
            self.assertEqual({f["path"] for f in a["files"]}, set(self.files))
        finally:
            git(self.repo, "reset", "-q", "--soft", "HEAD~1")

    def test_text_brief_is_compact(self):
        txt = self.cm("review --base main")
        self.assertTrue(txt.startswith("change map:"))
        self.assertLess(est_tokens(txt), 1500)

    def test_mcp_route(self):
        from codemap_core.mcp import handle
        r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "codemap", "arguments": {"cmd": f"--repo {self.repo} review --base main"}}})
        self.assertIn("review order", r["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
