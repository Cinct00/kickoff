# codemap

A token-efficient, queryable map of a repository, so agents navigate code through an index instead of grepping and reading whole files. Stdlib Python, no services, works in Claude Code, GitHub Copilot (CLI, cloud agent, VS Code) and any client that can run a command or an MCP server.

## Results

Measured with [`tests/bench_codemap.py`](../tests/bench_codemap.py) on six public repositories in six languages (tokens ≈ characters / 4 on both sides).

**Locate and understand a symbol.** Baseline: `git grep -n -w NAME` (capped at 250 lines), read the defining file, read the two files that use it most. codemap: `def` + `refs` + `show`.

| Repo | Symbol | Baseline | codemap | Saved |
|---|---|---:|---:|---:|
| requests (Python) | `Session` | 48,599 | 2,557 | 95% |
| requests | `resolve_redirects` | 52,029 | 1,424 | 97% |
| hono (TypeScript) | `compose` | 9,720 | 486 | 95% |
| hono | `Context` | 17,311 | 2,436 | 86% |
| cobra (Go) | `ExecuteC` | 65,252 | 640 | 99% |
| cobra | `Command` | 69,391 | 2,603 | 96% |
| gson (Java) | `TypeAdapterFactory` | 20,428 | 1,085 | 95% |
| gson | `JsonReader` | 63,644 | 3,975 | 94% |
| Newtonsoft.Json (C#) | `JsonSerializerInternalReader` | 46,282 | 2,748 | 94% |
| Newtonsoft.Json | `JsonConvert` | 134,299 | 3,300 | 98% |
| ripgrep (Rust) | `Searcher` | 52,411 | 667 | 99% |
| ripgrep | `search_slice` | 18,330 | 500 | 97% |
| **total** | | **597,696** | **22,421** | **96%** |

**Orient in a new repo.** Baseline: `git ls-files` + README + the three most central files. codemap: `overview` + `map --budget 1024`.

| Repo | Files | Baseline | codemap | Saved | Full index | Index size |
|---|---:|---:|---:|---:|---:|---:|
| requests | 130 | 13,656 | 1,232 | 91% | 0.3 s | 0.8 MB |
| hono | 584 | 37,339 | 1,238 | 97% | 1.9 s | 2.7 MB |
| cobra | 66 | 28,494 | 1,186 | 96% | 0.3 s | 0.7 MB |
| gson | 313 | 20,397 | 1,300 | 94% | 1.2 s | 4.2 MB |
| Newtonsoft.Json | 1,176 | 47,451 | 1,305 | 97% | 7.2 s | 23 MB |
| ripgrep | 226 | 48,781 | 1,232 | 97% | 2.8 s | 2.4 MB |

After the first build, a query that also checks for changes takes about 0.15 s; after editing a file in the 1,176-file C# repo, the next query picked the change up in 0.21 s. `codemap savings` keeps a running total for your own work.

Run it yourself: `python3 tests/bench_codemap.py path/to/repo:SymbolName …`.

## Why this design

| Option | Verdict |
|---|---|
| **In-memory DB in Docker** (Redis, Memgraph, Neo4j…) | Rejected. Needs Docker and a running service, loses state when it stops, can't run in the Copilot cloud agent, and the data is small enough that the server adds nothing but startup time. |
| **Graph database** | Rejected for the same reasons; the queries agents need (definitions, references, one or two hops of dependencies, PageRank) are a few indexed joins in SQLite. |
| **SQLite file in the user cache** ✅ | In-process, zero install (it's in Python's stdlib, with FTS5 full-text search), persistent across sessions, incremental, concurrent readers (WAL), and SQL as an escape hatch. Kept outside the repo so it never gets committed. |
| **Language servers / SCIP indexers** | Most precise, but one heavy toolchain per language, slow to start, and they need the project to build. Good complement, wrong default. |
| **tree-sitter** | The best general parser, and what Aider's repo map uses, but it needs native wheels per platform. For the languages that matter most here (C#, Rust), codemap has its own structural parsers that match tree-sitter to within 0.1–0.4%, and tree-sitter serves as the test oracle (`tests/eval_extraction.py`). |
| **Embeddings / vector search** | Needs a model or API, costs money and setup, and returns fuzzy chunks. Agents mostly need exact structure, so it isn't included. |

The map itself follows the approach Aider documented for repo maps: extract definitions and references, build a file graph weighted by how distinctive each referenced name is, rank it with PageRank (personalised to the files you are working on), and render only signatures, choosing as many as fit a token budget.

Tools such as Graphify build richer knowledge graphs of a codebase. codemap is deliberately narrow, deterministic and local: you can read every line of what gets indexed, nothing leaves the machine, and the output formats are tuned for tokens rather than for humans.

## Accuracy by language

| Language | Extractor | Measured against tree-sitter |
|---|---|---|
| **C#** | structural parser (`lang_cs.py`): real lexer (verbatim, raw `"""`, interpolated strings; keeps the first `#if` branch) + scope-aware member walker | 25,866 declarations in Newtonsoft.Json, Polly and eShop: **99.9% recall, 100.0% precision, 99.1% correct parent** (was 63.7% / 88.4% / 82.6% with patterns) |
| **Rust** | structural parser (`lang_rs.py`): lexer (nested comments, raw/byte strings, char vs lifetime) + item walker | 11,625 items in ripgrep, axum and serde: **100.0% recall, 99.6% precision, 100% end lines and parents** (was 94.7% / 95.2%) |
| **Python** | the stdlib `ast` parser | exact by construction |
| TS/JS, Go, Java, Kotlin, Scala, C/C++, PHP, Ruby, Swift | comment/string-masking lexer + definition patterns | spot-checked on real repos, not yet measured |

What each structural parser extracts:
- **C#**: namespaces (block and file-scoped), classes, structs (incl. `ref struct`), interfaces, enums, records (with primary constructors), and delegates. Members: methods (generic, expression-bodied, bodyless interface/partial/abstract, explicit interface implementations), constructors and destructors, properties, indexers, events, fields and consts (multi-declarator), and operators. Also XML-doc summaries and base lists.
- **Rust**: functions and methods (const/async/unsafe/extern; nested fns), structs, enums, unions, traits (with associated types and consts), `impl` blocks (trait impls recorded as the type's base, so `hierarchy Trait` lists implementors), type aliases, consts and statics, inline and file modules, and `macro_rules!` (template bodies are never mistaken for definitions). Also `///` docs through attributes.

Measure it yourself with `tests/eval_extraction.py` (needs `pip install tree-sitter tree-sitter-c-sharp tree-sitter-rust` in a venv; tree-sitter is only the oracle, codemap stays stdlib-only). `--legacy` scores the old pattern extractor for comparison.

### Dependency graph quality

- **C#** resolves names the way the compiler does. Each file links to the files that define a type it actually uses, searched through its `using` namespaces, its own namespace and that namespace's parents, plus project-wide `global using` lines and MSBuild `<Using Include>` items (per `.csproj`, or `Directory.Build.props`). On Newtonsoft.Json this took import edges that point at a file defining a used type from **7.4% to 100%**. Coverage of real type dependencies rose from 7.4% to 65–77% (most of the rest are names that collide with a type but mean something else).
- **Rust** expands `use` trees (`use a::{b, c::{d, e}}`), finds each crate's root (`lib.rs`/`main.rs`, wherever Cargo puts it), follows `mod x;` declarations, and resolves `super::` inside inline modules (`mod tests { use super::*; }`) to the file itself. Internal imports that resolve to a file: ripgrep 46% → 96%, axum 71% → 99.5%, serde 81% → 100%.

## How it works

```
git ls-files ──▶ changed? (size, mtime, then sha1) ──▶ extract ──▶ SQLite (user cache)
                                                        │
          Python: stdlib ast (exact)                    ├─ files     path, lang, lines, tokens, is_test, rank
          14 other languages: comment/string-masking    ├─ symbols   name, qualname, kind, lines, signature, doc, parent
          lexer + definition/import patterns +          ├─ idents    identifier occurrences per file (references)
          brace/indent extents                          ├─ imports   raw → resolved file or external package
          Markdown: headings + relative links           ├─ bases     inheritance
                                                        ├─ deps      declared packages from manifests
                                                        ├─ edges     weighted file graph → PageRank
                                                        └─ FTS5      camelCase/snake_case-aware symbol search
```

- **Languages**: C# and Rust (structural parsers), Python (`ast`), and TypeScript/JavaScript, Go, Java, Kotlin, Scala, C, C++, PHP, Ruby, Swift and Markdown (patterns).
- **Import resolution**: Python packages and relative imports; tsconfig/jsconfig `paths` and `baseUrl`; npm workspaces; Go modules (multi-module); Java/Kotlin packages and wildcards; C# compiler-style scoping (usings, own and parent namespaces, global usings, MSBuild usings); Rust use-trees, crate roots, `mod`, `self`/`super` (incl. inline modules) and workspace crates; C/C++ includes; PHP namespaces; Ruby `require_relative`; Swift packages; Markdown links.
- **Manifests**: package.json, requirements*.txt, pyproject.toml (PEP 621 and Poetry), go.mod, Cargo.toml, *.csproj / Directory.Packages.props, pom.xml, build.gradle(.kts), Gemfile, composer.json.
- **Freshness**: every query re-checks the working tree, throttled to once every 3 s, and only re-parses changed files. Ranks are recomputed when files are added or removed, or at most every 10 minutes during a session. A session-start hook refreshes the index in the background.
- **References** are name-based (like tags-based repo maps), then made precise: `refs` marks a use as confirmed when the file imports the defining file (or shares its package in Go, Java, C#, Kotlin, Scala and Swift), and lists other same-name matches separately as "name-only".

## Commands

| Command | Returns |
|---|---|
| `overview` | languages, dirs, entry points, central files, top packages (~250 tokens) |
| `map [--budget N] [--focus PATH\|SYMBOL]` | ranked signatures grouped by file, fitted to the budget |
| `tree [PATH] [--depth N]`, `files PATTERN` | directory summary with token sizes; file listing |
| `find TERMS [--kind K] [--path P]` | symbol search, exact and type matches first |
| `def NAME` | definition(s), signature, doc, bases, subtypes count |
| `outline PATH` | imports and every symbol with line ranges |
| `show SYMBOL \| PATH:A-B [-C N] [-n]` | exact source of one symbol or range |
| `refs NAME`, `callers NAME`, `callees SYMBOL` | uses grouped by file and enclosing function |
| `deps PATH [--depth N]`, `impact PATH\|SYMBOL`, `tests PATH\|SYMBOL` | dependencies, dependents by distance, tests to run |
| `hierarchy TYPE`, `packages [NAME]`, `cycles` | inheritance tree, declared vs imported packages, import cycles |
| `schema`, `sql "SELECT …"` | read-only SQL over the index |
| `index [--full]`, `status`, `savings`, `mcp` | maintenance, stats, the MCP server |

Global options: `--repo PATH`, `--db PATH`, `--no-refresh`. Environment: `CODEMAP_CACHE` (index directory), `CODEMAP_DB`, `CODEMAP_REFRESH=0`, `CODEMAP_HOOK=0`, `CODEMAP_MAX_FILE_BYTES`.

## How agents reach it

| Route | Where it comes from |
|---|---|
| MCP tool `codemap(cmd)` | plugin `.mcp.json` (Claude Code), `copilot-mcp.json` (Copilot plugin), `~/.copilot/mcp-config.json` (user-level install), project `.mcp.json` (vendored adoption) |
| `codemap` on the shell | `~/.local/bin/codemap` from `toolkit.py install` |
| `python3 …/scripts/codemap.py` | always works from the plugin folder |
| `codemap` skill | teaches the cheapest-first ladder; `code-navigator` agent runs it in isolation |

The MCP server exposes **one** tool with a single string parameter. Its schema is about 150 tokens, versus 1,500+ for a tool per command, and that cost is paid on every request.

## Limits

- C#, Rust and Python are parsed structurally (see the accuracy table). For C#, only the first branch of each `#if` is indexed, and code generated by source generators is invisible. In Rust, items produced by macros are invisible, as they are to any non-compiling tool.
- The other languages use pattern-based extraction, checked on real repos but not measured. Unusual syntax (heavily nested generics, JS regex literals) can be missed; `show PATH:A-B` and grep remain available.
- References are by name. Common method names (`get`, `run`) are down-weighted in ranking, and `refs` separates confirmed from name-only matches, but dynamic dispatch and reflection are invisible.
- Strings, comments and config values aren't indexed for search. Use grep for those.
