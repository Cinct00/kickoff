# codemap

Token-efficient repository map: a SQLite index of symbols, imports, references and packages with a ranked repo map, search, outlines, exact symbol source, refs/callers, dependency and change-impact queries. CLI + single-tool MCP server; ~96% fewer tokens than grep-and-read.

Part of [ai-toolkit](../../README.md).

<!-- BEGIN GENERATED:install -->
## Install

Claude Code:

```
/plugin marketplace add gimarais/ai-toolkit
/plugin install codemap@ai-toolkit
```

GitHub Copilot CLI:

```bash
copilot plugin marketplace add gimarais/ai-toolkit
copilot plugin install codemap@ai-toolkit
```

Any other Agent Skills client: copy or link `skills/*` into `~/.agents/skills/` (or run `python3 scripts/toolkit.py install --target skills` from the toolkit).

## Contents

| Skill | Description |
|---|---|
| [`change-review`](skills/change-review/SKILL.md) | Review a pull request, branch or local diff from its structural change map instead of a raw diff: symbol-level changes, a risk-ranked review order, callers outside the diff that a change may break, affected and missing… |
| [`codemap`](skills/codemap/SKILL.md) | Navigate a codebase through its indexed map instead of grepping and reading whole files: overview, ranked repo map, symbol search, definitions, outlines, exact symbol source, references, callers, dependencies, change im… |

| Agent | Description |
|---|---|
| [`code-navigator`](agents/code-navigator.agent.md) | Read-only code navigator. Answers structural questions about a repository (where is X implemented, how does a flow work end to end, what calls Y, what would changing Z affect, which tests cover it) using the codemap ind… |

Hooks: Claude Code SessionStart (`hooks/hooks.json`); Copilot sessionStart (`hooks/copilot-hooks.json`).
<!-- END GENERATED:install -->
