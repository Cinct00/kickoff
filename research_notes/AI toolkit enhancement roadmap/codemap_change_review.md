# codemap repo map and change-review tooling (unmerged branches of Cinct00/ai-toolkit)

Scope and method. I read the stacked branches `origin/claude/codemap-ecosystem` (f95a508), `origin/claude/change-review` (3891956) and the tip `origin/claude/csharp-rust-precision` (ed9a9bf, 0ef875a, 3e980fb, 1310ad7, all dated 2026-11-02) in a detached scratch worktree at the tip commit 1310ad7. All repo paths below are relative to the branch root (e.g. `git show origin/claude/csharp-rust-precision:plugins/codemap/scripts/codemap_core/store.py`). Repo citations use the form `path:line` at commit 1310ad7. The codemap code totals 5,226 lines of stdlib Python across 15 modules (`plugins/codemap/scripts/codemap_core/*.py`). I ran the test suite and part of the benchmarks, plus security proofs of concept (PoCs), in the scratchpad; results are below. Network note: aider.chat, arxiv.org, huggingface.co, cursor.com, emergentmind.com and helpnetsecurity.com could not be fetched from this session (DNS blocked). For those sources I relied on search-result summaries or GitHub-hosted copies, and I mark each such case.

## 1. Architecture of codemap: parsing, languages, ranking, caching, output, exposure

### Takeaway
codemap is a stdlib-only Python indexer that stores a SQLite database (with FTS5) in the user's cache directory. It does not use tree-sitter at runtime. Python goes through `ast`; C# and Rust have hand-written structural lexers/parsers; 11 other languages use a comment/string-masking lexer plus regex definition patterns. It ranks files and symbols Aider-style, with PageRank over a def/ref + import file graph (personalised for `--focus`), and fits the map to a token budget by binary search. It refreshes lazily on every query through git status, and is exposed as a CLI, a single-tool MCP server, a skill, a subagent and a SessionStart hook.

### Cited Findings
- **Parsing strategy (repo).** The module docstring reads: "Python uses the stdlib `ast` module (exact). Other languages use a lexer that masks comments and strings, then per-language definition/import patterns, with brace matching (or indentation) for symbol extents. Identifier references are collected language-agnostically from the masked text, as in tags-based repo maps" (`plugins/codemap/scripts/codemap_core/extract.py:1-7`).
  - Dispatch is `python → extract_python`; `csharp`/`rust` → `lang_cs.extract_csharp` / `lang_rs.extract_rust`, falling back to the generic pattern extractor on `RecursionError/IndexError/KeyError/ImportError`; `markdown → extract_markdown`; everything else → `extract_generic` (`extract.py:696-712`).
  - Python falls back to the generic extractor on `SyntaxError/ValueError/RecursionError` (`extract.py:186-194`).
- **Languages (repo).** The extension map covers Python, JS/TS (incl. .mjs/.cjs/.mts/.cts), Go, Java, Kotlin, Scala, C#, Rust, C, C++, PHP, Ruby, Swift and Markdown (`util.py:11-22`). The docs say accuracy is measured against tree-sitter only for C# and Rust. For "TS/JS, Go, Java, Kotlin, Scala, C/C++, PHP, Ruby, Swift" the extractor is a "comment/string-masking lexer + definition patterns", "spot-checked on real repos, not yet measured" (`docs/codemap.md:57-64`).
- **C#/Rust structural parsers (repo, commit ed9a9bf).** The docs and commit message report results measured against a tree-sitter oracle (`tests/eval_extraction.py`; tree-sitter is used only as the oracle and "codemap stays stdlib-only", `docs/codemap.md:70`):
  - C#: 25,866 declarations in Newtonsoft.Json, Polly and eShop. Recall 63.7% → 99.9%, precision 88.4% → 100.0%, correct parent 82.6% → 99.1%.
  - Rust: 11,625 items in ripgrep, axum and serde. Recall 94.7% → 100.0%, precision 95.2% → 99.6%, end lines and parents 100%.
  - Sources: `docs/codemap.md:61-62` and commit ed9a9bf.
  - C# indexes only the first `#if` branch, and source-generator output is invisible. Rust macro-generated items are invisible (`docs/codemap.md:170`).
- **Import resolution (repo).**
  - C# resolves "the way the compiler does" through usings, own/parent namespaces, global usings and MSBuild `<Using Include>`. Import edges pointing at a used type went from 7.4% to 100% on Newtonsoft.Json, but "coverage of real type dependencies rose from 7.4% to 65–77%" (`docs/codemap.md:74`).
  - Rust: internal imports resolved went from 46% to 96% (ripgrep), 71% to 99.5% (axum) and 81% to 100% (serde) (`docs/codemap.md:75`).
  - Other ecosystems: tsconfig paths, npm workspaces, Go modules, JVM packages, PHP namespaces, Ruby `require_relative`, C/C++ includes and Markdown links (`docs/codemap.md:93`).
  - Manifests parsed: package.json, requirements, pyproject, go.mod, Cargo.toml, csproj/Directory.Packages.props, pom.xml, gradle, Gemfile, composer.json (`docs/codemap.md:94`).
