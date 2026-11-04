"""Tests for the local-first PreToolUse hook. Run: python3 -m unittest discover -s tests"""
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
PLUGIN = ROOT / "plugins" / "local-first"
HOOK = PLUGIN / "hooks" / "local_first.py"


def make_clone(path: Path, remote: str, files: dict[str, str], branch: str = "main") -> Path:
    (path / ".git").mkdir(parents=True)
    (path / ".git" / "config").write_text(f'[remote "origin"]\n\turl = {remote}\n\tfetch = +refs/heads/*:refs/remotes/origin/*\n')
    (path / ".git" / "HEAD").write_text(f"ref: refs/heads/{branch}\n")
    for rel, text in files.items():
        (path / rel).parent.mkdir(parents=True, exist_ok=True)
        (path / rel).write_text(text)
    return path


class LocalFirstHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="local-first-test-"))
        self.home = self.tmp / "home"
        self.src = self.home / "src"
        self.clone = make_clone(self.src / "widgets", "git@github.com:Acme/widgets.git", {"src/app.py": "print(1)\n"})
        make_clone(self.src / "nested" / "gadgets", "https://github.com/acme/gadgets", {"README.md": "# gadgets\n"})
        self.project = make_clone(self.tmp / "proj", "https://github.com/me/proj.git",
                                  {"node_modules/leftpad/README.md": "# leftpad\n", "docs/sdk/index.md": "sdk\n"})
        self.env = {**os.environ, "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / ".config"),
                    "XDG_CACHE_HOME": str(self.tmp / "cache"), "TMPDIR": str(self.tmp / "t")}
        self.env.pop("AI_TOOLKIT_LOCAL_FIRST", None)
        self.env.pop("AI_TOOLKIT_LOCAL_ROOTS", None)
        (self.tmp / "t").mkdir()
        self.session = uuid.uuid4().hex

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_hook(self, tool, args, fmt="claude", env=None, raw=None):
        payload = raw if raw is not None else json.dumps(
            {"session_id": self.session, "cwd": str(self.project), "tool_name": tool, "tool_input": args})
        proc = subprocess.run([sys.executable, str(HOOK), "--format", fmt], input=payload, capture_output=True,
                              text=True, env={**self.env, **(env or {})}, cwd=self.project, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def assertDenied(self, out, *needles):
        data = json.loads(out)
        hso = data["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        self.assertEqual(hso["permissionDecision"], "deny")
        for n in needles:
            self.assertIn(n, hso["permissionDecisionReason"])
        return hso["permissionDecisionReason"]

    def test_github_file_redirects_once_then_allows(self):
        args = {"owner": "acme", "repo": "widgets", "path": "src/app.py"}
        reason = self.assertDenied(self.run_hook("mcp__github__get_file_contents", args),
                                   str(self.clone / "src" / "app.py"), "on main")
        self.assertIn("repeat the same call", reason)
        self.assertEqual(self.run_hook("mcp__github__get_file_contents", args), "")

    def test_strict_mode_always_denies(self):
        args = {"owner": "acme", "repo": "widgets", "path": "src/app.py"}
        env = {"AI_TOOLKIT_LOCAL_FIRST": "strict"}
        self.assertDenied(self.run_hook("mcp__github__get_file_contents", args, env=env), "strict")
        self.assertDenied(self.run_hook("mcp__github__get_file_contents", args, env=env))

    def test_off_mode_and_unknown_repos_pass(self):
        args = {"owner": "acme", "repo": "widgets", "path": "src/app.py"}
        self.assertEqual(self.run_hook("mcp__github__get_file_contents", args, env={"AI_TOOLKIT_LOCAL_FIRST": "off"}), "")
        self.assertEqual(self.run_hook("mcp__github__get_file_contents", {"owner": "x", "repo": "y", "path": "a"}), "")

    def test_missing_local_file_lets_remote_through(self):
        self.assertEqual(self.run_hook("mcp__github__get_file_contents",
                                       {"owner": "acme", "repo": "widgets", "path": "src/new.py"}), "")

    def test_path_traversal_is_not_suggested(self):
        self.assertEqual(self.run_hook("mcp__github__get_file_contents",
                                       {"owner": "acme", "repo": "widgets", "path": "../../../etc/passwd"}), "")

    def test_nested_root_and_code_search(self):
        self.assertDenied(self.run_hook("mcp__github__search_code", {"query": "repo:acme/gadgets parse"}),
                          str(self.src / "nested" / "gadgets"), "Grep")

    def test_writes_and_issue_tools_are_ignored(self):
        args = {"owner": "acme", "repo": "widgets", "path": "src/app.py", "content": "x"}
        self.assertEqual(self.run_hook("mcp__github__create_or_update_file", args), "")
        self.assertEqual(self.run_hook("mcp__github__list_issues", {"owner": "acme", "repo": "widgets"}), "")
        self.assertEqual(self.run_hook("mcp__github__pull_request_read", {"owner": "acme", "repo": "widgets"}), "")

    def test_webfetch_github_and_raw_urls(self):
        self.assertDenied(self.run_hook("WebFetch", {"url": "https://github.com/acme/widgets/blob/dev/src/app.py",
                                                     "prompt": "x"}), str(self.clone / "src" / "app.py"))
        self.assertDenied(self.run_hook("WebFetch", {"url": "https://raw.githubusercontent.com/acme/widgets/main/src/app.py"}))
        self.assertEqual(self.run_hook("WebFetch", {"url": "https://github.com/acme/widgets/issues/3"}), "")

    def test_bash_curl_and_gh_api(self):
        self.assertDenied(self.run_hook("Bash", {"command": "curl -sL https://raw.githubusercontent.com/acme/widgets/main/src/app.py"}))
        self.assertDenied(self.run_hook("Bash", {"command": "gh api repos/acme/widgets/contents/src/app.py --jq .content"}))
        self.assertEqual(self.run_hook("Bash", {"command": "ls src"}), "")

    def test_library_docs_use_installed_dependency_and_clone(self):
        self.assertDenied(self.run_hook("mcp__context7__resolve-library-id", {"libraryName": "leftpad"}),
                          str(self.project / "node_modules" / "leftpad"))
        self.assertDenied(self.run_hook("mcp__context7__get-library-docs", {"context7CompatibleLibraryID": "/acme/widgets"}),
                          str(self.clone))

    def test_docs_map_from_user_and_project_config(self):
        cfg = self.home / ".config" / "ai-toolkit"
        cfg.mkdir(parents=True)
        (self.home / "docs" / "tf").mkdir(parents=True)
        (cfg / "local-first.json").write_text(json.dumps({"docs": {"terraform": str(self.home / "docs" / "tf")}}))
        self.assertDenied(self.run_hook("WebSearch", {"query": "terraform aws_instance arguments"}), str(self.home / "docs" / "tf"))
        (self.project / ".ai-toolkit").mkdir()
        (self.project / ".ai-toolkit" / "local-first.json").write_text(json.dumps(
            {"docs": {"our-sdk": "docs/sdk", "evil": "../../home", "abs": "/etc"}}))
        self.assertDenied(self.run_hook("mcp__docs__search_docs", {"query": "our-sdk auth flow"}), "docs/sdk")
        self.assertEqual(self.run_hook("mcp__docs__search_docs", {"query": "evil abs"}), "")

    def test_project_config_cannot_add_roots(self):
        other = make_clone(self.tmp / "elsewhere" / "secret", "https://github.com/acme/secret", {"a.txt": "x"})
        (self.project / ".ai-toolkit").mkdir()
        (self.project / ".ai-toolkit" / "local-first.json").write_text(json.dumps({"roots": [str(other.parent)]}))
        self.assertEqual(self.run_hook("mcp__github__get_file_contents", {"owner": "acme", "repo": "secret", "path": "a.txt"}), "")
        self.assertDenied(self.run_hook("mcp__github__get_file_contents", {"owner": "acme", "repo": "secret", "path": "a.txt"},
                                        env={"AI_TOOLKIT_LOCAL_ROOTS": str(other.parent)}))

    def test_local_tools_skip_and_bad_input_fails_open(self):
        self.assertEqual(self.run_hook("Read", {"file_path": "https://github.com/acme/widgets/blob/main/src/app.py"}), "")
        self.assertEqual(self.run_hook("x", {}, raw="not json"), "")
        self.assertEqual(self.run_hook("x", {}, fmt="copilot", raw="not json"), "{}")

    def test_copilot_format_with_string_args(self):
        payload = json.dumps({"timestamp": 1, "cwd": str(self.project), "toolName": "github-mcp-server-get_file_contents",
                              "toolArgs": json.dumps({"owner": "acme", "repo": "widgets", "path": "src/app.py"})})
        data = json.loads(self.run_hook("", {}, fmt="copilot", raw=payload))
        self.assertEqual(data["permissionDecision"], "deny")
        self.assertIn(str(self.clone), data["permissionDecisionReason"])
        self.assertEqual(json.loads(self.run_hook("bash", {}, fmt="copilot", raw=json.dumps(
            {"cwd": str(self.project), "toolName": "bash", "toolArgs": "{\"command\": \"ls\"}"}))), {})

    def test_hook_files_are_wired(self):
        claude = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]["PreToolUse"][0]
        self.assertIn("mcp__", claude["matcher"])
        self.assertIn("local_first.py", claude["hooks"][0]["command"])
        cmd = json.loads((PLUGIN / "hooks" / "copilot-hooks.json").read_text())["hooks"]["preToolUse"][0]["bash"]
        payload = json.dumps({"cwd": str(self.project), "toolName": "web_fetch",
                              "toolArgs": json.dumps({"url": "https://github.com/acme/widgets/tree/main/src/app.py"})})
        out = subprocess.run(["bash", "-c", cmd], input=payload, capture_output=True, text=True, cwd=self.project,
                             env={**self.env, "PLUGIN_ROOT": str(PLUGIN)}, timeout=30).stdout
        self.assertEqual(json.loads(out)["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
