# Harden, Measure, Then Grow the AI Toolkit

The four open branches of gimarais/ai-toolkit are not four separate projects. They form **one linear stack**: `main` → `claude/sleepy-cerf-pluea6` → `claude/codemap-ecosystem` → `claude/change-review` → `claude/csharp-rust-precision`. The tip commit, 1310ad7, contains everything and can fast-forward `main`. It builds three things. The first is a cross-LLM plugin marketplace generated from one `toolkit.json` by a stdlib-only `scripts/toolkit.py` (1,696 lines, 11 subcommands), covering 6 plugins, 34 skills, 5 agents and 1 MCP server. The second is a "kickoff" router plus a "harvest" loop that writes new skills out of session experience. The third is **codemap**, a 5,226-line stdlib SQLite/PageRank repo map. Its `review` command and GitHub Action produce structural PR change maps. The tip is clean (53 tests pass, `validate` and `audit --strict` are green), and codemap's published token savings reproduce exactly on independent clones.

The research found three things to fix before the toolkit grows further:

- **Security.** Three codemap holes are confirmed by proof of concept: tracked symlinks let the tool read host files, the documented file-size cap is never enforced, and the "read-only" MCP tool can write files and point itself at other repos. On top of that, the supply chain is unpinned, and harvest writes hooks "without asking" into a symlinked checkout that is live in every AI client on the machine.
- **Measurement.** A default install likely carries **about 12–13k always-on tokens, about three times what `audit` reports**. No benchmark measures answer quality or routing accuracy.
- **Growth.** "Self-growing" is a prompt contract with no evals and a single version number for all plugins. Codex, Cursor and Gemini are supported only by convention. Meanwhile, 2025–2026 platforms now ship semver tags, rename maps, dependency bundles, deferred tool search and shared SKILL.md/AGENTS.md standards that the toolkit could generate output for.

The recommended order is: security fixes on the tip before merging, then honest token accounting and evals, then versioned, eval-gated growth with generated adapters for each client, then codemap precision work.

## One linear stack ships a marketplace, a router and a repo map

All commits are dated 2026-11-02, and `git merge-base --is-ancestor` confirms that `main` is an ancestor of every branch. The tip's diff against `main` is **118 files, +26,059 lines**, of which codemap is roughly 20k. That makes "which branch should I contribute to" a simple question: cut new work from `claude/csharp-rust-precision` and treat the intermediate branches as redundant once the tip merges ([commit 1310ad7](https://github.com/gimarais/ai-toolkit/commit/1310ad7)). One merge side effect needs a decision first. `main` currently holds repo-level Copilot agents (`.github/agents/doc-*.agent.md`) and a `doc-coauthor.prompt.md` prompt. The stack moves the agents into `plugins/doc-coauthor/`, turns the orchestrator agent into a skill and deletes the prompt, so merging removes them from `main`. No pull requests were found for any branch, although a permission-limited API response cannot be ruled out.

| Branch | What it added | `toolkit.py` | Skills |
|---|---|---|---|
| sleepy-cerf-pluea6 | Marketplace, `build/validate/catalog/install/adopt/promote/sync/status`, kickoff + harvest, plugins | 1,102 lines | 44 |
| codemap-ecosystem | codemap plugin, `doctor`, `audit`, user-level install targets, install ledger, first 28 tests | 1,652 lines | 45 |
| change-review | `codemap review`, change-map GitHub Action, `adopt --review-workflow` | 1,696 lines | 46 |
| csharp-rust-precision (tip) | C#/Rust structural parsers, benchmark fixes, Roslyn-scale performance, removal of life-and-career plugin | unchanged | 34 |

The ecosystem layer treats `toolkit.json` as the single source of truth. From it, `build` generates a Claude manifest (`.claude-plugin/plugin.json`) and a Copilot manifest (root `plugin.json`) for every plugin, two identical marketplace files, and the README tables. `validate` lints names, description lengths, agent filenames, hook-event casing and proprietary-licence markers ([toolkit.py L447-555](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L447-L555)). `catalog` shallow-clones seven upstream marketplaces into a **1,451-row `catalog.tsv`** that the router greps instead of reading. `install` targets five locations and, **by default, also installs all 26 upstream "profile" plugins** ([toolkit.py L915-922](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L915-L922)).