- **Storage schema (repo).** The index has these tables: files (path, lang, lines, tokens, is_test, rank, generated); symbols (name, qualname, kind, lines, signature, doc, parent, exported, rank); idents (identifier occurrences per file); imports (raw → resolved file or external package); bases; deps; edges (weighted file graph); and FTS5 for camelCase/snake_case-aware search (`docs/codemap.md:79-90`; `queries.py:809-815`). SQLite runs in WAL mode with `synchronous=NORMAL` (`store.py:59-61`). The DB lives in `$XDG_CACHE_HOME/ai-toolkit/codemap/<slug>-<sha1(root)[:10]>.db` (`util.py:100-116`).
- **Ranking: Aider-style PageRank (repo).** `_compute_ranks` is documented as "Aider-style: weighted def/ref file graph -> PageRank -> per-symbol scores" (`store.py:448-504`).
  - **Edge weights.**
    - A file that references an identifier defined in another file gets an edge weighted `mul*sqrt(count)/len(def_files)`.
    - `mul` is ×10 for long camelCase/snake_case names, ×0.1 for `_private` names, and ×0.1 for names defined in more than 5 files.
    - Names defined in more than 20 files are skipped entirely (`MAX_DEFS_FOR_EDGES = 20`, `store.py:47`).
    - Resolved imports add +0.5 per edge.
    - Only the 40 strongest out-edges per file are persisted (`MAX_EDGES_PER_FILE = 40`, `store.py:48`).
  - **PageRank itself.** A hand-rolled power iteration: damping 0.85, 30 iterations, tol 1e-6, optional personalisation vector (`graph.py:5-37`).
  - **Symbol rank.** The file's PageRank share is distributed over the referenced names, plus a small base for exported symbols (`store.py:490-503`).
- **Map selection (repo).** `map` takes these steps (`queries.py:191-300`; constants `queries.py:17-19`):
  - Considers only the top 300 ranked files (`MAP_CANDIDATE_FILES = 300`), excluding generated files and tests.
  - Scores each symbol as `file_rank*(0.15 + symbol_rank/max_rank_in_file)`. Focus names get ×10; headings, consts and macros get ×0.3.
  - Binary-searches the number of symbols so that rendered signatures grouped by file fit `--budget` (default 1024 tokens).
  - With `--focus`, runs personalised PageRank on a 2-hop neighbourhood capped at 3,000 nodes.
- **Freshness and caching (repo).**
  - Every query triggers a lazy refresh, throttled to once per 3 s (`LAZY_MIN_GAP = 3`, `store.py:49`).
  - In git repos the candidate set comes from `git status --porcelain -z`, `git diff --name-only indexed_head..HEAD`, and the paths that were dirty last time. Otherwise it falls back to a full `list_files` scan (`store.py:137-163`).
  - A changed file is detected by size+mtime, then sha1 of the content (`store.py:199-221`).
  - Lazy refreshes resolve only the changed files. Global re-resolution and re-ranking are deferred to a detached background `codemap index`, spawned at most once a minute (`store.py:116-135`, `store.py:236-245`).
  - Parsing uses a `ProcessPoolExecutor` once a batch reaches 300 files, in batches of 1,000 (`store.py:515-553`).
- **Output format (repo).** Compact plain text grouped by file, with line numbers. The `map` output prints `path:` and then indented `line: signature` rows (`queries.py:258-287`). Every query logs `out_tokens` and an "avoided" figure, defined as "tokens of the files a query stood in for (outline/show: that file; find/refs/map: files listed)" (`queries.py:179-190`; `cli.py:143`).
- **Exposure (repo).**
  - MCP server: stdlib JSON-RPC over stdio exposing **one** tool `codemap(cmd: string)`. Its schema is about 150 tokens "versus 1,500+ for a tool per command" (`mcp.py:1-28`; `docs/codemap.md:166`). Protocol version `2025-06-18`, and the server echoes the client's requested version (`mcp.py:14`, `mcp.py:54-57`).
  - Plugin wiring: `plugins/codemap/.mcp.json` and `copilot-mcp.json`.
  - CLI shim `~/.local/bin/codemap`, installed by `toolkit.py install`.
  - Skill `skills/codemap/SKILL.md`, which teaches a cost "ladder": overview → map → find/def → outline/show → refs/callers → impact.
  - Subagent `agents/code-navigator.agent.md`: read-only, returns at most 40 lines with file:line references.
  - SessionStart hook `hooks/session_start.py`: spawns a background index when the DB is more than 60 s stale and injects about 60 tokens of context (`session_start.py:56-73`). Claude Code hook config: `hooks/hooks.json`.
- **External comparison: Aider.** Aider's repo map "defaults to 1k tokens" (`--map-tokens`). It uses a file dependency graph with "a graph ranking algorithm", so that the identifiers selected are those "most often referenced by other portions of the code" — [Aider repomap doc (GitHub copy)](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/docs/repomap.md). The fetched page did not mention tree-sitter, and aider.chat itself was unreachable.

### Inferences
- codemap's ranking is a close reimplementation of Aider's design: def/ref graph, PageRank, ~1k-token default budget, ×10 boost for long identifiers, ×0.1 for private names, personalisation by focus. Its differentiators are persistence (SQLite + incremental git-driven refresh), a query surface (refs/callers/impact/hierarchy/sql) and import-aware "confirmed vs name-only" references. Aider's map is ephemeral per chat.
- The choice of stdlib only, with no tree-sitter at runtime, buys zero-install portability. The cost is that 11 of the 14 code languages rest on unmeasured regexes. For those languages, references are pure name matching over masked text (ctags-like), so precision for `refs/callers/impact` is unknown.
- The single-tool MCP design is token-cheap but opaque. The model must learn the command grammar from the description or `help`, and arguments are not schema-validated (see Security).

