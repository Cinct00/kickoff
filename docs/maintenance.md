# Keeping the toolkit alive

The toolkit is meant to grow from use and stay lean and current without anyone remembering to tend it. These loops keep it that way.

## The loops

| Loop | Trigger | What it does | Command |
|---|---|---|---|
| **Route** | every substantial task | kickoff picks tools, checks the catalog, logs gaps | `kickoff` skill |
| **Navigate** | every code question | codemap answers from the index; the index refreshes itself per query | `codemap …` |
| **Harvest** | end of every kickoff run (a Claude `Stop` hook reminds once) | captures procedures, corrections and gaps as skills, agents, hooks or routes; prunes one overlap or stale item | `harvest` skill |
| **Doctor** | session start, at most daily (one line only if something is wrong); on demand | checks installs on this device and shadowing in the current repo; `--fix` repairs the safe cases | `toolkit.py doctor [--repo] [--fix]` |
| **Audit** | on demand, and before releases | always-on token cost per bundle, oversized descriptions, overlapping skills, routes or profile plugins that no longer exist upstream, skills untouched for 180 days | `toolkit.py audit` |
| **Catalog refresh** | weekly CI workflow | rescans upstream marketplaces and opens a PR when new plugins appear | `toolkit.py catalog` |
| **Sync** | when you sit down at another device | `git pull` plus plugin updates | `toolkit.py sync` |

## User level vs repository level (the Copilot migration)

GitHub Copilot (CLI, cloud agent and VS Code) and Claude Code both load skills, agents, hooks and MCP servers from the **user level** for every repo on the device:

| | Copilot | Claude Code |
|---|---|---|
| Skills | `~/.copilot/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` (or plugins) |
| Agents | `~/.copilot/agents/<name>.agent.md` | `~/.claude/agents/<name>.md` (or plugins) |
| Hooks | `~/.copilot/hooks/*.json` | `~/.claude/settings.json` (or plugins) |
| MCP | `~/.copilot/mcp-config.json` | `claude mcp add --scope user` (or plugins) |

`toolkit.py install` writes exactly these. On Copilot it uses symlinks, so a `git pull` updates every device instantly. It records every path in `~/.config/kickoff/installed.json` so `doctor` can verify them later.

**Precedence matters.** A project-level skill with the same name **overrides** your personal one in Copilot, and agents go the other way. So a skill vendored into a repo months ago silently shadows the up-to-date version you installed at user level. It also costs extra listing tokens. To migrate a repo:

1. Install at user level on your device: `python3 ~/.kickoff/scripts/toolkit.py install`.
2. Check the repo: `python3 ~/.kickoff/scripts/toolkit.py doctor --repo path/to/repo`.
   - *duplicates the toolkit skill you already have at user level* → safe to delete; `--fix` does it.
   - *differs from the toolkit version* → stale or customized. Compare; `promote` it if the change is worth keeping, otherwise delete it.
3. If teammates or the Copilot cloud agent need the toolkit in that repo, use `adopt --mode plugins` (a few lines of settings that auto-install current versions) instead of vendored copies.

## Token budget

Every installed skill's name and description, every agent description and every MCP tool schema is sent on **every** request. `toolkit.py audit` prints the total per bundle:

```
bundle core  ~  860 tokens  (kickoff, codemap)
bundle dev   ~3,360 tokens  (+ engineering-craft, thinking-tools, doc-coauthor)
bundle full  ~4,070 tokens  (+ communication-and-leadership)
```

Install the smallest bundle that covers your work on each device (`install --bundle dev`). Keep descriptions under ~700 characters, and when harvest finds two overlapping skills, merge them instead of adding a third.

## Health checklist (monthly, 5 minutes)

```bash
cd ~/.kickoff && git pull
```

```bash
python3 scripts/toolkit.py doctor --fix
```

```bash
python3 scripts/toolkit.py audit
```

```bash
python3 scripts/toolkit.py catalog && python3 scripts/toolkit.py build && python3 scripts/toolkit.py validate
```

Then skim [`catalog/gaps.md`](../catalog/gaps.md) for open gaps and the catalog-refresh PRs for new plugins worth adding to your profile.