"Cross-LLM" in practice means native support for Claude Code and GitHub Copilot. The author states that the Copilot CLI and VS Code paths were never run ([docs/platforms.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/docs/platforms.md#L20)). For Codex, Cursor and Gemini, the integration is a symlink into `~/.agents/skills` plus an `AGENTS.md` pointer. Nothing is generated in their native formats ([toolkit.py L929-949](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L929-L949)).

The "self-growing" behaviour is mostly prose. Kickoff makes loading `harvest` mandatory on every run. Harvest scans the session for recurring procedures, gaps and repeated corrections, then writes at most three artefacts (skill, agent, hook or route) "without asking". Committing them needs the user's yes ([harvest SKILL.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/kickoff/skills/harvest/SKILL.md#L8-L99)). Three mechanisms enforce it:

- A Claude-only `Stop` hook blocks once per route if no harvest block was written ([harvest_check.py](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/kickoff/hooks/harvest_check.py#L1-L81)).
- A SessionStart hook runs `doctor` once a day.
- A weekly CI job refreshes the catalog.

There is no evidence yet that the loop has produced an artefact. `catalog/gaps.md` holds three rows, all from build day.

codemap is the most mature part. Python is parsed with `ast`. C# and Rust have hand-written structural parsers that, measured against a tree-sitter oracle, reach **99.9% recall and 100% precision on 25,866 C# declarations, and 100% recall and 99.6% precision on 11,625 Rust items**. The other 11 languages use regex patterns over masked text, and their accuracy is "not yet measured" ([docs/codemap.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/docs/codemap.md#L57-L64)).

Ranking reimplements Aider's design: a def/ref file graph, PageRank, and a default budget of about 1k tokens ([Aider repomap](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/docs/repomap.md)). What codemap adds is persistence (git-driven incremental refresh), a query surface (`refs/callers/impact`), and a single-tool MCP server whose schema costs about 150 tokens ([mcp.py](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/scripts/codemap_core/mcp.py#L1-L28)). On dotnet/roslyn (35,451 files), the tip cut a full index from over 6 minutes to **126 s, peak memory from 1.6 GB to 0.68 GB, and no-change queries to 0.17 s** ([docs/codemap.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/docs/codemap.md#L108-L119)).

The change-review layer works in three steps. It diffs the symbols on each side of a change and finds import-aware "callers outside the diff". It gives each file a hand-weighted 0–100 risk score. It then renders text, a token-budgeted context pack, Markdown with Mermaid, HTML and JSON. A composite action posts the result as a sticky PR comment ([review.py](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/scripts/codemap_core/review.py#L473-L513); [action.yml](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/.github/actions/change-map/action.yml#L39-L95)).

## The default install pays ~12k always-on tokens the audit never counts

Token economy is an explicit goal throughout the toolkit, and many of its mechanisms match current best practice:

- At most three judgment skills are loaded up front.
- The catalog is searched with grep, never read whole.
- Breadth work is delegated to read-only subagents that must answer in under 40 lines.
- MCP follows a one-tool rule, because "every tool schema is paid on every request".
- `audit` reports the always-on cost of each bundle and flags over-long descriptions and overlapping skills ([kickoff SKILL.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/kickoff/skills/kickoff/SKILL.md#L85-L92); [toolkit.py L1487-1574](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L1487-L1574)).

The weakness is what the accounting leaves out. `audit` reports **~862 tokens for core, ~3,358 for dev and ~4,066 for full**. It ignores the 26 upstream profile plugins that `install` adds by default. Those contribute 132 skills, agents and commands, whose listings come to **about 8,632 tokens even with descriptions truncated to 400 characters** ([catalog/index.json](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/catalog/index.json)). Add `AGENTS.md` (~640 tokens) and kickoff's own ~2,925-token body, which loads on every substantial task, and the realistic fixed cost is several times the headline. This is an estimate using the toolkit's own chars/4 heuristic; no exact tokenizer counts were available.

The cost matters more than the raw number suggests because of how Claude Code budgets skill listings. The listing budget **scales at 1% of the model's context window**. When it overflows, descriptions are dropped starting with the least-invoked skills, and only names survive ([Claude Code skills docs](https://code.claude.com/docs/en/skills)). A maximal install can therefore **silently strip the toolkit's own trigger descriptions**. The router stops working, and nothing reports an error. Commit 94226ea already deleted the 12-skill life-and-career plugin to bring the full bundle from ~5,260 to ~4,070 tokens, so the author is aware of the pressure ([commit 94226ea](https://github.com/gimarais/ai-toolkit/commit/94226ea)). Removing content is not the only remedy, though.

### Progressive disclosure is specified but barely used

The Agent Skills standard defines three tiers: about **100 tokens of metadata per skill**, a body under 5,000 tokens and 500 lines, and reference files one level deep that cost nothing until they are read ([agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)). Claude Code adds two details that change how bodies should be written. A loaded body stays in the conversation as "a recurring token cost". After compaction, only the **first 5,000 tokens of each skill (25,000 combined)** are re-attached ([Claude Code skills docs](https://code.claude.com/docs/en/skills)).

On the tip, only `kickoff` has a `references/` folder. The 28 judgment skills are single dense essays of 1,200–2,300 tokens each; mathematical-thinking, for example, packs ~1,916 tokens into 34 lines. Splitting each into a lean procedure-and-checklist `SKILL.md` plus a `references/` deep dive would cut the cost of loading a skill by roughly half. That figure is an estimate, not a measurement. The split would also put the imperative rules where compaction keeps them. Kickoff's 32-row routing table should move into a grepped reference file, as `catalog.tsv` already is.

The toolkit's portability rule limits frontmatter to `name` and `description` ([harvest SKILL.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/kickoff/skills/harvest/SKILL.md#L56-L64)). That rules out Claude-only flags such as `disable-model-invocation`. The same effect is still available through settings. Claude Code supports per-skill `skillOverrides` (`"name-only"`, `"user-invocable-only"`, `"off"`) ([Claude Code skills docs](https://code.claude.com/docs/en/skills)), so `adopt` and `install` can write those overrides for low-priority skills and leave the SKILL.md files portable.

### Platform features have overtaken some of the toolkit's hand-rolled thrift

Anthropic measured MCP tool definitions at about **55K tokens for a five-server setup**. Its Tool Search Tool cut that by **85% and raised MCP-eval accuracy for Opus 4.5 from 79.5% to 88.1%** ([Anthropic, advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use)). Presenting MCP tools as code files that the agent reads on demand cut one workflow from **150,000 to 2,000 tokens** ([Anthropic, code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)). Claude Code now defers MCP tool definitions by default, caps up-front descriptions and server instructions at 4,096 characters, and warns when a tool output exceeds 10,000 tokens ([Claude Code MCP docs](https://code.claude.com/docs/en/mcp)).

As a result, codemap's single-tool design matters less inside Claude Code than it did when the rule was written. It still pays off in Copilot, where no equivalent deferral was verified. The design has a real cost too: the command grammar is opaque, and arguments are not validated against a schema. The better move is to keep one tool but give it an enum-validated verb and keyword-first server instructions. The docs' advice to "prefer CLI tools" because they "don't add any per-tool listing" also supports codemap's CLI shim ([Claude Code costs docs](https://code.claude.com/docs/en/costs)).

The cheapest gain the toolkit does not yet ship is output-filter hooks. A PreToolUse hook that pipes test-runner output through `grep -A 5 -E '(FAIL|ERROR|error:)' | head -100` takes such output "from tens of thousands of tokens to hundreds" ([Claude Code costs docs](https://code.claude.com/docs/en/costs)).

Evidence on always-loaded context also argues for restraint. Gloaguen et al. (ICLR 2026) found that repository context files **gave no improvement in task success while raising inference cost by more than 20%**. LLM-generated overview files were the worst performers ([arxiviq summary](https://arxiviq.substack.com/p/evaluating-agentsmd-are-repository)). The toolkit should keep `AGENTS.md` minimal and never inject codemap's `overview` into always-on files. Codex stops reading the `AGENTS.md` chain at a **32 KiB byte cap**, so the budget check should count bytes, not lines ([Codex AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)).

Prompt caching sets one more rule. The cache prefix runs tools → system → messages, a change at any level invalidates everything after it, and cache reads cost **0.1x base input (0.05x on Opus 5.5)** ([prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)). Hooks must therefore never change the tool list mid-session. Volatile SessionStart text, such as the daily doctor summary and the open-gap count, should stay short and come last.

### codemap's savings are real but measured against strawmen

An independent reproduction on requests, cobra and ripgrep **matched the published per-row numbers exactly**. For example, cobra `ExecuteC` went from 65,252 to 640 tokens, and ripgrep `HEAD~30` review from 245,130 to 8,022. All of these benchmarks count tokens only ([tests/bench_codemap.py](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/tests/bench_codemap.py#L7-L105)). They have four specific weaknesses:

- **Unrealistic baseline.** The symbol baseline reads whole files that a modern agent would read with offset and limit.
- **Circular orientation baseline.** The orientation baseline picks its "central files" using codemap's own ranking.
- **Budget-capped review pack.** The review pack is hard-capped at about 8k tokens, so the **96.5% "saving" largely restates the budget**. The docs themselves call it "a triage view, not a full review" ([docs/change-review.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/docs/change-review.md#L56-L78)).
- **Inflated in-product counter.** The in-product "avoided" counter credits whole-file tokens for every file listed in a result ([queries.py](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/scripts/codemap_core/queries.py#L179-L190)).

Current evaluation practice grades retrieval quality instead. SWE-Explore scores explorers on line-level precision and recall, file hits and context efficiency across 848 issues in 10 languages. It finds agentic explorers a tier above classical retrieval, but **line recall stays low at roughly 0.14–0.23** ([hyper.ai summary](https://hyper.ai/en/papers/2606.07297)). That figure comes from an aggregator and should be checked against the paper. The highest-value codemap contribution is therefore a quality-aware harness. It would measure file hit@k and line precision/recall at equal budgets, run A/B agent trials with and without codemap, and measure attention-item recall on bug-bearing PRs.

Three precision upgrades follow:

- **Optional LSP/SCIP backends** for `refs/callers/impact`. Claude Code ships official LSP plugins for 13 languages but "doesn't start plugin language servers" in cloud sessions ([Claude Code code intelligence](https://code.claude.com/docs/en/plugins/code-intelligence.md)). That leaves codemap's stdlib path as a genuine differentiator in the cloud, while a precise backend can take over wherever one runs.
- **Wider extraction evals.** Extend `tests/eval_extraction.py` to TS/JS, Go and Java.
- **Task-conditioned ranking.** Add a `map --query` that seeds personalised PageRank from FTS hits on the issue text. This is the hybrid lexical-plus-graph localisation behind RepoGraph and LocAgent; LocAgent reports **92.7% file-level accuracy** ([LocAgent, arXiv 2503.09089](https://arxiv.org/html/2503.09089v1)).

Claude Code's telemetry makes measuring the skill layer itself possible now. `claude_code.token.usage` carries `skill.name`, `plugin.name` and `mcp_server.name` attributes ([Claude Code monitoring docs](https://code.claude.com/docs/en/monitoring-usage)). `/skill-doctor` flags skills that are never invoked, and skill-creator's benchmark mode compares pass rate and tokens with and without a skill ([Claude Code skills docs](https://code.claude.com/docs/en/skills)).

## Self-growth runs on prose; 2026 platforms supply the missing machinery

The harvest loop is sound, and its human gate is deliberately slow: the model writes, the user commits, and other devices `sync`. Three of its supports are weak, though. Pruning relies on git age and Jaccard overlap between descriptions, not on usage. `promote` copies files without evaluating them. And **every plugin shares one version (2.3.0)** because no plugin entry overrides `cfg["version"]` ([toolkit.py L263, L300](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L263)).

The shared version collides with how Claude Code delivers updates. Users receive a new copy only when the computed version changes; "pushing commits without bumping a set `version` delivers nothing" ([Host and maintain a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md)). A harvested skill therefore reaches no plugin-installed user until someone bumps the global version. When someone does, every plugin re-downloads together. Removals are a related gap. The deleted `life-and-career` plugin has no retirement entry, although Claude Code provides an append-only `renames` map (old → `null`) plus `forceRemoveDeletedPlugins` for exactly that case ([Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)).

Claude Code now has real package-manager semantics, and the toolkit should adopt them rather than keep its own:

- Per-plugin tags named `<plugin>--v<version>`, created by `claude plugin tag --push`, which validates first and refuses dirty trees.
- Dependency ranges in npm-semver syntax, resolved against those tags.
- Bundles defined as a plugin containing nothing but a `dependencies` array.
- Full-SHA pins (40 characters) for git sources and `sha256` for archives.
- `stable`/`latest` release channels run as two catalogs.
- `relevance` blocks that let Claude Code suggest a plugin when a project matches ([Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md); [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)).

Mapped onto the repo, the `bundles` block in `toolkit.json` becomes generated bundle plugins, and the upstream profile becomes pinned dependencies. Claude Code then handles installation natively instead of `toolkit.py` shelling out to `plugin install` 26 times. One trust boundary must be preserved: cross-marketplace dependencies install only when they are allow-listed in `allowCrossMarketplaceDependenciesOn`.

### Make "cross-LLM" a build output instead of a convention

Skills are now the shared unit across clients. Anthropic published Agent Skills as an open standard on 2025-12-18, and the Linux Foundation's Agentic AI Foundation became the neutral home of MCP and AGENTS.md on 2025-12-09 ([SiliconANGLE](https://siliconangle.com/?p=724434); [Codex skills ecosystem](https://codex.danielvaughan.com/2026/03/27/codex-cli-skills-ecosystem/)). The packaging layer has not converged.

- **Codex** uses `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` ([xairouter guide](https://xairouter.com/en/blog/codex-plugins-guide)).
- **Gemini CLI** uses `gemini-extension.json`, and its gallery auto-indexes tagged repos that pass validation ([Gemini extension reference](https://geminicli.com/docs/extensions/reference/)).
- **Cursor** uses `.mdc` rules with `globs`, `description` and `alwaysApply` ([mer.vin deep dive](https://mer.vin/2025/12/cursor-ide-rules-deep-dive/)).

The toolkit already generates two manifests per plugin from one source, so extending `build` to emit the Codex, Gemini and Cursor formats is a natural increment ([toolkit.py L254-289](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L254-L289)). Generating `.mdc` files that scope rules by description, rather than `alwaysApply`, matters for cost: Cursor loads `AGENTS.md` and `CLAUDE.md` together, so duplicated content is paid twice. One caveat applies. The Codex and Cursor format details come from secondary sources because the official docs were unreachable during research, so each generated adapter needs a CI job that runs the real CLI's validator before it is advertised. The Copilot harvest gap closes the same way: Copilot exposes an `agentStop` event that has no `harvest_check` equivalent today ([docs/platforms.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/docs/platforms.md#L59)).

### Gate growth on evals, in small deltas

The best 2025–2026 evidence on self-improving context favours incremental curation over rewriting. ACE treats context as an evolving "playbook" maintained by separate Generator, Reflector and Curator roles. It uses itemised delta updates to avoid "brevity bias" and "context collapse", and reports **+12.3% over ReAct+ICL** ([ACE, arXiv 2510.04618](https://arxiv.org/abs/2510.04618)). Harvest's existing limits (at most three artefacts and one prune per run) already fit that philosophy. Two pieces are missing. First, a Reflector/Curator split, so the agent that experienced the session is not the only judge of what it learned. Second, an eval gate.

Anthropic recommends evaluation-first skill development with at least three evals, tested across model tiers ([Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)). skill-creator tunes descriptions against should-trigger and near-miss prompts using a 60/40 train/test split ([smartscope guide](https://smartscope.blog/en/generative-ai/claude/skill-creator-eval-pipeline-guide/)).

A practical pipeline has six stages:

1. Harvest writes to a staging branch or worktree, never to the live checkout.
2. `validate` and `skills-ref validate` run.
3. A routing eval runs: task prompts mapped to expected skills, with a precision/recall gate.
4. A with-skill versus without-skill uplift check runs.
5. A human reviews the change as a PR.
6. `claude plugin tag` creates the release.

Usage telemetry closes the loop. Skills that are never invoked, or that show no uplift, become removal candidates retired through `renames`, instead of being pruned by git age. A Claude Code skills doc mentions a `claude plugin eval` grader, but a second researcher found no reference page for it, so it should be treated as unverified until tested.

## Three confirmed codemap holes and an unpinned supply chain come first

The 2025–2026 threat record shows that skill and plugin marketplaces are now active supply-chain targets:

- **Snyk's ToxicSkills** found security issues in **36.82% of 3,984 skills** ([Snyk](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)).
- **A USENIX Security 2026 study** confirmed 157 malicious skills among 98,380. One actor accounted for **54.1% of cases through brand impersonation**, and advanced attacks abused platform hooks and permission flags ([arXiv 2602.06547](https://arxiv.org/html/2602.06547v1/)).
- **Trail of Bits** bypassed every skill scanner it tested, three of four in under an hour, and recommended curation, controlled contributors and version pinning ([Trail of Bits](https://blog.trailofbits.com/2026/06/03/the-sorry-state-of-skill-distribution/)).
- **Cisco's own documentation** says its rule engine alone catches about 7.7% of malicious skills ([PyPI cisco-ai-skill-scanner](https://pypi.org/project/cisco-ai-skill-scanner/2.2.1/)).
- **The s1ngularity/Nx malware** invoked locally installed `claude` and `gemini` CLIs with permission-skipping flags to hunt for secrets across **2,180 GitHub accounts** ([BleepingComputer](https://bleepingcomputer.com/news/security/ai-powered-malware-hit-2-180-github-accounts-in-s1ngularity-attack)).
- **CVE-2025-59536** let hooks in a repo's `.claude/settings.json` run before the trust prompt ([Check Point](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/)).

Anthropic's own position is blunt: an installed plugin can execute arbitrary code with the user's privileges, and permission rules and the sandbox do not cover code a plugin runs itself ([Claude Code plugin security](https://code.claude.com/docs/en/plugins/security)). The toolkit installs plugins, hooks and MCP servers, so it sits squarely inside this threat model.

### The codemap holes break Claude Code's own permission boundary

The research reproduced three codemap issues in a scratch environment.

- **Symlinks are followed.** `read_text` calls `read_bytes()` with no symlink or containment check, and `list_files` accepts whatever `git ls-files` lists, including symlinks. A committed `evil.py -> ../outside_secret.txt` was indexed, and `show notes.txt:1-2` printed `/etc/os-release` ([util.py L195-233](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/scripts/codemap_core/util.py#L195-L233)). Because the read happens inside the MCP server, a malicious repo can surface `~/.ssh` or cloud credentials into model context **without ever hitting Claude Code's Read permission rules**.
- **The size cap does nothing.** `CODEMAP_MAX_FILE_BYTES` is defined and documented but never referenced ([util.py L41](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/scripts/codemap_core/util.py#L41)). A committed `zero.js -> /dev/zero` exhausted memory. Since the SessionStart hook spawns `codemap index` automatically, opening a hostile repo starts a runaway process without any prompt ([session_start.py](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/hooks/session_start.py#L56-L65)). Any PR can also kill the change-map CI job.
- **The MCP tool can write and re-target.** The MCP `cmd` string is fed to the full CLI parser, so `review --out FILE` writes anywhere and `--repo`/`--db` point the tool at other locations ([cli.py L181-198](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/scripts/codemap_core/cli.py#L181-L198)). A tool that users would naturally auto-approve as "read-only navigation" thus becomes an unprompted file writer.

Two smaller issues sit alongside these. Unescaped backticks in file paths let a PR inject Markdown into the bot's sticky comment ([review_render.py L221-229](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/scripts/codemap_core/review_render.py#L221-L229)). And `actions/checkout` keeps its default `persist-credentials` while untrusted files are parsed.

Much of codemap is done correctly. It never executes repo code, it calls git without a shell and with `--no-ext-diff`, the action uses `pull_request` rather than `pull_request_target` and passes inputs via `env:`, the HTML report renders via `textContent`, and `sql` opens the database read-only.

### The growth loop is also the persistence channel

The ecosystem layer's riskiest property is a chain. Simon Willison's "lethal trifecta" describes when an agent becomes exploitable for exfiltration: private data, untrusted content and an outbound channel in one session ([Willison](https://simonwillison.net/2025/nov/2/new-prompt-injection-papers)). In this toolkit, untrusted session content (a web page, a repo file, or one of the **202 community-sourced rows** in a catalog that agents grep during routing) can steer harvest. Harvest then writes a skill, or a hook "calling one shared script", into the toolkit checkout without asking ([harvest SKILL.md](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/kickoff/skills/harvest/SKILL.md#L38-L64)). Because installs symlink skills and point hooks at absolute paths in that checkout, the change is **live in every client at the next session, before any commit or review** ([toolkit.py L767-853](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L767-L853)).

The rest of the trust surface is unpinned:

- The `curl | bash` installer clones `main` with no tag or checksum ([install.sh](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/install.sh#L4-L28)).
- The marketplaces in `toolkit.json` carry no ref or SHA ([toolkit.json L51-59](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/toolkit.json#L51-L59)).
- `sync` runs `git pull` and updates every plugin with no diff review.
- Actions are pinned by tag rather than by SHA. Mutable tags are what exposed more than 23,000 repos in the tj-actions compromise ([Decryption Digest](https://www.decryptiondigest.com/blog/github-actions-security-hardening)).
- The `adopt` template defaults `--review-ref` to `main` ([toolkit.py L1183-1208](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L1183-L1208)).
- `_git_clone` passes upstream-supplied URLs with no `--` separator. Exploitability is unverified.
- Skill path containment uses a fragile string prefix ([toolkit.py L194-216, L560-568](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L194-L216)).
- The Copilot MCP config grants `"tools": ["*"]` ([copilot-mcp.json](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/plugins/codemap/copilot-mcp.json#L7)).
- `adopt --mode vendor` silently runs `rmtree` over customised vendored skills, even though `doctor` treats such differences as worth keeping ([toolkit.py L1228-1235](https://github.com/gimarais/ai-toolkit/blob/claude/csharp-rust-precision/scripts/toolkit.py#L1228-L1235)).

### Controls that fit the architecture

The OWASP Agentic Skills Top 10 maps directly onto these findings: AST01 malicious skills, AST02 supply chain, AST03 over-privileged skills, AST07 update drift and AST10 cross-platform reuse ([OWASP AST10](https://owasp.org/www-project-agentic-skills-top-10/docs/OWASP-Agentic-Skills-Top10-v0.5.pdf)). It should frame a new `SECURITY.md`; the repo has none.

The architectural defences come from the prompt-injection design-patterns paper (Dual LLM, Plan-Then-Execute, Context-Minimization) ([arXiv 2506.08837](https://arxiv.org/abs/2506.08837)) and from Meta's Rule of Two: at most two of untrusted input, sensitive access and state change per session ([Willison](https://simonwillison.net/2025/nov/2/new-prompt-injection-papers)). codemap's read-only `code-navigator` subagent is already the right shape for a Dual LLM reader. The change-review action is already a deterministic, non-LLM step. Any future LLM reviewer layered on the review pack should keep that split: an LLM reads the pack as data, and a script with fixed arguments posts the comment.

One design tension deserves a direct fix. The portability rule omits `tools` from agents because tool IDs differ between clients (Claude `Read`/`Grep`, Copilot `read`/`search`), which gives up least privilege. Because `build` already emits a separate manifest for each client, it can **generate a tool allowlist for each client** and get portability and least privilege at the same time.

Scanners still belong in CI: Cisco skill-scanner, Snyk agent-scan, secret scanning and zizmor ([Cisco skill-scanner](https://github.com/cisco-ai-defense/skill-scanner)). Given the bypass evidence, they must sit in front of CODEOWNERS review of `hooks/`, `scripts/`, MCP configs and `toolkit.json`, never replace it.

## Prioritized roadmap tied to files and branches

All work should branch from the tip `claude/csharp-rust-precision`, since it contains the whole stack. The "origin" column names the branch that introduced the code, which matters only if a reviewer asks for the +26k-line merge to be split. P0 items should land before `main` is fast-forwarded, because merging makes `catalog-refresh.yml` (with `contents: write`) and `change-map.yml` live.

| # | Priority | Contribution | Files (origin branch) | Evidence | Effort |
|---|---|---|---|---|---|
| 1 | P0 | Refuse symlinks and non-regular files; require `realpath` inside root; enforce `MAX_FILE_BYTES` via `st_size`; add PoC regression tests | `plugins/codemap/scripts/codemap_core/util.py` (`read_text`, `list_files`), `queries.py` `show`, `review.py` file reads, `resolve.py` config readers; `tests/test_codemap.py` (codemap-ecosystem) | PoC: host file read, `/dev/zero` OOM | S |
| 2 | P0 | Strip `--out/--db/--repo` from MCP calls, enum-validate the verb, then advertise `readOnlyHint`; replace Copilot `"tools":["*"]` | `codemap_core/cli.py` L181-198, `mcp.py`, `plugins/codemap/copilot-mcp.json` (codemap-ecosystem) | PoC: arbitrary write, sibling-repo read | S |
| 3 | P0 | Escape backticks in Markdown paths; `persist-credentials: false`; SHA-pin all actions; default `--review-ref` to a tag/SHA | `review_render.py` L221-229, `.github/workflows/*.yml`, `.github/actions/change-map/action.yml`, `toolkit.py` L1183-1208/L1661 (change-review) | tj-actions; Markdown injection | S |
| 4 | P0 | Quarantine harvest: never auto-write hooks or scripts; write all artefacts to a staging worktree/branch; `doctor` flags uncommitted changes under `hooks/` and `scripts/`; point symlinked installs at a release worktree, not the working checkout | `plugins/kickoff/skills/harvest/SKILL.md`, `toolkit.py` `doctor` L1304-1468 and install L767-853 (sleepy-cerf) | Injection → live hook chain | M |
| 5 | P0 | Harden ecosystem plumbing: `--` and leading-dash check in `_git_clone`; `Path.is_relative_to` containment; refuse to overwrite locally modified vendored skills; default `install` to `core` with upstream opt-in | `toolkit.py` L194-216, L560-568, L1228-1235, L891/L1638 (sleepy-cerf, codemap-ecosystem) | Unpinned 26-plugin default | S |
| 6 | P0 | Add `SECURITY.md` (trust model, AST10 mapping, canonical install URL), `CODEOWNERS` for `hooks/`, `scripts/`, MCP configs and `toolkit.json`, and a PR template requiring eval results | repo root, `.github/` (new) | No security doc exists | S |
| 7 | P1 | Make `audit` honest: count installed upstream listings, real MCP schema bytes, kickoff body, `AGENTS.md` bytes (Codex 32 KiB); warn against the 1%-of-context listing budget | `toolkit.py` `audit` L1487-1574 (codemap-ecosystem) | ~12–13k actual vs ~4k reported | S |
| 8 | P1 | Progressive-disclosure refactor: lean `SKILL.md` plus `references/` for the 28 judgment skills; move the kickoff routing table to `references/routes.md`; write `skillOverrides` in `adopt` for low-priority skills | `plugins/{engineering-craft,thinking-tools,communication-and-leadership}/skills/*`, `plugins/kickoff/skills/kickoff/SKILL.md` (sleepy-cerf) | 5k-token compaction cutoff | M |
| 9 | P1 | Routing and trigger eval harness (prompt → expected skills, near-miss negatives) run in CI with a precision/recall gate | new `tests/evals/`, `.github/workflows/validate.yml` | No routing measurement exists | M |
| 10 | P1 | Quality-aware codemap benchmarks: fair grep+offset baselines, SWE-Explore-style line P/R, attention-item recall, A/B agent runs; correct the "~96%" README claim | `tests/bench_codemap.py`, `docs/codemap.md`, `docs/change-review.md`, `plugins/codemap/README.md` (codemap-ecosystem, tip) | Token-only, circular baselines | M |
| 11 | P1 | Ship output-filter PreToolUse hooks (test runners, linters, logs) as a small plugin with a fixed, reviewed script | new `plugins/output-filters/`, `toolkit.json` | "tens of thousands → hundreds" | S |
| 12 | P2 | Per-plugin versions in `toolkit.json`; `claude plugin tag` releases; generated per-plugin `CHANGELOG`; `validate` fails when a changed plugin's version is unchanged; `renames: {"life-and-career": null}` | `toolkit.json`, `toolkit.py` L263/L300 and `build`, `.claude-plugin/marketplace.json` (sleepy-cerf, tip) | No version change means no update is delivered | M |
| 13 | P2 | Pinned upstream: `ref`/`sha` per marketplace and profile entry; turn `catalog-refresh` into a bump-PR bot with a diff of descriptions; replace `bundles` and profile with generated bundle and dependency plugins | `toolkit.json` L51-98, `.github/workflows/catalog-refresh.yml`, `toolkit.py` `install` (sleepy-cerf) | AST02/AST07; native dependency support | M |
| 14 | P2 | Generate Codex (`.codex-plugin/`, `.agents/plugins/marketplace.json`), Gemini (`gemini-extension.json`) and Cursor (`.cursor/rules/*.mdc`) adapters plus per-client tool allowlists; add a Copilot `agentStop` harvest check; CI jobs running each real CLI | `toolkit.py` `build` L254-289/L414-442, `plugins/kickoff/hooks/` (sleepy-cerf) | Cross-LLM by convention only | L |
| 15 | P2 | Eval-gated, ACE-style harvest: itemised delta edits, a separate reviewer pass, `promote` runs evals; prune by OTel `skill.name` usage rather than git age | `harvest/SKILL.md`, `toolkit.py` `promote` L1249-1278 and `audit` | ACE +12.3%; no usage data | M |
| 16 | P2 | Security CI gate: Cisco skill-scanner, agent-scan, gitleaks, zizmor, Bandit, and a content lint for bidi/zero-width characters, whitespace padding and binaries; signed tags plus artifact attestations on release | `.github/workflows/` (new `security.yml`, release job) | Scanner bypass means layering | M |
| 17 | P3 | `map --query` (FTS-seeded personalised PageRank) returning ranked line regions; recover the common-API edges dropped by the 20-file and 40-edge caps for `impact` | `codemap_core/queries.py` L191-300, `store.py` L47-48/L448-504, `graph.py` (codemap-ecosystem, tip) | RepoGraph/LocAgent; line-recall gap | M |
| 18 | P3 | Optional LSP/SCIP backend with per-answer confidence labels; extend `eval_extraction.py` to TS/JS, Go and Java | `codemap_core/` (new backend module), `tests/eval_extraction.py`, `catalog/gaps.md` (tip) | 11 languages unmeasured | L |
| 19 | P3 | Calibrate change-review risk weights against fix-commit history; report precision@k of the review order | `codemap_core/review.py` L473-513 (change-review) | Hand-tuned weights | M |
| 20 | P3 | CI matrix for Windows, macOS and Python 3.9; tests for `catalog` against a fixture, `promote` clashes, `validate` negatives, install/adopt idempotence | `.github/workflows/validate.yml`, `tests/test_toolkit.py` | Claimed but untested support | M |

## Conclusion

The toolkit's best idea and its biggest risk are the same lever. Kickoff and harvest turn experience into always-loaded context. Done well, that is the self-improving playbook the ACE line of research rewards. Done blindly, it adds bloat that silently overflows the listing budget, or gives an attacker persistence through a hook. What separates the two outcomes is not more prompt rules but the measurement and provenance the stack lacks today. Evals tell growth apart from bloat. Pinning, staging and per-plugin versions tell it apart from compromise. That is why the roadmap puts these items before any new skills, and why the P0 security fixes, which are small, should block the merge.

The platforms are also absorbing the toolkit's hand-built thrift: deferred tool search, skill-listing budgets, native LSP and plugin semver now come from Claude Code itself. The durable value of ai-toolkit therefore shifts toward three things the platforms do not provide. The first is generating one source into every client's native format. The second is a zero-dependency code map that still works in cloud sessions, where LSP servers do not run. The third is curation backed by evidence. Two uncertainties should be closed early: the Codex and Cursor format details, which rest on secondary sources, and the real tokenizer cost of a default install, which is estimated here at chars/4.
