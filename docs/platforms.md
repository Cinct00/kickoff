# Platforms

What works where, and how to set each client up.

## Compatibility

| | Claude Code | Claude app | Copilot CLI | Copilot cloud agent | Copilot in VS Code | Codex / Cursor / Gemini CLI |
|---|---|---|---|---|---|---|
| Toolkit skills | ✅ plugin | ✅ synced skills | ✅ plugin | ✅ plugin via repo settings, or vendored | ✅ vendored or `~/.agents/skills`; agent plugins (preview) | ✅ `~/.agents/skills` or vendored |
| Kickoff routing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (judgment skills + catalog; fewer procedure tools) |
| Agents (`toolkit-scout`, `doc-*`) | ✅ | ⚠️ follows the agent prompt in-session | ✅ | ✅ | ✅ vendored to `.github/agents/` | ⚠️ follows the agent prompt in-session |
| SessionStart hook | ✅ | — | ✅ when the runtime exposes `PLUGIN_ROOT`, else a silent no-op; ✅ vendored | ✅ vendored to `.github/hooks/` | not verified | — |
| Harvest `Stop` reminder | ✅ | — | — | — | — | — |
| Upstream plugin profile | ✅ | ✅ (installed in the app) | ✅ skills, agents, hooks, MCP; ⚠️ Claude slash commands don't load | ✅ via repo settings | partial | skills only (copy them) |

✅ verified or documented · ⚠️ works with a fallback · — not applicable

**Verified here:** every toolkit plugin passes `claude plugin validate`, installs and enables in Claude Code 2.1.316, and a headless Claude Code run loaded all toolkit skills and received the SessionStart context. Sample upstream profile plugins (including `url`/`git-subdir` sources and `document-skills`) installed successfully. The Copilot formats (manifest lookup order, `hooks` path, hook schema, `.github/copilot/settings.json` keys) follow GitHub's Copilot CLI reference and the layout of GitHub's own `copilot-plugins` and `awesome-copilot` marketplaces. I could not run the Copilot CLI or reach the VS Code docs from the build environment, so the VS Code column relies on the shared Agent Skills locations and should be confirmed on first use.

## Setting up each client

### Claude Code
`python3 scripts/toolkit.py install --target claude` (or `/plugin marketplace add gimarais/ai-toolkit`, then `/plugin install kickoff@ai-toolkit`). Skills appear as `kickoff:kickoff`, `engineering-craft:reviewing-code`, etc.

### Claude app (claude.ai, desktop, mobile)
The app syncs skills from your account, not from git. Upload changed skills from `plugins/*/skills/` through the app's skill settings or the `propose_skills` flow at the end of a harvest. The app's own built-ins (`deep-research`, `docs`, `tutor`…) are listed in `toolkit.json` → `app_builtins`; kickoff only routes to them there.

### GitHub Copilot CLI
`python3 scripts/toolkit.py install --target copilot`, or:

```bash
copilot plugin marketplace add gimarais/ai-toolkit
```

```bash
copilot plugin install kickoff@ai-toolkit
```

Copilot reads the same marketplace format, so the upstream Anthropic marketplaces work too (`copilot plugin marketplace add anthropics/claude-plugins-official`). Plugin slash commands written for Claude Code are not loaded; kickoff falls back to the plugin's agents or the command file.

### GitHub Copilot cloud agent (and teammates)
Run `toolkit.py adopt <repo>` (or the `toolkit-adopt` skill) and commit the result. `.github/copilot/settings.json` declares the marketplace and enabled plugins; the cloud agent and Copilot CLI read it, scoped to that repository. Use `--mode vendor --hooks --github-agents` to commit the files themselves instead.

### GitHub Copilot in VS Code
Fastest: `toolkit.py install --target skills --skills-dir ~/.copilot/skills` (user-wide), or `adopt --mode vendor` (per repo, committed). VS Code also has agent plugins in preview; add `gimarais/ai-toolkit` as a plugin marketplace in its agent-plugin settings (check the VS Code docs for the current setting name).

### Codex, Cursor, Gemini CLI and other Agent Skills clients
`toolkit.py install --target skills` links every toolkit skill into `~/.agents/skills` (add `--skills-dir` for client-specific folders). `AGENTS.md` in adopted repos tells them to start with kickoff.

## Naming differences kickoff handles

| Concept | Claude Code | Copilot |
|---|---|---|
| Skill invocation | `Skill` tool, `<plugin>:<skill>` | automatic by description, or `/<skill>` |
| Subagent | `Agent` tool, `subagent_type: "<plugin>:<agent>"` | `agent` / `runSubagent` tool |
| Read-only tools | `Read`, `Grep`, `Glob` | `read`, `search` |
| Hook events | `SessionStart`, `Stop`, `PreToolUse` | `sessionStart`, `agentStop`, `preToolUse` |
| Plugin root in hooks | `${CLAUDE_PLUGIN_ROOT}` | `${PLUGIN_ROOT}` |
| Repo plugin settings | `.claude/settings.json` | `.github/copilot/settings.json` |
| Project instructions | `CLAUDE.md` (imports `AGENTS.md`) | `AGENTS.md`, `.github/copilot-instructions.md` |
