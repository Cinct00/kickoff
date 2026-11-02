# codemap

A token-efficient, queryable map of a repository, so agents navigate code through an index instead of grepping and reading whole files. Stdlib Python, no services, works in Claude Code, GitHub Copilot (CLI, cloud agent, VS Code) and any client that can run a command or an MCP server.

## Results

Measured with [`tests/bench_codemap.py`](../tests/bench_codemap.py) on ten public repositories (Python, TypeScript, Go, Java, three C#, three Rust), with the structural C# and Rust parsers. Tokens are estimated at characters ÷ 4 on both sides.

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
| Newtonsoft.Json (C#) | `JsonSerializerInternalReader` | 46,282 | 2,806 | 94% |
| Newtonsoft.Json | `JsonConvert` | 134,299 | 5,679 | 96% |
| Polly (C#) | `ResiliencePipeline` | 34,898 | 2,437 | 93% |
| Polly | `RetryStrategyOptions` | 31,818 | 2,874 | 91% |
| eShop (C#) | `OrderingContext` | 3,416 | 1,628 | 52% |
| eShop | `BasketService` | 4,616 | 1,979 | 57% |
| ripgrep (Rust) | `Searcher` | 52,411 | 758 | 99% |
| ripgrep | `search_slice` | 18,330 | 502 | 97% |
| axum (Rust) | `Router` | 48,457 | 1,387 | 97% |
| axum | `IntoResponse` | 37,452 | 236 | 99% |
| serde (Rust) | `Deserializer` | 62,561 | 3,472 | 94% |
| serde | `Serialize` | 34,283 | 717 | 98% |
| **total** | | **855,197** | **39,681** | **95%** |

Where files are small (eShop's services are a few hundred lines), grep-and-read is already cheap and codemap saves about half. Its value there is structure (confirmed vs name-only references, enclosing members) more than tokens.

**Orient in a new repo.** Baseline: `git ls-files` + README + the three most central files. codemap: `overview` + `map --budget 1024`.

| Repo | Baseline | codemap | Saved | Full index |
|---|---:|---:|---:|---:|
| requests | 13,656 | 1,232 | 91% | 0.5 s |
| hono | 37,339 | 1,238 | 97% | 2.2 s |
| cobra | 28,494 | 1,186 | 96% | 0.3 s |
| gson | 20,397 | 1,300 | 94% | 1.2 s |
| Newtonsoft.Json | 42,395 | 1,301 | 97% | 5.3 s |
| Polly | 19,562 | 1,318 | 93% | 3.8 s |
| eShop | 16,535 | 1,344 | 92% | 1.0 s |
| ripgrep | 48,781 | 1,231 | 97% | 1.2 s |
| axum | 13,556 | 1,296 | 90% | 1.3 s |
| serde | 70,170 | 1,224 | 98% | 0.8 s |
| **total** | **310,885** | **12,670** | **96%** | |

After the first build, a query that also checks for changes takes about 0.15 s; after editing a file in a 1,176-file C# repo, the next query picked the change up in 0.21 s. `codemap savings` keeps a running total for your own work.

Run it yourself: `python3 tests/bench_codemap.py path/to/repo:SymbolName …`.

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

## Large repositories

Built and measured against [dotnet/roslyn](https://github.com/dotnet/roslyn) (35,451 files, 18,291 C#, about 64M tokens of C#). See the "Scale" numbers below.

- **Freshness without scanning.** In a git repo, each query asks git what changed: `git status`, commits since the last index (so pulls and branch switches are seen), and files that were dirty last time (so reverts are seen). It parses only those files, so the cost doesn't grow with repo size. Outside git, or for an explicit `index`, it does a full scan.
- **No whole-repo work inside a query.** An edited or new file is parsed and resolved right away. Global work (re-resolving every import, re-ranking) runs in a detached background `codemap index`, started after structural changes and at session start. Queries keep answering from the current index meanwhile.
- **Parallel, memory-bounded indexing.** Files are parsed on every CPU core, 1,000 at a time.
- **Bounded ranking.** Names defined in more than 20 files (e.g. `Create`, `Dispose`) add no ranking edges, and each file keeps its 40 strongest. On Roslyn this took ranking from 301 s to 39 s and the edge table from 17.4M rows to 0.68M.
- **Generated code and tests** are detected (by path, and by `<auto-generated>`, `@generated` or `DO NOT EDIT` headers). They stay searchable but are kept out of "central files" and the map, where on big repos they would otherwise dominate.

### Scale: measured on Roslyn (35,451 files)

| | Before the scale work | Now |
|---|---:|---:|
| Full index (first build, 4 cores) | over 6 min (import resolution 35 s + ranking 301 s alone) | **126 s** |
| Peak memory during a full index | 1.6 GB | **0.68 GB** |
| Index size | 1,229 MB | **512 MB** |
| Ranking edges stored | 17.4 M | **0.68 M** |
| Query with no changes (freshness check included) | 0.7 s spent just listing and stat-ing files | **0.17 s** |
| First query after editing / adding / deleting a file | full re-resolve + re-rank inside the query (minutes) | **1.1 s / 1.0 s / 0.27 s** |

Query latency on Roslyn: `find`, `def`, `outline`, `refs` and `callers` 0.16–0.19 s; `show` 0.29 s; `map` 0.43 s; `map --focus` 0.85 s; `overview` 1.5 s; `impact` 1.8 s; `review` of 10 commits (68 files) 4.2 s.

What an answer costs in tokens stays flat as the repo grows: `def` ~400, `refs` ~2,900, `map` ~1,000, a 68-file review pack ~8,000. The grep-and-read baseline at this size (1–6.5M tokens for one symbol or one review) is larger than any model's context window, so the percentage saved stops being meaningful. Without an index, an agent on a repo like this has to sample and guess.

Expect roughly half these index times and sizes at 16,000 files; query times barely change.

### What gets indexed: `.gitignore` and `.codemap.json`

By default codemap indexes exactly what git would show you: tracked files plus untracked files that are not ignored. It skips build output (`bin/`, `obj/`, `node_modules/`, `dist/`, `target/`…), minified files and lock files. If real source lives behind `.gitignore` (generated API clients, vendored SDKs, source-generator output you check), opt it in. Put a `.codemap.json` in the repo root, commit it or list it in `.git/info/exclude`:

```json
{
  "include": ["src/Generated/**/*.cs", "obj/**/*.g.cs"],
  "exclude": ["**/*.Designer.cs", "legacy/**"]
}
```

`include` globs can reach ignored and normally-skipped paths; `exclude` drops tracked files you don't want mapped. Patterns follow gitignore conventions (`**/` matches any number of directories). The same lists can come from `CODEMAP_INCLUDE` / `CODEMAP_EXCLUDE` (comma-separated). Included ignored files are re-checked on every query, because `git status` does not report them. Git submodules are not indexed; run codemap inside the submodule.

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
