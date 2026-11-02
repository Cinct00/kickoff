# AGENTS.md

Instructions for any AI agent (Claude, Copilot, Codex, Cursor, Gemini…) working **on this repository**, the ai-toolkit itself.

## What this repo is

A plugin marketplace and skills library that must work identically in Claude Code and GitHub Copilot, and degrade gracefully everywhere else. `toolkit.json` is the single source of truth; most JSON in the tree is generated from it.

## Layout

- `toolkit.json`: toolkit plugins, bundles, upstream marketplaces, the user's plugin profile, Claude-app built-ins.
- `plugins/<name>/`: one plugin each. `skills/<skill>/SKILL.md`, `agents/<agent>.agent.md`, `hooks/hooks.json` (Claude) + `hooks/copilot-hooks.json` (Copilot).
- `plugins/<name>/.claude-plugin/plugin.json` and `plugins/<name>/plugin.json`: **generated** (Claude and Copilot manifests).
- `.claude-plugin/marketplace.json` and `.github/plugin/marketplace.json`: **generated**, identical.
- `catalog/`: **generated** by `toolkit.py catalog` (index.json, CATALOG.md) plus the hand-kept `gaps.md` ledger. The kickoff skill's `references/catalog.tsv` is generated too.
- `scripts/toolkit.py`: the CLI (stdlib-only Python 3.9+): build, validate, catalog, install, adopt, promote, doctor, audit, sync.
- `plugins/codemap/scripts/`: the codemap engine (`codemap_core/`), also stdlib-only.
- `tests/`: unit tests (`python3 -m unittest discover -s tests`) and the codemap token benchmark.

## Working rules

- After any change: `python3 scripts/toolkit.py build && python3 scripts/toolkit.py validate`, then the unit tests. CI runs all three plus `audit --strict`.
- Navigate this repo with `codemap` too (`python3 plugins/codemap/scripts/codemap.py overview`).
- Never hand-edit generated files, including the README sections between `BEGIN GENERATED` markers.
- Keep artefacts portable (see the "Portable format rules" in `plugins/kickoff/skills/harvest/SKILL.md`): skill frontmatter is only `name` + `description`; agents are `<name>.agent.md` with no `tools`/`model` unless essential; hooks ship in both formats.
- Never vendor third-party content with a proprietary license. Reference the plugin in `toolkit.json` → `upstream.profile` instead.
- A new task type that an existing plugin covers is a new row in the kickoff routing table, not a new skill.
- Use the `kickoff` skill for substantial work here too, and finish with `harvest`.
