"""codemap must treat repositories and MCP callers as untrusted. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("CODEMAP_BACKGROUND", "0")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins" / "codemap" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from codemap_core.cli import run_line  # noqa: E402
from codemap_core.mcp import handle  # noqa: E402
from codemap_core.util import safe_path  # noqa: E402


def git(root, *args):
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args], cwd=root, check=True,
                   capture_output=True)


class UntrustedRepoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="codemap-sec-"))
        os.environ["CODEMAP_CACHE"] = str(cls.tmp / "cache")
        cls.secret = cls.tmp / "outside" / "secret.py"
        cls.secret.parent.mkdir(parents=True)
        cls.secret.write_text("def STOLEN_SECRET():\n    return 'hunter2'\n")
        cls.repo = cls.tmp / "repo"
        (cls.repo / "src").mkdir(parents=True)
        (cls.repo / "src" / "app.py").write_text("def main():\n    return 1\n")
        (cls.repo / "src" / "inside.py").symlink_to("app.py")             # fine: stays in the repo
        (cls.repo / "src" / "leak.py").symlink_to(cls.secret)              # must never be read
        if Path("/dev/zero").exists():
            (cls.repo / "src" / "zero.js").symlink_to("/dev/zero")         # must never be read
        (cls.repo / "src" / "huge.py").write_text("x = 1\n" * 300_000)    # over the 1 MB cap
        git(cls.repo, "init", "-q", "-b", "main")
        git(cls.repo, "add", "-A")
        git(cls.repo, "commit", "-q", "-m", "base")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def cm(self, line, restricted=False):
        out, err = io.StringIO(), io.StringIO()
        rc = run_line(f"--repo {self.repo} {line}" if not restricted else line, out, err, restricted=restricted)
        return rc, out.getvalue(), err.getvalue()

    def test_safe_path(self):
        self.assertIsNotNone(safe_path(self.repo, "src/app.py"))
        self.assertIsNotNone(safe_path(self.repo, "src/inside.py"))
        self.assertIsNone(safe_path(self.repo, "src/leak.py"))
        self.assertIsNone(safe_path(self.repo, "../outside/secret.py"))
        self.assertIsNone(safe_path(self.repo, "/etc/passwd"))
        self.assertIsNone(safe_path(self.repo, "src"))  # not a regular file
        if Path("/dev/zero").exists():
            self.assertIsNone(safe_path(self.repo, "src/zero.js"))

    def test_symlinks_leaving_the_repo_are_not_indexed_or_shown(self):
        rc, out, _ = self.cm("index --full --quiet")
        self.assertEqual(rc, 0)
        rc, out, _ = self.cm("find STOLEN_SECRET")
        self.assertNotIn("leak.py", out)
        self.assertIn("no symbols match", out)
        rc, out, err = self.cm("show src/leak.py:1-2")
        self.assertNotEqual(rc, 0)
        self.assertNotIn("hunter2", out + err)
        rc, out, _ = self.cm("show src/app.py:1-2")
        self.assertEqual(rc, 0)
        self.assertIn("def main", out)

    def test_oversized_files_are_skipped(self):
        self.cm("index --full --quiet")
        rc, out, _ = self.cm("outline src/huge.py")
        self.assertNotIn("x = 1", out)

    def test_mcp_refuses_other_repos_databases_and_file_writes(self):
        target = self.tmp / "written.txt"
        os.environ["CODEMAP_REPO"] = str(self.repo)
        try:
            for cmd in (f"--repo {self.tmp / 'outside'} show secret.py:1-2", f"--rep {self.tmp} overview",
                        f"--db {self.tmp / 'x.db'} overview", f"review --base main --out {target}",
                        f"review --base main -o {target}", f"review --base main --o {target}"):
                r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": "codemap", "arguments": {"cmd": cmd}}})["result"]
                self.assertTrue(r["isError"], cmd)
                self.assertNotIn("hunter2", r["content"][0]["text"], cmd)
            self.assertFalse(target.exists())
            self.assertFalse((self.tmp / "x.db").exists())
            ok = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                         "params": {"name": "codemap", "arguments": {"cmd": "def main"}}})["result"]
            self.assertFalse(ok["isError"], ok)
            self.assertIn("src/app.py", ok["content"][0]["text"])
        finally:
            os.environ.pop("CODEMAP_REPO", None)
        tools = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})["result"]["tools"]
        self.assertTrue(tools[0]["annotations"]["readOnlyHint"])

    def test_cli_still_allows_explicit_flags(self):
        rc, out, _ = self.cm(f"--db {self.tmp / 'cli.db'} def main")
        self.assertEqual(rc, 0)
        self.assertIn("src/app.py", out)

    def test_mcp_stdout_stays_json_on_help_and_version(self):
        lines = [json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                             "params": {"name": "codemap", "arguments": {"cmd": cmd}}})
                 for i, cmd in enumerate(("find --help", "review -h", "--version", "bogus --nope"), 1)]
        proc = subprocess.run([sys.executable, str(SCRIPTS / "codemap.py"), "mcp"], input="\n".join(lines) + "\n",
                              capture_output=True, text=True, cwd=self.repo, timeout=60,
                              env={**os.environ, "CODEMAP_REPO": str(self.repo)})
        replies = [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]  # every line must be JSON
        self.assertEqual([r["id"] for r in replies], [1, 2, 3, 4])
        self.assertIn("usage: codemap find", replies[0]["result"]["content"][0]["text"])
        self.assertIn("codemap", replies[2]["result"]["content"][0]["text"])
        self.assertTrue(replies[3]["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
