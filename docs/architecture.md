# Architecture

## Goals

1. **Clone anywhere, same experience.** One command sets up a device; the same skills, agents and hooks appear in Claude Code, GitHub Copilot and other Agent Skills clients.
2. **Tool selection, not tool hoarding.** Hundreds of skills and plugins exist; listings get truncated and the right one rarely triggers by itself. Kickoff routes explicitly.
3. **Grow from use.** Every task ends in a harvest that captures reusable work. Gaps are either filled from the catalog of existing plugins or built, and the result is written back here so every device and project gets it.

## Pieces

```
toolkit.json ───────────────┐ single source of truth
                            ▼
scripts/toolkit.py build ──▶ plugins/*/.claude-plugin/plugin.json   (Claude Code manifest)
                         ──▶ plugins/*/plugin.json                  (Copilot manifest, read first by Copilot)
                         ──▶ .claude-plugin/marketplace.json  ═  .github/plugin/marketplace.json
                         ──▶ README tables, plugin READMEs, own rows of catalog.tsv
scripts/toolkit.py catalog ─▶ catalog/index.json, catalog/CATALOG.md,
                              plugins/kickoff/skills/kickoff/references/catalog.tsv
```

### Toolkit plugins

| Plugin | Role |
|---|---|
| `kickoff` | The router (`kickoff`), the growth loop (`harvest`), project adoption (`toolkit-adopt`), the catalog search agent (`toolkit-scout`), and hooks: SessionStart context in both clients, plus a Claude `Stop` reminder when a route ran without a harvest |
| `engineering-craft`, `thinking-tools`, `communication-and-leadership` | Judgment skills: how to think about a kind of task. Kickoff pairs each with a procedure tool |
| `codemap` | The repo map: SQLite index + CLI + single-tool MCP server, `codemap` skill (navigation ladder), `code-navigator` agent, session hook that keeps the index warm. See [codemap.md](codemap.md). Also `codemap review` + the `change-review` skill + the `change-map` GitHub Action for structural PR review. See [change-review.md](change-review.md) |
| `doc-coauthor` | A complete procedure: coordinator skill + three isolated sub-agents |

### Upstream profile

`toolkit.json` → `upstream.profile` names the Anthropic, GitHub and partner plugins you use, as `plugin@marketplace`. They are installed from their own marketplaces rather than copied, which keeps them current, keeps their licenses with them, and avoids redistributing proprietary ones (`claude-security`, `document-skills`).

### Catalog

`toolkit.py catalog` shallow-clones each marketplace in `upstream.marketplaces`, reads its `marketplace.json`, and inventories every plugin's skills, agents, commands, hooks and MCP servers (externally hosted plugins are inventoried when they are in the profile, or with `--deep`). Each row is tagged `own` / `active` / `available` / `app`. A weekly workflow (`.github/workflows/catalog-refresh.yml`) opens a PR when upstream changes, so new plugins become discoverable automatically.

The kickoff skill carries the TSV inside its own folder, so it is available wherever the plugin is installed or vendored, including Copilot cloud agent sessions in other repos.

## The loop

```
kickoff ─ classify ─ load judgment ─ availability check ─┬─ loaded ───────────────▶ run
                                                         ├─ in catalog (active) ──▶ say install line, run with judgment alone
                                                         ├─ in catalog (available)▶ recommend plugin
                                                         └─ nothing ──────────────▶ gap noted
run ─▶ verify ─▶ harvest ─┬─ procedure/correction ─▶ skill  ─┐
                          ├─ delegable work ───────▶ agent  ─┤  toolkit checkout? ─ yes ─▶ plugins/<bundle>/…  ─▶ build, validate, commit, push ─▶ sync everywhere
                          ├─ mechanical rule ──────▶ hook   ─┤                    └ no ──▶ project .claude/…  ─▶ later: toolkit.py promote
                          ├─ existing plugin fits ─▶ route + profile entry
                          └─ unfilled ─────────────▶ gaps.md
```

## Design decisions

- **Skills are the portable unit.** Agent Skills (`SKILL.md` with `name` + `description`) load in Claude Code, the Claude app, Copilot (CLI, cloud, VS Code), Codex, Cursor and Gemini CLI. Anything that must work everywhere is a skill; agents, hooks and commands are enhancements where supported.
- **The doc co-author coordinator is a skill, not an agent**, because Claude subagents cannot spawn subagents. A skill runs in the main session, which can always delegate.
- **Agents carry no `tools` or `model`** by default. Tool ids differ between Claude (`Read`, `Grep`, `Bash`) and Copilot (`read`, `search`, `execute`), and Copilot model lists break Claude. Restrictions are stated in the prompt.
- **Two hook files per plugin.** Both clients default to `hooks/hooks.json`, but the formats differ. Claude reads its own format there; the Copilot manifest points at `hooks/copilot-hooks.json`. One Python script serves both via `--format`.
- **Two manifests per plugin.** Copilot checks a root `plugin.json` before `.claude-plugin/plugin.json`, so each client gets the manifest written for it.
- **Repo adoption is declarative.** `extraKnownMarketplaces` + `enabledPlugins` in `.claude/settings.json` and `.github/copilot/settings.json` make the plugins auto-install for every collaborator in Claude Code, Copilot CLI and the Copilot cloud agent, scoped to that repo.
- **Token cost is a first-class metric.** Navigation goes through codemap; MCP servers expose one tool; `audit` reports the always-on cost of every bundle; harvest prunes as well as adds.
- **User level first.** Personal tooling installs once per device at user level (where Copilot and Claude now look for it); repositories get declarative plugin settings, not copies. `doctor` finds and removes copies that shadow the user-level versions. See [maintenance.md](maintenance.md).
- **Stdlib Python only.** `toolkit.py` and the hooks run on any machine with Python 3.9+, including Windows, with nothing to `pip install`.
