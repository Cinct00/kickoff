# kickoff

The router. Classifies a task, loads the right skills, agents and plugin commands on whatever platform you are on, checks the catalog for gaps and existing plugins that fill them, then harvests reusable work back into the toolkit so it grows.

Part of [ai-toolkit](../../README.md).

<!-- BEGIN GENERATED:install -->
## Install

Claude Code:

```
/plugin marketplace add Cinct00/ai-toolkit
/plugin install kickoff@kickoff
```

GitHub Copilot CLI:

```bash
copilot plugin marketplace add Cinct00/ai-toolkit
copilot plugin install kickoff@kickoff
```

Any other Agent Skills client: copy or link `skills/*` into `~/.agents/skills/` (or run `python3 scripts/toolkit.py install --target skills` from the toolkit).

## Contents

| Skill | Description |
|---|---|
| [`harvest`](skills/harvest/SKILL.md) | Turns reusable work from the current session into new or improved skills, agents, hooks and kickoff routes, written in a portable format that works in Claude Code, GitHub Copilot and other Agent Skills clients, and reco… |
| [`kickoff`](skills/kickoff/SKILL.md) | Routes a task to the right skills, agents and plugin commands on whatever platform you are running on (Claude Code, Claude app, GitHub Copilot, others), checks the toolkit catalog for gaps and for existing plugins that… |
| [`toolkit-adopt`](skills/toolkit-adopt/SKILL.md) | Brings the AI toolkit into another repository so kickoff, the judgment skills and the right Anthropic, GitHub and partner plugins work there for every collaborator and in GitHub Copilot (CLI, cloud agent, VS Code) as we… |

| Agent | Description |
|---|---|
| [`toolkit-scout`](agents/toolkit-scout.agent.md) | Read-only scout that finds the best route for a task across everything this toolkit knows about: installed skills, agents and commands plus the catalog of Anthropic, GitHub and partner plugins. Returns a ranked route, i… |

Hooks: Claude Code SessionStart, Stop (`hooks/hooks.json`); Copilot sessionStart (`hooks/copilot-hooks.json`).
<!-- END GENERATED:install -->
