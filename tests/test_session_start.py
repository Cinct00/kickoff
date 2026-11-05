"""Tests for the kickoff SessionStart hook. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "plugins" / "kickoff" / "hooks" / "session_start.py"


class KickoffSessionStartTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kickoff-session-"))
        self.home = self.tmp / "home"
        self.cfg = self.home / ".config"
        self.cwd = self.tmp / "project"
        for d in (self.home, self.cwd):
            d.mkdir(parents=True)
        self.env = {**os.environ, "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.cfg), "USERPROFILE": str(self.home)}
        self.env.pop("KICKOFF_HOME", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fake_toolkit(self, path: Path, doctor_output: str = "") -> Path:
        (path / "scripts").mkdir(parents=True)
        (path / "toolkit.json").write_text("{}")
        (path / "scripts" / "toolkit.py").write_text(f"print({doctor_output!r})\n")
        return path

    def run_hook(self, fmt="claude", env=None):
        proc = subprocess.run([sys.executable, str(HOOK), "--format", fmt], input="{}", capture_output=True, text=True,
                              cwd=self.cwd, env={**self.env, **(env or {})}, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def context(self, **kw):
        return self.run_hook(**kw)["hookSpecificOutput"]["additionalContext"]

    def test_formats(self):
        out = self.run_hook("claude")
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("kickoff", out["hookSpecificOutput"]["additionalContext"])
        self.assertIn("kickoff", self.run_hook("copilot")["additionalContext"])

    def test_no_toolkit_checkout_found(self):
        self.assertNotIn("Toolkit checkout", self.context())

    def test_toolkit_home_resolution_order(self):
        env_home = self.fake_toolkit(self.tmp / "from-env")
        marker_home = self.fake_toolkit(self.tmp / "from-marker")
        default_home = self.fake_toolkit(self.home / ".kickoff")
        self.assertIn(f"Toolkit checkout: {default_home}", self.context())
        (self.cfg / "kickoff").mkdir(parents=True, exist_ok=True)
        (self.cfg / "kickoff" / "home").write_text(f"{marker_home}\n")
        self.assertIn(f"Toolkit checkout: {marker_home}", self.context())
        self.assertIn(f"Toolkit checkout: {env_home}", self.context(env={"KICKOFF_HOME": str(env_home)}))
        # An env var pointing somewhere without toolkit.json is ignored.
        self.assertIn(f"Toolkit checkout: {marker_home}", self.context(env={"KICKOFF_HOME": str(self.tmp)}))

    def test_open_gaps_are_counted(self):
        ledger = self.cwd / "catalog" / "gaps.md"
        ledger.parent.mkdir()
        ledger.write_text("| gap | status |\n|---|---|\n| a | open |\n| b | closed |\n| c | open |\n")
        self.assertIn("2 open toolkit gap(s)", self.context())

    def test_doctor_nudge_runs_at_most_daily(self):
        self.fake_toolkit(self.home / ".kickoff", doctor_output="toolkit doctor: 1 issue(s)")
        self.assertIn("toolkit doctor: 1 issue(s)", self.context())
        self.assertNotIn("toolkit doctor", self.context(), "second run within a day must be silent")
        stamp = self.cfg / "kickoff" / "last-doctor"
        old = time.time() - 2 * 86400
        os.utime(stamp, (old, old))
        self.assertIn("toolkit doctor: 1 issue(s)", self.context())


    def test_failing_selftest_is_reported(self):
        self.fake_toolkit(self.home / ".kickoff")
        res = self.cfg / "kickoff" / "selftest.json"
        res.parent.mkdir(parents=True, exist_ok=True)
        res.write_text(json.dumps({"failed": ["local-first: Copilot preToolUse hook"]}))
        self.assertIn("1 check(s) failing (local-first: Copilot preToolUse hook)", self.context())
        self.assertNotIn("selftest", self.context(env={"KICKOFF_SELFTEST": "1"}), "no nudges inside a self-test")


if __name__ == "__main__":
    unittest.main()
