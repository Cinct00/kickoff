"""Freshness at scale: git-based lazy refresh and .codemap.json include/exclude. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("CODEMAP_BACKGROUND", "0")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "codemap" / "scripts"))

from codemap_core.cli import run_line  # noqa: E402
from codemap_core import store as store_mod  # noqa: E402


def git(repo, *args):
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args], cwd=repo, check=True,
                   capture_output=True)


class FreshnessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="codemap-fresh-"))
        self.repo = self.tmp / "repo"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "gen").mkdir()
        (self.repo / "src" / "a.py").write_text("def alpha():\n    return 1\n")
        (self.repo / "src" / "b.py").write_text("def beta():\n    return 2\n")
        (self.repo / "src" / "Big.Designer.py").write_text("def designer_noise():\n    pass\n")
        (self.repo / "gen" / "client.py").write_text("def generated_client():\n    pass\n")
        (self.repo / ".gitignore").write_text("gen/\n")
        (self.repo / ".codemap.json").write_text('{"include": ["gen/**/*.py"], "exclude": ["**/*.Designer.py"]}')
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        os.environ["CODEMAP_CACHE"] = str(self.tmp / "cache")
        self.old_gap = store_mod.LAZY_MIN_GAP
        store_mod.LAZY_MIN_GAP = 0  # every query re-checks, so tests don't need to sleep
        self.cm("index --quiet")

    def tearDown(self):
        store_mod.LAZY_MIN_GAP = self.old_gap
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cm(self, line):
        out, err = io.StringIO(), io.StringIO()
        run_line(f"--repo {self.repo} {line}", out, err)
        return out.getvalue()

    def found(self, name):
        return "no symbols match" not in self.cm(f"find {name}")

    def test_include_and_exclude(self):
        self.assertTrue(self.found("generated_client"), "gitignored file opted in via .codemap.json")
        self.assertFalse(self.found("designer_noise"), "tracked file excluded via .codemap.json")

    def test_lazy_refresh_tracks_git_changes(self):
        time.sleep(0.01)
        (self.repo / "src" / "a.py").write_text("def alpha_renamed():\n    return 1\n")  # uncommitted edit
        self.assertTrue(self.found("alpha_renamed"))
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "rename")  # now clean again
        (self.repo / "src" / "c.py").write_text("def gamma():\n    pass\n")  # untracked new file
        self.assertTrue(self.found("gamma"))
        (self.repo / "src" / "b.py").unlink()  # deletion
        self.assertFalse(self.found("beta"))
        git(self.repo, "checkout", "-q", "--", "src/b.py")  # revert to clean: must come back
        self.assertTrue(self.found("beta"))
        (self.repo / "gen" / "client.py").write_text("def generated_client_v2():\n    pass\n")  # ignored + included
        self.assertTrue(self.found("generated_client_v2"))

    def test_branch_switch(self):
        git(self.repo, "checkout", "-q", "-b", "feature")
        (self.repo / "src" / "d.py").write_text("def delta():\n    pass\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "feature")
        self.assertTrue(self.found("delta"))
        git(self.repo, "checkout", "-q", "main")  # commits since the indexed head are diffed both ways
        self.assertFalse(self.found("delta"))


if __name__ == "__main__":
    unittest.main()
