"""Tests for scripts/toolkit.py and the plugin hooks. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLKIT = ROOT / "scripts" / "toolkit.py"


class ToolkitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="toolkit-test-"))
        cls.home = cls.tmp / "home"
        (cls.home / ".copilot").mkdir(parents=True)
        cls.env = {**os.environ, "HOME": str(cls.home), "XDG_CONFIG_HOME": str(cls.home / ".config"),
                   "CLAUDE_CONFIG_DIR": str(cls.home / ".claude"), "COPILOT_HOME": str(cls.home / ".copilot"),
                   "AI_TOOLKIT_BIN": str(cls.home / "bin"), "CODEMAP_CACHE": str(cls.tmp / "cache")}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def tk(self, *args, ok=True):
        proc = subprocess.run([sys.executable, str(TOOLKIT), *args], capture_output=True, text=True, env=self.env, timeout=300)
        if ok and proc.returncode != 0:
            self.fail(f"toolkit {' '.join(args)} failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
        return proc

    def test_generated_files_are_current(self):
        self.tk("build", "--check")

    def test_validate(self):
        self.assertIn("validate: ok", self.tk("validate").stdout)

    def test_audit_runs(self):
        out = self.tk("audit", "--no-git").stdout
        self.assertIn("Always-on cost", out)
        self.assertIn("all routes resolve", out)

    def test_user_level_install_and_doctor(self):
        self.tk("install", "--target", "copilot-user", "--target", "skills", "--bundle", "dev", "--no-upstream")
        cop = self.home / ".copilot"
        self.assertTrue((cop / "skills" / "kickoff" / "SKILL.md").exists())
        self.assertTrue((cop / "agents" / "code-navigator.agent.md").exists())
        mcp = json.loads((cop / "mcp-config.json").read_text())
        self.assertTrue(mcp["mcpServers"]["codemap"]["args"][0].endswith("plugins/codemap/scripts/codemap.py"))
        hooks = json.loads((cop / "hooks" / "ai-toolkit.json").read_text())
        self.assertEqual(hooks["version"], 1)
        self.assertTrue(all(Path(e["env"]["PLUGIN_ROOT"]).is_dir() for e in hooks["hooks"]["sessionStart"]))
        self.assertTrue((self.home / "bin" / "codemap").exists())
        ledger = json.loads((self.home / ".config" / "ai-toolkit" / "installed.json").read_text())
        self.assertEqual(ledger["bundle"], "dev")

        # A repo with vendored copies: identical ones shadow user-level installs; edited ones are kept.
        repo = self.tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        self.tk("adopt", str(repo), "--mode", "vendor", "--plugin", "kickoff")
        (repo / ".claude" / "skills" / "harvest" / "SKILL.md").write_text("customized\n")
        out = self.tk("doctor", "--repo", str(repo), ok=False).stdout
        self.assertIn(".claude/skills/kickoff duplicates the toolkit skill", out)
        self.assertIn(".claude/skills/harvest differs", out)
        self.tk("doctor", "--repo", str(repo), "--fix", ok=False)
        self.assertFalse((repo / ".claude" / "skills" / "kickoff").exists())
        self.assertTrue((repo / ".claude" / "skills" / "harvest").exists())

    def test_adopt_plugins_mode_writes_both_clients(self):
        repo = self.tmp / "repo-plugins"
        repo.mkdir()
        self.tk("adopt", str(repo), "--bundle", "core", "--upstream", "feature-dev@claude-plugins-official")
        for f in (".claude/settings.json", ".github/copilot/settings.json"):
            data = json.loads((repo / f).read_text())
            self.assertTrue(data["enabledPlugins"]["codemap@ai-toolkit"])
            self.assertIn("claude-plugins-official", data["extraKnownMarketplaces"])
        self.assertIn("@AGENTS.md", (repo / "CLAUDE.md").read_text())

    def test_adopt_vendor_codemap_mcp_server_runs(self):
        repo = self.tmp / "repo-vendor"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        (repo / "app.py").write_text("def hello():\n    return 1\n")
        self.tk("adopt", str(repo), "--mode", "vendor", "--plugin", "codemap", "--hooks")
        mcp = json.loads((repo / ".mcp.json").read_text())["mcpServers"]["codemap"]
        self.assertTrue((repo / mcp["args"][0]).is_file())
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "codemap", "arguments": {"cmd": "def hello"}}}]
        proc = subprocess.run([sys.executable, *mcp["args"]], cwd=repo, input="\n".join(map(json.dumps, msgs)) + "\n",
                              capture_output=True, text=True, timeout=60, env=self.env)
        replies = [json.loads(l) for l in proc.stdout.splitlines()]
        self.assertIn("def hello()", replies[1]["result"]["content"][0]["text"])
        hook = json.loads((repo / ".github" / "hooks" / "ai-toolkit-codemap.json").read_text())
        self.assertEqual(hook["hooks"]["sessionStart"][0]["env"]["PLUGIN_ROOT"], ".github/ai-toolkit/plugins/codemap")

    def test_adopt_review_workflow(self):
        repo = self.tmp / "repo-review"
        repo.mkdir()
        self.tk("adopt", str(repo), "--bundle", "core", "--review-workflow", "--review-ref", "abc123")
        wf = (repo / ".github" / "workflows" / "change-map.yml").read_text()
        self.assertIn("gimarais/ai-toolkit/.github/actions/change-map@abc123", wf)
        self.assertIn("fetch-depth: 0", wf)
        self.assertIn("pull-requests: write", wf)
        self.assertNotIn("pull_request_target", wf)

    def test_change_map_action_is_wired(self):
        import re
        action = (ROOT / ".github" / "actions" / "change-map" / "action.yml").read_text()
        self.assertIn("using: composite", action)
        self.assertTrue((ROOT / ".github" / "actions" / "change-map" / "../../../plugins/codemap/scripts/codemap.py").resolve().is_file())
        # No untrusted expression may be interpolated straight into a shell script.
        for block in re.findall(r"run: \|\n((?:        .*\n|\n)+)", action):
            self.assertNotIn("${{", block)

    def test_hooks_emit_valid_json(self):
        for plugin in ("kickoff", "codemap"):
            root = ROOT / "plugins" / plugin
            out = subprocess.run([sys.executable, str(root / "hooks" / "session_start.py"), "--format", "claude"],
                                 input="{}", capture_output=True, text=True, cwd=ROOT, env=self.env, timeout=30).stdout
            data = json.loads(out)
            self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "SessionStart")
            cmd = json.loads((root / "hooks" / "copilot-hooks.json").read_text())["hooks"]["sessionStart"][0]["bash"]
            out = subprocess.run(["bash", "-c", cmd], input="{}", capture_output=True, text=True, cwd=ROOT,
                                 env={**self.env, "PLUGIN_ROOT": str(root)}, timeout=30).stdout
            self.assertIn("additionalContext", json.loads(out))


if __name__ == "__main__":
    unittest.main()
