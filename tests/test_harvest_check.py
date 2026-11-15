"""Tests for the kickoff Stop hook that nudges for a missing harvest. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "plugins" / "kickoff" / "hooks" / "harvest_check.py"


def entry(role, text, as_blocks=True):
    content = [{"type": "text", "text": text}] if as_blocks else text
    return json.dumps({"type": role, "message": {"role": role, "content": content}})


class HarvestCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harvest-check-"))
        (self.tmp / "t").mkdir()
        self.env = {**os.environ, "TMPDIR": str(self.tmp / "t")}
        self.env.pop("KICKOFF_HARVEST_CHECK", None)
        self.session = uuid.uuid4().hex

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_hook(self, lines, extra=None, env=None, raw=None):
        transcript = self.tmp / "transcript.jsonl"
        transcript.write_text("\n".join(lines) + "\n")
        payload = raw if raw is not None else json.dumps(
            {"session_id": self.session, "transcript_path": str(transcript), **(extra or {})})
        proc = subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True,
                              env={**self.env, **(env or {})}, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def test_route_without_harvest_blocks_once(self):
        lines = [entry("user", "fix the bug"), entry("assistant", "**Route:** debugging → engineering-craft:debugging")]
        data = json.loads(self.run_hook(lines))
        self.assertEqual(data["decision"], "block")
        self.assertIn("harvest", data["reason"])
        self.assertEqual(self.run_hook(lines), "", "the reminder must not repeat for the same route")

    def test_harvest_after_route_passes(self):
        same_message = [entry("assistant", "Route: review → reviewing-code\n...\n**Harvest**\n- nothing reusable")]
        later_message = [entry("assistant", "Route: review → reviewing-code"), entry("assistant", "Harvest: nothing reusable")]
        self.assertEqual(self.run_hook(same_message), "")
        self.assertEqual(self.run_hook(later_message), "")

    def test_new_route_after_harvest_needs_its_own_harvest(self):
        lines = [entry("assistant", "Route: a → x"), entry("assistant", "Harvest: done"),
                 entry("assistant", "Route: b → y", as_blocks=False)]
        self.assertEqual(json.loads(self.run_hook(lines))["decision"], "block")

    def test_no_route_or_user_only_text_passes(self):
        self.assertEqual(self.run_hook([entry("assistant", "Just answering a question.")]), "")
        self.assertEqual(self.run_hook([entry("user", "Route: a → b")]), "")

    def test_stop_hook_active_disable_switch_and_bad_input_fail_open(self):
        lines = [entry("assistant", "Route: a → b")]
        self.assertEqual(self.run_hook(lines, extra={"stop_hook_active": True}), "")
        self.assertEqual(self.run_hook(lines, env={"KICKOFF_HARVEST_CHECK": "0"}), "")
        self.assertEqual(self.run_hook(lines, raw="not json"), "")
        self.assertEqual(self.run_hook(lines, raw=json.dumps({"transcript_path": str(self.tmp / "missing.jsonl")})), "")
        self.assertEqual(self.run_hook(["{broken", entry("assistant", "hello")]), "")


if __name__ == "__main__":
    unittest.main()
