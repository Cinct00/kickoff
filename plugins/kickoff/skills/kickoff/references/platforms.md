# Platform reference

How to invoke toolkit and plugin tools on each platform. Kickoff names tools bare
(`reviewing-code`, `feature-dev`); resolve them here.

## Telling platforms apart

| You see | You are in |
|---|---|
| `Skill` tool and `Agent` tool (with `subagent_type`), `Bash`, `Edit` | Claude Code (terminal, IDE, desktop, web) |
| `Skill` tool plus `Artifact`, `propose_skills` or `SendUserFile`, often no repo | Claude app (claude.ai, desktop, mobile) |
| `runSubagent` / `agent` tool, tools named `read`, `edit`, `search`, `execute`; `.github/copilot-instructions.md` or `AGENTS.md` in context | GitHub Copilot (VS Code agent mode, Copilot CLI, or Copilot cloud agent) |
| Skills listed by name and path, no delegation tool | Another Agent Skills client (Codex, Cursor, Gemini CLI, …) |

## Invoking tools

| Tool kind | Claude Code | Claude app | GitHub Copilot | Other clients |
|---|---|---|---|---|
| Toolkit skill | `Skill` with `<plugin>:<name>` (e.g. `engineering-craft:reviewing-code`) or bare name if installed in `~/.claude/skills` | `Skill` with `anthropic-skills:<name>` or the synced name | Loads automatically from its description; to force it, type `/<name>` or read its `SKILL.md` | Read the `SKILL.md` from the skills directory |
| Plugin skill | `Skill` with `<plugin>:<skill>` | `Skill` with `<plugin>:<skill>` | Same as toolkit skill | Same |
| Plugin agent | `Agent` with `subagent_type: "<plugin>:<agent>"` | `Agent` if offered, else follow the agent's prompt yourself | `agent`/`runSubagent` with the agent name | Follow the agent file's instructions in a fresh, scoped pass |
| Plugin command (`/plugin:command`) | Type or invoke `/<plugin>:<command> <args>` | Usually exposed as a skill of the same name | Not loaded from Claude plugins. If the plugin is installed, read `commands/<command>.md` in its folder and follow it; otherwise use its agents or the judgment skill alone | Same as Copilot |
| Hooks | Run automatically once the plugin is installed | Not applicable | Run automatically (Copilot CLI and cloud agent read plugin hooks, `.github/hooks/*.json` and `.claude/settings.json`) | Not applicable |

`[[name]]` links inside skills always mean "the skill called `name`", resolved with the row above.

## Installing a missing plugin (only with the user's yes)

| Client | Add marketplace (once) | Install |
|---|---|---|
| Claude Code | `claude plugin marketplace add <owner/repo>` or `/plugin marketplace add <owner/repo>` | `claude plugin install <plugin>@<marketplace>` |
| Copilot CLI | `copilot plugin marketplace add <owner/repo>` | `copilot plugin install <plugin>@<marketplace>` |
| Copilot cloud agent / whole team | add both entries to the repo's `.github/copilot/settings.json` (`extraKnownMarketplaces`, `enabledPlugins`); `toolkit-adopt` does this | — |
| Claude Code, whole team | same keys in the repo's `.claude/settings.json` | — |
| VS Code / Codex / Cursor | copy the plugin's `skills/<name>/` folder into the repo's `.claude/skills/` or `.github/skills/` (or `~/.agents/skills/` for every repo) | — |

Marketplace names → repos: `claude-plugins-official` = `anthropics/claude-plugins-official`,
`knowledge-work-plugins` = `anthropics/knowledge-work-plugins`, `anthropic-agent-skills` = `anthropics/skills`,
`claude-for-financial-services` = `anthropics/financial-services-plugins`, `claude-for-legal` = `anthropics/claude-for-legal`,
`copilot-plugins` = `github/copilot-plugins`, `awesome-copilot` = `github/awesome-copilot` (built into Copilot CLI),
`ai-toolkit` = `Cinct00/ai-toolkit` (this toolkit).

## Where new artefacts go

| Situation | Skills | Agents | Hooks |
|---|---|---|---|
| Toolkit checkout available (`$AI_TOOLKIT_HOME`, `~/.config/ai-toolkit/home`, or `~/.ai-toolkit`) and the artefact is cross-project | `plugins/<bundle>/skills/<name>/SKILL.md` | `plugins/<bundle>/agents/<name>.agent.md` | `plugins/<bundle>/hooks/hooks.json` **and** `hooks/copilot-hooks.json` |
| Project-specific, any client | `.claude/skills/<name>/SKILL.md` (read by Claude Code and Copilot) | `.claude/agents/<name>.md` | `.claude/settings.json` (Claude; Copilot CLI reads it too) or `.github/hooks/<name>.json` (Copilot format) |
| Claude app, no repo | `propose_skills` | write the file and send it with `SendUserFile` | write the rule file and send it |