### Gaps
- Tree-sitter-vs-codemap accuracy for TS/JS, Go, Java, Kotlin, Scala, C/C++, PHP, Ruby and Swift is not measured anywhere in the branch. The docs say so.
- No measurement exists of `refs`/`callers` precision and recall against a compiler or LSP (e.g. SCIP or rust-analyzer find-references) for any language.

## 2. change-review: how structural, visual change maps are built and integrated

### Takeaway
`codemap review` parses the git patch, re-extracts symbols from both sides of each changed file (base via `git show`, head via worktree or `git show`), and matches them by qualified name. From that it classifies changes as signature, removed, renamed, moved, modified or added. Using the index, it adds import-aware "callers outside the diff", a heuristic 0–100 risk score per file, test-gap analysis and manifest dependency diffs. It renders text, a token-budgeted "context" pack, GitHub Markdown with a Mermaid flowchart, self-contained HTML and JSON. A composite GitHub Action posts a sticky PR comment, writes the job summary and uploads artifacts.

### Cited Findings
- **Diff collection (repo).**
  - Collection runs `git -c core.quotePath=false diff --no-color --no-ext-diff -M -U3 <base> [<head>]`. In worktree mode, untracked files are synthesised as all-added hunks (`review.py:62-67`, `review.py:171-191`).
  - The base defaults to the merge-base with `origin/HEAD` or a common default branch (`review.py:70-99`).
  - File sides are read with `git show ref:path`, or from the worktree (`review.py:194-200`).
- **Symbol diff (repo).**
  - The change markers mean: `~` signature changed (old → new shown), `-` removed, `→` renamed (same body, new name) or moved (same body, another file), `*` modified (changed lines inside the symbol's own body, not its children's), `+` added (`docs/change-review.md:11`). Implementation: `review.py:205-290`.
  - Attention items are raised for signature, removed, renamed or moved symbols that have callers outside the diff (`review.py:387-400`).
- **Callers outside the diff (repo).** These are "files that use the name *and* import the changed file (or share its package in Go/JVM/C#/Swift), and are not in the diff" (`docs/change-review.md:12`; `review.py:449-467`).
- **Risk score (repo, `review.py:473-513`).** The score is a hand-weighted sum, clamped to 0–100 (thresholds in `review.py:469-471`):
  - Base by status: A/D 10, M 12, R 5.
  - Churn: `min(25, 6*log2(1+churn))`.
  - Centrality: `+20*rank_pct` if the file is in the top 20% by PageRank.
  - Dependents: `+min(15, 3*sqrt(n_dependents))`.
  - Public API signature, removal or rename: +10.
  - Callers outside the diff: `+min(15, 5*n)`.
  - Untested: +10. Tests changed: −5.
  - Sensitive path: +12. The regex covers auth, token, secret, payment, migration, schema, `.github/workflows/`, docker, terraform, k8s, csrf, cors, iam (`review.py:25-28`).
  - Caps: test files capped at 25; markdown and non-code at 15; generated/lock files fixed at 3, "skim".
- **Dependency view (repo).** Nodes are up to 30 changed non-test, non-generated files by risk plus up to 12 impacted files. Edges come from the persisted ranking edges (weight ≥ 0.5) plus resolved imports, capped at 80 (`review.py:516-545`).
  - The Mermaid output is a `flowchart LR`: at most 15 changed and 6 impacted nodes, 35 edges, subgraphs per directory, classDefs per status, and bold for high risk (`review_render.py:146-195`).
