# Adding and changing components

Most additions happen through **harvest** at the end of a kickoff run. This page is the manual version.

## A skill

1. Pick the plugin: engineering method → `engineering-craft`; reasoning → `thinking-tools`; people and writing → `communication-and-leadership`; personal → `life-and-career`; routing/toolkit mechanics → `kickoff`.
2. Create `plugins/<plugin>/skills/<name>/SKILL.md`:
   ```markdown
   ---
   name: <name>              # = folder name, lowercase-hyphenated, ≤ 64 chars
   description: <what it does and when to use it, with trigger phrases; ≤ 1024 chars>
   ---
   ```
   Keep the body under ~500 lines; put detail in `references/`. Link other skills as `[[name]]`.
3. If it introduces a new kind of task, add a row to the routing table in `plugins/kickoff/skills/kickoff/SKILL.md`.
4. `python3 scripts/toolkit.py build && python3 scripts/toolkit.py validate`.

Already wrote it inside a project? `python3 scripts/toolkit.py promote path/to/.claude/skills/<name> --plugin <plugin>`.

## An agent

`plugins/<plugin>/agents/<name>.agent.md` with frontmatter `name` (= file stem) and `description` (when to delegate). Leave out `tools` and `model` unless essential; state restrictions in the prompt.

## A hook

Write one script in `plugins/<plugin>/hooks/` that accepts `--format claude|copilot`, then register it in both:

- `hooks/hooks.json` (Claude): PascalCase events, `"command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/<script>.py\" --format claude"`.
- `hooks/copilot-hooks.json` (Copilot): `"version": 1`, camelCase events, a `bash` command that resolves `${PLUGIN_ROOT}` and prints `{}` when it can't (see the kickoff example), and a `powershell` equivalent.

Hooks must fail open: catch everything and exit 0 unless blocking is the point.

## A new toolkit plugin

Create `plugins/<name>/`, add an entry under `plugins` in `toolkit.json` (description, category, keywords), optionally add it to a bundle, then build. Manifests and READMEs are generated.

## An upstream plugin or marketplace

- Use a plugin day to day: add `plugin@marketplace` to `toolkit.json` → `upstream.profile`.
- Track a new marketplace: add `{name, repo, publisher, trust}` to `upstream.marketplaces`, then `python3 scripts/toolkit.py catalog`. `name` must match the `name` in that repo's `marketplace.json`.

Never copy third-party skills into `plugins/` unless their license allows redistribution; `validate` rejects files with proprietary markers.
