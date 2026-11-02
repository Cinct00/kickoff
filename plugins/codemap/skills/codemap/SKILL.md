---
name: codemap
description: "Navigate a codebase through its indexed map instead of grepping and reading whole files: overview, ranked repo map, symbol search, definitions, outlines, exact symbol source, references, callers, dependencies, change impact and affected tests, at roughly 5% of the tokens. Use whenever you need to find where something lives, understand how code fits together, trace who calls what, or plan a change in any repository, before reaching for grep or opening files."
---

# Codemap

A SQLite index of the repository's symbols, imports, references and declared packages, kept fresh automatically. Every answer is compact text, grouped by file, with line numbers you can act on. Measured on six real repos, locating and understanding a symbol cost 96% fewer tokens than grep-and-read.

## Running it

Use the first that works:

1. The `codemap` MCP tool: `codemap(cmd="refs UserService")`.
2. `codemap <cmd>` on the shell (installed on PATH by the toolkit installer).
3. `python3 <this skill's folder>/../../scripts/codemap.py <cmd>`.

The index lives in your user cache, not the repo. The first query builds it (seconds; about 8 s for a 1,000-file C# solution). After that, each query re-checks changed files in ~0.2 s, so you never need to reindex after editing.

## The ladder: cheapest step that answers the question

| Need | Command | Instead of |
|---|---|---|
| What is this repo? | `overview` (~250 tokens) | README + directory listing + opening files |
| What matters, structurally? | `map` (1k-token ranked signatures); `map --focus <file or symbol>` for the neighbourhood of what you're working on; `--budget 3000` for a bigger picture | reading central files |
| Where is X? | `find <terms>` (camelCase/snake_case aware), `def <Name>` | `grep -rn` |
| What's in this file? | `outline <path>` | reading the file |
| Show me X | `show <Name>`, `show Class.method`, `show path:120-180` | reading the file to find it |
| Who uses X? | `refs <Name>`; `callers <Name>` for function-level | grep + opening each hit |
| What does X use? | `callees <Symbol>`, `deps <path>` | reading imports by hand |
| What breaks if I change X? | `impact <path or Symbol>` lists dependents by distance and the tests to run | guessing |
| Type relationships | `hierarchy <Type>` | grepping `extends`/`implements` |
| Third-party packages | `packages`, `packages <name>` (declared vs actually imported) | reading manifests |
| What does this PR / branch change? | `review` (structural change map; see the `change-review` skill) | reading the raw diff |
| Anything else | `schema`, then `sql "SELECT …"` (read-only) | |

## Rules

- **Map before you read.** Start with `overview` or `map` in an unfamiliar repo, and `find`/`def` when you know a name. Read code with `show` (one symbol) or `outline` (one file), not by opening whole files.
- **Open a whole file only when you will edit most of it**, or after `outline` shows it is short (the header gives its size in tokens).
- **Before editing shared code, run `impact`** and include its test list in your verification.
- **Grep is still right** for string literals, log messages, config keys, comments and non-code files. If `find` says "no symbols match", fall back to grep.
- **Trust but verify** name-only matches: `refs` separates import-linked uses from "name-only matches (may be unrelated)".
- Keep outputs small: the default limits are deliberate; raise `--limit` only when you need the tail.
- `savings` reports tokens saved so far; mention it if the user asks about token usage.

## Delegating

For broad questions ("how does auth work end to end", "what would replacing X touch"), delegate to the `code-navigator` agent. It runs the ladder in its own context and returns a short answer with file:line references, keeping your context lean.