- **Renderers (repo).**
  - text brief (~1k tokens); `context` pack fitted to `--budget` (risk-ordered summary, attention, deps, tests, then per-file symbol changes and hunks); `md` (sticky-comment marker, Mermaid in `<details>`, review-order table, symbol changes in ```diff blocks, tests, dependencies; truncated at 60,000 chars for GitHub's 65,536 limit); `html` (data embedded as JSON in `<script type="application/json">`, rendered client-side via `textContent`); `json` (`review_render.py:44-128`, `198-260`, `263-266`; `docs/change-review.md:20-26`).
  - Per-file diffs are truncated at 400 lines (`review.py:24`, `review.py:333`).
- **GitHub integration (repo).**
  - The composite action is `.github/actions/change-map/action.yml`. It runs `codemap index`, then four `review` invocations (json/md/html/context). It appends `comment.md` to `$GITHUB_STEP_SUMMARY`, uploads the directory with `actions/upload-artifact@v4`, and creates or PATCHes a sticky comment found by the `<!-- codemap-change-map -->` prefix using `gh api` (`action.yml:39-95`).
  - It uses the script from `github.action_path`, "never from the pull request checkout" (`action.yml:43-44`).
  - The dogfood workflow triggers on `pull_request` (not `pull_request_target`) with `contents: read, pull-requests: write`, and checks out with `fetch-depth: 0` (`.github/workflows/change-map.yml`).
  - `toolkit.py adopt <repo> --review-workflow` installs the workflow in other repos (`scripts/toolkit.py:1656`).
  - The docs advise pinning `@<sha>` in production (`docs/change-review.md:50`).
- **Skill guidance (repo).** The change-review skill tells agents to verify every attention item first, walk files in risk order, and run the "likely affected, not changed" tests. It also says to treat attention items "as leads to verify, not verdicts" (`plugins/codemap/skills/change-review/SKILL.md`).

### Inferences
- The analysis is static and name-based. It is closer to a "semantic diff + blast-radius" tool (in the spirit of Sourcegraph and other code-intel diff views) than to an LLM reviewer. That makes it cheap and deterministic, a good pre-filter for an AI reviewer.
- The risk weights are hand-tuned. No calibration against historical defect data exists: no check of whether high-risk files actually received review comments or later fixes.

### Gaps
- No evaluation shows whether the attention items ("callers outside the diff", "removed but still referenced") catch real bugs, or what their false-positive rate is.

## 3. Benchmarks: methodology, results, soundness, reproduction

### Takeaway
All published numbers measure tokens only: characters ÷ 4, comparing codemap output against a scripted "grep-and-read" or "patch + full files" baseline. None measures answer quality, task success, tool-call count or latency of an agent loop. I reproduced the token numbers exactly on requests, cobra and ripgrep, and all 53 unit tests pass. Two problems weaken the claims: the baselines are pessimistic, and the review pack is capped by budget, so its "96.5% saved" largely restates the budget. Pairing these numbers with retrieval-quality metrics, as recent benchmarks like SWE-Explore do, would make them meaningful.

### Cited Findings
- **Symbol benchmark methodology (repo).** The baseline is `git grep -n -w NAME` (first 250 lines), plus reading the defining file in full, plus the 2 files with the most grep hits. The codemap side is `def + refs + show`. Both sides use `est_tokens = (len+3)//4` (`tests/bench_codemap.py:7-17`, `51-59`; `util.py:50-53`).
- **Orientation benchmark methodology (repo).** The baseline is `git ls-files` + README + the 3 "central files" read in full. The central files are taken from codemap's own `overview` output. The codemap side is `overview` + `map --budget 1024` (`bench_codemap.py:99-105`).
- **Review benchmark methodology (repo).** The baseline is the full `git diff base..head` plus every changed non-deleted file read in full. The codemap side is the `--format context --budget 8000` pack (`bench_codemap.py:62-81`). Commit 0ef875a stopped counting binary files ("overstated eShop's baseline by ~460k tokens").
- **Published results, 10 repos (repo).**
  - Locate+understand: 855,197 → 39,681 tokens (95%) over 20 symbols. Small-file repos save less (eShop 52–57%) (`docs/codemap.md:11-35`).
  - Orientation: 310,885 → 12,670 (96%) (`docs/codemap.md:39-51`).
  - Review pack: 3,091,679 → 107,966 (96.5%, median 92.5%) over 18 commit ranges. Small changes (requests 59–63%, Polly `HEAD~5` 78%) save less (`docs/change-review.md:56-76`).
  - The skill text after commit 3e980fb says: "84–99% fewer tokens than patch + changed files on 7–251-file changes; 59–78% on small changes" (`skills/change-review/SKILL.md`).
  - The plugin README still advertises "~96% fewer tokens than grep-and-read" (`plugins/codemap/README.md`).
- **My reproduction (scratchpad, this session).** I cloned requests (HEAD 3c7baaa), cobra (adbc881) and ripgrep (91f5d22) at depth 60 and ran `bench_codemap.py` (stdlib, `-I`). The results matched the published per-row numbers exactly:
  - requests `Session` 48,599 → 2,557; cobra `ExecuteC` 65,252 → 640; ripgrep `Searcher` 52,411 → 758.
  - Orientation: requests 13,656 → 1,232; cobra 28,494 → 1,186; ripgrep 48,781 → 1,232.
  - Review ranges: requests `HEAD~20` 5,757 → 2,105 (63%); cobra `HEAD~20` 98,506 → 7,649 (92%); ripgrep `HEAD~30` 245,130 → 8,022 (97%).
  - Full index times: 0.2–0.7 s.
  - `python3 -m unittest discover -s tests` ran 53 tests, all OK, in 9.7 s.
- **What the benchmarks do not measure (repo).** Neither script contains any correctness check: no ground-truth locations, no answer grading, no agent runs (`tests/bench_codemap.py` is 131 lines of token arithmetic only). The extraction eval (`tests/eval_extraction.py`) is the only accuracy measurement, and it covers C# and Rust declarations only, not retrieval usefulness.
- **External: how quality-aware retrieval benchmarks are designed.**
  - **SWE-Explore** (arXiv 2606.07297, June 2026). An explorer returns ranked code regions under a fixed line budget for 848 issues across 10 languages and 203 repos (from SWE-bench Verified, Pro and Multilingual). Ground truth comes from regions consulted by successful solving trajectories. Metrics are line-level P/R/F1, file-level hits and context efficiency. Agentic explorers beat classical retrieval, but line recall is low (reported ~0.14–0.23) despite strong file-level accuracy. Source: [hyper.ai summary](https://hyper.ai/en/papers/2606.07297), [alphaxiv](https://www.alphaxiv.org/audio/2606.07297v1). Aggregator only; arXiv was unreachable.
  - **Agent Retrieval Bench** (2607.24882). File-level retrieval, 427 samples across 25 repos. It evaluates lexical retrieval, RepoMap, open-source embeddings, selective abstention and logged agent context selection — [HF papers page (search snippet only)](https://huggingface.co/papers/2607.24882). The page itself was unreachable, so I have no numbers.
  - **Code-review benchmarks.** Qodo notes "no standard benchmark for AI code review" exists. Example designs: Greptile uses 50 PRs with one historically fixed bug each; Qodo uses 580 injected issues across 8 repos; Martian's Code Review Bench reports Greptile at 60.8% F1. GitHub released ReviewBench in 2026. Sources: [Qodo glossary](https://www.qodo.ai/glossary/what-is-ai-code-review-benchmarks/), [Help Net Security on ReviewBench](https://helpnetsecurity.com/2026/10/06/github-reviewbench-ai-code-review-benchmark). Search summaries only; most of these numbers are vendor-run.

### Inferences
- **The baselines are strawmen of a modern agent.** Claude Code's tools read files with offset/limit, Grep defaults to files-with-matches and supports `-C` context, and agents rarely read the two most-referencing files in full. A fairer baseline would replay real agent trajectories, or use "grep -n + read ±N lines around hits". Savings would still be large on big files but smaller than 95%.
- **The orientation baseline is circular.** Its "3 most central files" are chosen by codemap's own ranking.
- **The review-pack saving is mostly the budget.** The pack is hard-capped at about 8k tokens, so on any change above ~100k tokens it is by design "a triage view, not a full review" (`docs/change-review.md:78`). Reporting 96.5% compares a truncated triage summary against complete information. The meaningful question is review recall at equal budget, and nothing measures it.
- **Lock and generated files inflate the review baseline.** `bench_codemap.py:77` counts every non-deleted changed file. `estimate_baseline_tokens` in the product excludes generated files (`review.py:548-552`), but the benchmark does not.
- **The `savings` counter overstates benefit.** It credits whole-file tokens for every file a `find`/`refs`/`map` result lists (`queries.py:185`). It is a marketing counter, not a measurement.
- **Exact reproduction is good for determinism.** It also suggests the published runs used the same upstream HEADs (cloned 2026-11-03 vs commit 2026-11-02).

### Gaps
- I did not reproduce the C# (Newtonsoft.Json, Polly, eShop), hono, gson, axum or serde rows, and did not run `eval_extraction.py`: it needs pip and tree-sitter wheels, which I skipped to stay stdlib-only and read-only.
- I did not reproduce the Roslyn scale numbers (see section 4).

## 4. Scaling to 35k-file repositories

### Takeaway
Commit 1310ad7 profiled dotnet/roslyn (35,451 files, 18,291 C#) and removed the whole-repo work from the query path. It made freshness git-driven, deferred global resolve and rank to a background process, parallelised parsing in bounded batches, pruned ranking edges, and restricted `map` to the top-ranked or 2-hop subgraph. The reported results: full index 126 s, 0.68 GB peak memory, 512 MB DB, and 0.16–1.8 s queries.

### Cited Findings
- **Reported Roslyn numbers (repo, before → after).**
  - Full index: over 6 min (35 s import resolution + 301 s ranking) → 126 s on 4 cores.
  - Peak memory: 1.6 GB → 0.68 GB.
  - Index size: 1,229 MB → 512 MB.
  - Ranking edges: 17.4M → 0.68M.
  - No-change query: 0.7 s → 0.17 s.
  - First query after edit/add/delete: minutes → 1.1 s / 1.0 s / 0.27 s.
  - Sources: `docs/codemap.md:108-117`; commit 1310ad7.
- **Per-command latency on Roslyn (repo).** `find/def/outline/refs/callers` 0.16–0.19 s; `show` 0.29 s; `map` 0.43 s; `map --focus` 0.85 s (was 14.6 s); `overview` 1.5 s; `impact` 1.8 s; `review` of 68 files 4.2 s (`docs/codemap.md:119`; commit 1310ad7).
- **Mechanisms (repo).**
  - git-based candidate detection (`store.py:137-163`).
  - Background `codemap index`, disabled with `CODEMAP_BACKGROUND=0` (`store.py:116-135`).
  - `ProcessPoolExecutor` on all cores, 1,000-file batches (`store.py:515-553`).
  - Names defined in more than 20 files dropped; top 40 edges per file kept (`store.py:47-48`, `472-489`).
  - C# scope resolution iterates the smaller of used names vs namespace types (29 s → 21 s).
  - `map` scores the top 300 files only (`queries.py:18`, `253-256`).
  - `--focus` 2-hop subgraph with a 3,000-node cap (`queries.py:202-227`).
  - Generated and test detection by path and header (`util.py:43-74`).
  - Schema bumped to 3.
- **Token flatness claim (repo).** Answer sizes stay flat (`def` ~400, `refs` ~2,900, `map` ~1,000, 68-file pack ~8,000). Meanwhile "the grep-and-read baseline at this size (1–6.5M tokens for one symbol or one review) is larger than any model's context window, so the percentage saved stops being meaningful" (`docs/codemap.md:121`).
- **Index throughput in my tests.** requests, cobra and ripgrep each fully indexed in 0.2–0.7 s.

### Inferences
- Dropping names defined in more than 20 files and truncating to 40 edges per file are pragmatic. They also silently remove precisely the common-API edges (`Dispose`, `Create`) that impact analysis may need, so `impact`/`review` dependents on large repos are probably under-reported. This trade-off is not measured.
- Between background re-ranks, ranks can be stale (`ranks_stale` meta). For a single agent session this is fine, but the review action calls `index` first, so CI is unaffected.

### Gaps
- No independent reproduction of the Roslyn numbers. I did not clone Roslyn (35k files) in this session.
- No scale numbers for JS/TS monorepos, where the pattern extractor and name-based idents would dominate.

## 5. Security: untrusted repos and PR content

### Takeaway
The design is sound in the main respects:
- No repository code is executed or imported (Python uses `ast.parse`, not import).
- The CI action runs codemap from its own pinned ref under `pull_request`.
- The HTML report escapes JSON and renders via `textContent`.
- SQL is opened read-only.

I confirmed three real issues with PoCs: tracked symlinks are followed outside the repo (read and print host files, or hang/OOM on `/dev/zero`); the documented `CODEMAP_MAX_FILE_BYTES` cap is never enforced; and the "read-only" MCP tool can write arbitrary files via `review --out` and re-target other repos via `--repo/--db`. Minor: unescaped backticks in paths can inject Markdown into the PR comment.

### Cited Findings
- **No code execution (repo).**
  - Python is parsed with `ast.parse` (`extract.py:189`); other languages are lexed as text.
  - Git calls are list-form `subprocess.run` (no shell) with `--no-ext-diff` (`review.py:62-67`, `171-175`; `util.py:85-90`).
  - The docs state the action "only reads and parses the PR's files, never executes them. It uses `pull_request`, not `pull_request_target`, and passes every input through environment variables" (`docs/change-review.md:50`; `action.yml:42-57`).
- **HTML escaping (repo).** The data blob is `json.dumps(...).replace("</", "<\\/").replace("<!--", "<\\!--")`, and the title is stripped of `<>&"` (`review_render.py:263-266`). The client renders with `textContent`. The only `innerHTML` is a static SVG marker built from the page's own CSS variable (`review_render.py:319-391`, line 383). A regression test injects `</script><script>alert(1)</script>` (`tests/test_review.py:109`, `200-206`).
- **SQL (repo).** `sql` accepts only `SELECT/WITH/PRAGMA table_info` and opens the DB with `mode=ro` (`queries.py:792-806`).
- **Path traversal in `show`/`outline` (repo).** Paths resolve only against rows in the `files` table (`queries.py:33-47`), so `show ../../etc/passwd:1-5` fails.
- **[PoC-confirmed] Symlinks are followed (repo).**
  - Mechanism: `read_text()` calls `path.read_bytes()` with no `is_symlink`/`lstat`/realpath containment check (`util.py:223-233`). `list_files` takes whatever `git ls-files` lists, including mode-120000 symlinks (`util.py:195-220`). `show` reads `root / path` directly (`queries.py:493-497`). No module contains `islink`/`is_symlink`.
  - In a scratch repo, a committed `evil.py -> ../outside_secret.txt` was indexed (`find leaked` returned its function), and `show evil.py:1-3` printed the out-of-repo file's contents.
  - A committed `notes.txt -> /etc/os-release` printed host OS data via `show notes.txt:1-2`. Non-code files are not parsed, but `show PATH:A-B` still reads them.
  - Impact: a malicious repo can make an agent read and surface `~/.ssh/*`, `~/.aws/credentials` and similar into model context (an exfiltration vector when combined with prompt injection). This bypasses Claude Code's own Read permission rules because the read happens inside the MCP server.
- **[PoC-confirmed] Unbounded reads (DoS) (repo).**
  - `MAX_FILE_BYTES = int(os.environ.get("CODEMAP_MAX_FILE_BYTES", 1_000_000))` is defined (`util.py:41`) and documented (`docs/codemap.md:155`), but grep shows no other reference anywhere in the code.
  - A 3.3 MB `.js` file was fully read and indexed: 300,001 lines, a 6 MB DB for 5 files.
  - A committed `zero.js -> /dev/zero` made `codemap index` raise `MemoryError` under a 1.5 GB `ulimit -v`. Without a limit it would consume all memory.
  - In CI the action runs `codemap index` on the PR checkout (`action.yml:53`), so any PR can kill the change-map job.
  - Locally, the SessionStart hook spawns `codemap index` automatically on session start (`session_start.py:56-63`). Opening a hostile repo would start a runaway background process with no prompt.
- **[PoC-confirmed] The MCP tool has write and re-target capability (repo).**
  - The MCP `cmd` string is `shlex.split` and fed to the full argparse CLI (`cli.py:181-198`). This includes global `--repo`/`--db` (`cli.py:96-98`) and `review --out FILE`, which calls `Path(args.out).write_text(...)` (`cli.py:83`, `cli.py:171-172`).
  - Calling `handle()` with `review ... --format md --out <scratch>/outside/written.md` attempted the write; it failed only because the directory did not exist.
  - `--repo ../cobra overview` read a sibling repository.
  - Impact: an agent that is allowed the codemap MCP tool, perhaps auto-approved as "read-only navigation", can be steered by injected content to overwrite files anywhere the user can write, outside the IDE's write-permission prompts. `--db` can also create SQLite files at arbitrary paths. Only `mcp` itself is blocked (`cli.py:190-192`).
- **Markdown/Mermaid injection (repo).**
  - Mermaid labels escape `"`, `<`, `>` and `|` (`review_render.py:132-133`). Each node and edge is emitted on its own line inside a fenced block, and git C-quotes control characters, so newline breakout is unlikely.
  - In the Markdown table and symbol headings, paths are wrapped in single backticks without escaping: `` f"| {i} | `{f['path']}`..." `` (`review_render.py:221`) and `` f"**`{f['path']}`**" `` (`review_render.py:229`). Git permits backticks in filenames, so a PR can add a file whose name closes the code span and injects Markdown (links, images, @-mentions) into the bot's sticky comment.
  - GitHub's HTML sanitizer limits this to content spoofing or tracking pixels, not script.
  - Reasons are `|`-escaped (`review_render.py:220`).
- **Token handling in CI (repo).** `GH_TOKEN` is set only in the comment step, not in the step that parses PR content (`action.yml:42-47` vs `77-82`). The comment step uses `continue-on-error` for fork PRs (`action.yml:76`). `actions/checkout@v4` runs with default `persist-credentials` (`.github/workflows/change-map.yml`), so the job token sits in `.git/config` on the runner while untrusted files are parsed.
- **Untrusted config (repo).** A repo-supplied `.codemap.json` can `include` gitignored files into the index (`util.py:130-148`, `183-192`). Combined with the symlink issue, it widens what gets read. A malformed `.codemap.json` is safely ignored.

### Inferences
- Recommended fixes:
  - Use `os.lstat`, skip symlinks, or require `realpath` inside root, in `read_text`, `show`, `review.file_text` and the tsconfig/csproj readers.
  - Enforce `MAX_FILE_BYTES` via `st.st_size`, and refuse non-regular files (`stat.S_ISREG`).
  - Strip `--repo/--db/--out` from MCP calls, or restrict `--out` to the cache directory.
  - Escape backticks, or use `<code>` with HTML-escaping, in Markdown paths.
  - Set `persist-credentials: false` in the workflow template.
- The PR-comment path still appears safe from symlink contents. In CI, review symbol extraction uses `git show HEAD:path`, which yields the link-target string, not the target's contents. I found no code path that copies indexed symlink-target content into `comment.md` or `change-map.html`, but I did not exhaustively prove this.

### Gaps
- I did not test the tsconfig `extends`, csproj and `Directory.Build.props` readers in `resolve.py` and `store.py:401` for out-of-root path following.
- Regex catastrophic backtracking (ReDoS) in the per-language definition patterns was not fuzzed.

## 6. State of the art (2025–2026) and concrete improvements for codemap

### Takeaway
The field has converged on a few points:
- Just-in-time, agentic retrieval (grep/glob) as the default (Anthropic, Claude Code).
- Precise symbol navigation via LSP/SCIP: Claude Code now ships official LSP plugins for 13 languages, though not in cloud sessions; Serena offers 40+ languages over MCP.
- Optional semantic (embedding) search, which Cursor reports as a measurable accuracy gain.
- Graph-guided localisation in research: RepoGraph, LocAgent, CoSIL.
- Benchmarks that grade retrieval quality, not tokens: SWE-Explore, Agent Retrieval Bench, code-review benchmarks.

codemap's niche is zero-dependency, cloud-session-compatible, token-budgeted structure. Its main gaps are unmeasured precision for 11 languages, no task-conditioned or semantic ranking, and token-only evaluation.

### Cited Findings
- **Anthropic on context engineering** (Sept 29, 2025). Agents should "maintain lightweight identifiers (file paths, stored queries, web links, etc.)" and load data just in time. Claude Code uses "glob and grep" to "retrieve files just-in-time", sidestepping "stale indexing and complex syntax trees", though "runtime exploration is slower than retrieving pre-computed data". Claude Code is described as a hybrid: CLAUDE.md up front, plus glob/grep. Tools should return "information that is token efficient" — [Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).
- **Claude Code and RAG.** Boris Cherny reportedly said early Claude Code used RAG with a local vector DB, and that agentic search worked better (staleness, privacy, simplicity; Latent Space podcast, May 2025). Secondary sources only — [ahkarimi blog](https://ahkarimi.github.io/blog/2026/rag-failed-in-production/), [dev.to analysis](https://dev.to/chen115y/the-representation-problem-why-rag-vs-agentic-search-is-the-wrong-debate-4j8f).
- **Claude Code native LSP.**
  - Official "code intelligence" plugins exist for C/C++ (clangd), C# (csharp-ls), Go (gopls), Java (jdtls), Kotlin, Lua, PHP (intelephense), Python (pyright), Ruby, Rust (rust-analyzer), Swift (sourcekit-lsp) and TypeScript/JavaScript, plus Shopify's Liquid. They provide diagnostics after edits and a read-only `LSP` tool that "looks up symbols through the server instead of searching text for them".
  - "In cloud sessions, Claude Code doesn't start plugin language servers" — [Claude Code docs: Code intelligence](https://code.claude.com/docs/en/plugins/code-intelligence.md).
  - Plugins can declare `lspServers` via `.lsp.json` — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference).
- **Serena (MCP).** Symbol-level tools (find symbol, symbol overview, find referencing symbols, declaration, implementations, diagnostics) backed by LSP for "over 40 programming languages", or by a paid JetBrains backend. Exposed via MCP over stdio or HTTP — [Serena README](https://raw.githubusercontent.com/oraios/serena/main/README.md).
- **SCIP.** "A language-agnostic protocol for indexing source code" powering go-to-definition, find-references and find-implementations. Indexers include scip-java (Java/Scala/Kotlin), scip-typescript, scip-python, rust-analyzer, scip-dotnet (C#/VB), scip-clang, scip-ruby, scip-php and scip-dart — [SCIP README](https://raw.githubusercontent.com/sourcegraph/scip/main/README.md).
- **Cursor indexing.** Merkle-tree change detection plus per-chunk embeddings cached by content. Cursor reports +12.5% average answer accuracy (range 6.5–23.5%) with semantic search on its internal Cursor Context Benchmark. This is a vendor benchmark with no independent replication, per search summaries — [Cursor blog: secure codebase indexing](https://cursor.com/blog/secure-codebase-indexing) (unreachable; numbers from search summary), [Bito guide](https://bito.ai/blog/how-cursors-codebase-indexing-works-2026-guide/).
- **RepoGraph** (ICLR 2025). A line-level code graph; retrieval returns sub-graphs (ego-graphs) around keywords. Plugged into four SWE frameworks, it "substantially boosts the performance of all systems"; a third-party summary reports +32.8% average relative resolve rate on SWE-bench Lite — [ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/4a4a3c197deac042461c677219efd36c-Abstract-Conference.html), [arXiv 2410.14684](https://arxiv.org/abs/2410.14684).
- **LocAgent** (ACL 2025). A heterogeneous graph of files, classes and functions with import, invoke and inheritance edges, navigated multi-hop by the agent. A fine-tuned Qwen2.5-Coder-32B reaches 92.7% file-level accuracy at about 86% lower cost, with +12% Pass@10 on issue resolution — [arXiv 2503.09089](https://arxiv.org/html/2503.09089v1), [ACL Anthology](https://preview.aclanthology.org/setup/2025.acl-long.426).
- **CoSIL.** Index-free, two-phase localisation over dynamically built module call graphs. Reported Top-1 of 43.3% (SWE-bench Lite) and 44.6% (Verified) with Qwen2.5-Coder-32B — [arXiv 2503.22424](https://arxiv.org/html/2503.22424v2).
- **SWE-Explore** (June 2026). Agents form "a clear tier above classical retrieval", and differences among Claude Code, OpenHands and mini-SWE-agent are minor relative to that gap. Line-level recall is the open problem — [hyper.ai summary](https://hyper.ai/en/papers/2606.07297) (aggregator).

### Inferences: concrete improvements, ranked by expected value
1. **Make the benchmarks quality-aware (highest priority).** Add a retrieval-quality harness alongside the token counts.
   - Score `map/find/refs/impact` outputs against SWE-Explore or Agent Retrieval Bench ground truth: file hit@k and line P/R at equal token budgets.
   - Run A/B agent trials (Claude Code with vs without codemap) on a SWE-bench Verified slice, reporting resolve rate, tokens, tool calls and wall time.
   - For change-review, measure attention-item recall and precision on a code-review benchmark with known bugs (e.g. Greptile-style historical bug PRs or ReviewBench), and compare an LLM reviewer given the 8k pack against one given the full diff, at equal cost.
   - Replace the strawman baselines with replayed real agent trajectories, and drop the circular "central files" orientation baseline.
2. **Use precise backends where available.** Keep the stdlib parsers as the zero-install floor, but:
   - When a SCIP index or a language server exists (Claude Code's official LSP plugins, rust-analyzer, pyright, csharp-ls), back `refs/callers/impact/hierarchy` with LSP or SCIP results, and label confidence per answer. This mirrors Serena's design.
   - Because Claude Code does not start LSP servers in cloud sessions, codemap's stdlib path remains the fallback there: a genuine differentiator worth stating in the docs.
3. **Get tree-sitter-grade extraction for the 11 pattern-based languages.** Either vendor optional `tree-sitter` + `tree-sitter-language-pack` wheels behind a feature flag (the oracle harness `tests/eval_extraction.py` already exists), or at minimum extend `eval_extraction.py` to TS/JS, Go, Java and the rest, and publish recall and precision the way C# and Rust already are.
4. **Task-conditioned ranking.** Today `map` personalises only by explicit `--focus` paths or symbols. Instead:
   - Add `map --query "<issue text>"`, seeding personalised PageRank from FTS/BM25 hits on symbol names, docstrings and identifiers (the hybrid lexical + graph approach of RepoGraph and LocAgent).
   - Optionally add a small local embedding model over symbol signatures and docs, gated by opt-in and privacy settings, which Cursor reports improves accuracy.
   - Return ranked line regions (start-end) rather than whole signatures, to target the line-recall gap SWE-Explore identifies.
5. **Call-graph precision.** Store call edges, not only file-level ident counts. Recover the edges dropped by `MAX_DEFS_FOR_EDGES` for `impact` via import-scoped resolution, and measure impact recall.
6. **MCP design.**
   - Keep the single-tool, low-schema-cost design, but add an enum-validated `cmd` verb plus args (still one tool).
   - Block filesystem-affecting flags (`--out`, `--db`, `--repo`) from MCP.
   - Advertise read-only tool annotations (`readOnlyHint`) only once writes are impossible.
   - Consider returning `structuredContent` for JSON-capable clients.
7. **Security hardening.** As in section 5: no symlink following, enforced size cap and regular-file check, Markdown escaping, `persist-credentials: false`, and pinned action SHAs in the adopt template.
8. **Change-review calibration.** Fit the risk weights against history (files later touched by fix commits, or PR review-comment density). Report precision@k of the review order. Add semantic signals: type changes in public signatures, deleted tests, config/infra diffs.

### Gaps
- I could not access Aider's site, arXiv, Hugging Face or Cursor's blog directly. Numbers for SWE-Explore, Agent Retrieval Bench, Cursor and RepoGraph's +32.8% come from aggregators or search summaries and should be verified against the primary papers.
- I found no independent, published head-to-head comparison of Aider-style repo maps against LSP-backed tools (Serena) on agent task success.
- I found no official Anthropic changelog date for the Claude Code LSP tool. The docs page confirms it exists now but not when it was introduced.
