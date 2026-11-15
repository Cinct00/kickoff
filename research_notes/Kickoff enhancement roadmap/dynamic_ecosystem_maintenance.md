# Dynamic, Self-Growing Ecosystem of Agent Skills, Plugins and MCP Servers: Standards, Registries, Tooling and Maintenance (state as of 2026-11-03)

> Research-environment note: in this session `agentskills.io`, `modelcontextprotocol.io` and `developers.openai.com` could not be reached (DNS blocked by the session network allowlist), and the GitHub API was not enabled for `anthropics/*`, `agentskills/*` or `modelcontextprotocol/*` repos. The Agent Skills spec was read from its GitHub raw mirror. MCP-registry and Codex details therefore rely on secondary sources and are flagged. Claude Code plugin facts come from the official docs at code.claude.com, fetched directly, and are the most reliable part of these notes.

## Q1. Standards and formats: Agent Skills, AGENTS.md, Claude Code plugins/marketplaces, Gemini CLI extensions, Codex plugins, MCP + Registry, A2A. Where are they converging, and how should one source of truth produce per-platform outputs?

### Takeaway
Skills are now the shared unit across platforms. SKILL.md (Agent Skills spec) and AGENTS.md (now under the Linux Foundation's Agentic AI Foundation) are read by Claude Code, Codex, Gemini CLI, Cursor, Copilot and others. MCP is the shared tool protocol. The packaging layer is still vendor-specific, and the formats are close but not identical: Claude `.claude-plugin/plugin.json` + `marketplace.json`, Codex `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json`, Gemini `gemini-extension.json`. So a toolkit should keep skills/MCP configs as spec-compliant canonical sources and generate a thin per-platform manifest for each target.

### Cited Findings

**Agent Skills (SKILL.md) open standard**
- A skill is a directory with one required `SKILL.md` (YAML frontmatter followed by Markdown). Optional dirs are `scripts/`, `references/` and `assets/`, and other files are allowed. — [agentskills spec (GitHub raw)](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- Frontmatter, required fields:
  - `name`: at most 64 chars; lowercase letters, digits and hyphens; no leading, trailing or consecutive hyphens; "Must match the parent directory name."
  - `description`: "Max 1024 characters. Non-empty." It should say what the skill does and when to use it, with keywords for matching.
- Frontmatter, optional fields:
  - `license`
  - `compatibility`: "Max 500 characters", for environment requirements only.
  - `metadata`: a string-to-string map; use key names unlikely to collide.
  - `allowed-tools`: experimental, a space-separated string; support varies by agent.
  — [agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- Progressive disclosure has three stages:
  1. Metadata, about 100 tokens per skill, loaded at startup.
  2. The full SKILL.md body on activation, recommended under 5,000 tokens and under 500 lines.
  3. Resources, loaded only when needed. File references should stay one level deep.
  — [agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- The reference validator is `skills-ref validate ./my-skill`. It checks frontmatter validity and naming conventions. — [agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- The spec has no `version` field. Versioning goes in `metadata` or in the enclosing plugin. — inferred from the field list in [agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- Anthropic published Agent Skills as an open standard on 2025-12-18. Adoption is reported at "over 26" to "over 30" platforms by early 2026, and OpenAI and Microsoft are reported to have adopted SKILL.md in late Dec 2025. These figures come from secondary aggregators. — [Codex CLI skills ecosystem blog](https://codex.danielvaughan.com/2026/03/27/codex-cli-skills-ecosystem/); [inference.sh overview](https://inference.sh/blog/skills/agent-skills-overview); [denser.ai guide](https://denser.ai/blog/agent-skills-guide/)
- Skill paths by platform (secondary sources):
  - Codex reads `~/.codex/skills`.
  - Gemini CLI reads `.gemini/skills/` and the shared `.agents/skills/`. Gemini support is dated to January 2026.
  - Cursor reads project-level dirs, including `.agents/skills/`.
  - GitHub Copilot docs say skills work in the Copilot cloud agent, code review, the CLI and agent mode in VS Code/JetBrains.
  — [strapi.io](https://strapi.io/blog/what-are-agent-skills-and-how-to-use-them); [dev.to SKILL.md cross-tool](https://dev.to/fabwaseem/agent-skills-explained-how-to-write-a-skillmd-for-claude-code-cursor-codex-and-copilot-323p); [serghei.pl Agent Skills 101](https://blog.serghei.pl/posts/agent-skills-101/)
- Governance is contested. One source calls the spec "governed as a cross-platform specification"; another says "open" here means published and openly licensed, not independently governed. — [search synthesis of the sources above; see denser.ai](https://denser.ai/blog/agent-skills-guide/), [serghei.pl](https://blog.serghei.pl/posts/agent-skills-101/)

**AGENTS.md / Agentic AI Foundation (AAIF)**
- The Linux Foundation announced the AAIF on 2025-12-09. It is the neutral home for Anthropic's MCP, Block's goose and OpenAI's AGENTS.md. Other backers include AWS, Bloomberg, Cloudflare, Google and Microsoft. — [SiliconANGLE](https://siliconangle.com/?p=724434); [Privacy Guides](https://www.privacyguides.org/news/2025/12/24/the-linux-foundation-announces-formation-of-the-agentic-ai-foundation/); [i-programmer](https://www.i-programmer.info/news/105-artificial-intelligence/18614-agentic-ai-foundation-announced.html)
- AGENTS.md is read natively by Codex, Cursor, Copilot, Gemini CLI, Aider, Windsurf, Zed, Factory, Jules and 20+ others. Repo counts conflict: 40k+ (Dec 2025) vs 60k+ (2026 guide). — [codersera AGENTS.md guide 2026](https://codersera.com/blog/agents-md-complete-guide-2026/); [intuitionlabs](https://intuitionlabs.ai/articles/agentic-ai-foundation-open-standards)

**Claude Code plugins and marketplaces (official docs)**
- *Marketplace file and entries*
  - A marketplace is a directory or repo containing `.claude-plugin/marketplace.json`. Required fields are `name`, `owner` (with `name`) and `plugins[]`. Each entry needs `name` and `source`. — [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
  - Optional top-level fields: `$schema`, `description`, `version`, `metadata.pluginRoot`, `forceRemoveDeletedPlugins`, `allowCrossMarketplaceDependenciesOn`, `renames`. Unknown keys are silently ignored at load time; `claude plugin validate` reports them as warnings. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
  - Entry fields include `description`, `version`, `category`, `tags`, `strict` (default true), `relevance`, `dependencies`, `defaultEnabled`, `displayName`, `metadata` (free-form, not read), `headers` and `headersHelper`. An entry also accepts any plugin.json field. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Plugin sources*
  - Relative path (`./…`)
  - `github` (`repo`, `ref`, `sha`)
  - `url` (any git URL, plus `ref`/`sha`)
  - `git-subdir` (`url`, `path`, `ref`, `sha`; sparse/partial clone, built for monorepos)
  - `npm` (`package`, `version` semver/dist-tag, `registry`; install scripts never run)
  - `archive` (HTTPS zip plus `sha256` pin; v2.1.224+)
  - `command` (a local command prints the plugin dir; v2.1.229+)

  `sha` must be a full 40-char commit SHA. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Hosting and naming*
  - Marketplaces can be hosted on GitHub, any git host, a bare `marketplace.json` URL (relative-path entries then fail) or a shared filesystem.
  - `#<ref>` pins a catalog branch or tag, e.g. `org/repo#stable`.
  — [Host and maintain a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md)
  - Reserved names include `claude-plugins-official`, `agent-skills`, `anthropic-agent-skills`, `knowledge-work-plugins` and `claude-plugins-community`. Impersonating names and alternate spellings are refused. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Distribution to organizations*
  - Admins can require marketplaces via managed `extraKnownMarketplaces` and `enabledPlugins`, allowlist via `strictKnownMarketplaces` (supports `owner/*`, `hostPattern`, `pathPattern`) and block via `blockedMarketplaces`. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md); [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md)
  - Team/Enterprise plans can sync a private marketplace repo through claude.ai Organization settings. A plugin with a top-level `bin/` dir is rejected there. — [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md)
- *Cross-platform note*: `claude plugin validate` also warns about names that Claude Desktop rejects (max 128 chars; letters, digits, `.`, `_`, `-`). Validation now spans Claude surfaces. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)

**OpenAI Codex plugins (secondary sources only; official docs blocked)**
- The manifest is `.codex-plugin/plugin.json`. `skills/`, `assets/`, `.app.json` and `.mcp.json` sit at the plugin root. — [xairouter Codex plugins guide](https://xairouter.com/en/blog/codex-plugins-guide)
- Codex reads three marketplace catalogs:
  - the curated official Plugin Directory
  - a repo marketplace at `$REPO_ROOT/.agents/plugins/marketplace.json`
  - a personal marketplace at `~/.agents/plugins/marketplace.json`

  The cache lives at `~/.codex/plugins/cache/$MARKETPLACE/$PLUGIN/$VERSION/`. `codex plugin marketplace add` clones a git repo. — [Codex marketplace blog (Apr 2026)](https://codex.danielvaughan.com/2026/04/11/codex-marketplace-plugin-distribution/); [xairouter](https://xairouter.com/en/blog/codex-plugins-guide)
- `openai/skills` ships a `plugin-creator` skill that scaffolds plugins and updates `.agents/plugins/marketplace.json`. Third-party submissions to the directory were reported as "coming soon". — [skillselion plugin-creator](https://skillselion.com/skills/openai/codex/plugin-creator); [awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins)

**Gemini CLI extensions**
- Each extension needs `gemini-extension.json` at the repo or archive root. Skills bundled with the extension are auto-discovered. Hooks live in `hooks/hooks.json`, not in the manifest. — [Extension reference](https://geminicli.com/docs/extensions/reference/); [Build extensions](https://www.geminicli.com/docs/extensions/writing-extensions)
- *Install*: `gemini extensions install <source> [--ref] [--auto-update] [--pre-release] [--consent]` installs a copy. — [Extension reference](https://geminicli.com/docs/extensions/reference/); [Release extensions](https://geminicli.com/docs/extensions/releasing/)
- *Update*: `gemini extensions update --all` checks the GitHub "Latest release", and a `migratedTo` field lets an extension move repos. — [Extension reference](https://geminicli.com/docs/extensions/reference/); [Release extensions](https://geminicli.com/docs/extensions/releasing/)
- *Gallery*: the gallery auto-indexes public tagged repos daily if they pass validation; no submission step. — [Extension reference](https://geminicli.com/docs/extensions/reference/); [Release extensions](https://geminicli.com/docs/extensions/releasing/)

**MCP spec evolution (secondary sources; official site blocked)**
- The 2025-11-25 revision added experimental async Tasks, a formal extensions framework (capability negotiation) and tool definitions in sampling. It also added authorization extensions for enterprise-managed access and M2M OAuth client credentials. — [WorkOS on 2025-11-25](https://workos.com/blog/mcp-2025-11-25-spec-update); [MCP changelog](https://modelcontextprotocol.io/specification/latest/changelog)
- The 2026-07-28 revision is reported to:
  - remove the initialize handshake and protocol-level sessions (stateless)
  - move Tasks into an official extension that uses polling
  - deprecate HTTP+SSE
  - adopt a feature lifecycle policy with a minimum 12-month deprecation window

  Its final-release status was not confirmed from an official page. — [modelcontextprotocol.info 2026-07-28 changelog mirror](https://modelcontextprotocol.info/specification/2026-07-28/changelog/); [modelcontextprotocol.net mirror](https://modelcontextprotocol.net/specification/2026-07-28/changelog); [releases.sh index](https://releases.sh/modelcontextprotocol/mcp-blog)
- MCP Apps reportedly went GA in January 2026. The 2026 roadmap is organized around Working Groups, with governance maturation as a priority. — [releases.sh index](https://releases.sh/modelcontextprotocol/mcp-blog)

**Official MCP Registry (secondary sources)**
- The registry has been in preview since September 2025. Its API is v0.1, and an older Go package page says GA is still to come. GA status as of Nov 2026 is unverified. — [affine.pro registry guide](https://affine.pro/blog/mcp-registry-guide); [pkg.go.dev registry v1.0.0](https://pkg.go.dev/github.com/modelcontextprotocol/registry@v1.0.0)
- *Publishing*:
  - Install `mcp-publisher`, run `init` to generate `server.json`, then validate and publish.
  - `io.github.*` namespaces authenticate through a GitHub device flow; reverse-DNS namespaces (`com.brand/*`) prove ownership with a DNS TXT record.
  - For remote servers, only the namespace is verified, not the URL.

  — [roxyapi registry guide 2026](https://roxyapi.com/blogs/mcp-registries-where-to-list-your-server); [dev.to: publishing 7 servers](https://dev.to/zebudata/what-we-learned-publishing-7-mcp-servers-to-the-official-registry-1f7i); [MS Learn .NET quickstart](https://learn.microsoft.com/en-us/dotnet/ai/quickstarts/publish-mcp-registry)
- The 2025-12-11 server.json schema caps `title` and `description` at 100 chars. — [dev.to: publishing 7 servers](https://dev.to/zebudata/what-we-learned-publishing-7-mcp-servers-to-the-official-registry-1f7i)
- Downstream registries and directories (GitHub MCP Registry, ToolHive, Smithery, etc.) consume or extend the official registry. — [composio on GitHub MCP Registry](https://composio.dev/content/github-mcp-registry); [Stacklok ToolHive publish](https://docs.stacklok.com/toolhive/guides-registry/publish-servers); [apideck MCP directories 2026](https://www.apideck.com/blog/mcp-server-directories)

**A2A**
- A2A is a Google-originated protocol now under the Linux Foundation, but not explicitly under AAIF. A2A v1.0 is mentioned in an April 2026 update. — [intuitionlabs AAIF](https://intuitionlabs.ai/articles/agentic-ai-foundation-open-standards)

### Inferences
- *Canonical layout*: keep a `skills/<name>/SKILL.md` tree that passes `skills-ref validate` (lowest common denominator, readable by all major tools). Keep a canonical `mcp/<server>/server.json` that follows the MCP Registry schema.
- *Generated outputs*: generate `.claude-plugin/plugin.json` + `marketplace.json`, `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json`, `gemini-extension.json`, and per-tool MCP config snippets from one `toolkit.yaml` (name, version, description, components).
- *Name constraint*: the skill `name` must equal its directory name and be lowercase-hyphenated, so plugin and skill names should use the same rules everywhere.
- *Description lengths*: descriptions should be written to the tightest limit any target enforces: 100 chars for MCP Registry `server.json`, 1024 for SKILL.md.
- *Where to put versions*: Claude plugins honor `version` from plugin.json first; the Agent Skills spec has no version field. Put the semver in the plugin/extension manifests and mirror it into SKILL.md `metadata.version` for traceability.
- *Prefer shared paths*: use `.agents/skills/` and AGENTS.md where a platform honors them, so per-platform copies become symlinks or generated files rather than forks.

### Gaps
- Could not reach agentskills.io or `agentskills/agentskills` via the API to get the official adopter list, governance model or `skills-ref` release history. Allow `agentskills.io` in session network settings to verify.
- Could not read official Codex docs (developers.openai.com blocked), so Codex manifest fields, versioning and auto-update behavior are unverified.
- Could not confirm MCP Registry GA status, the current `server.json` schema version, or whether 2026-07-28 is final (modelcontextprotocol.io blocked).
- Did not find details on A2A Agent Card fields or versioning, or a Cursor plugin/marketplace format.

## Q2. Dynamic addition: on-demand discovery and loading, and agents that author or improve their own skills. What safeguards are needed?

### Takeaway
On-demand loading is now built into the platforms. Skills use progressive disclosure, tools use deferred tool search, and plugins have relevance-based suggestions and auto-updating marketplaces. A toolkit can therefore grow its catalog without bloating context, provided descriptions are good. The main self-improvement pattern is incremental, curated "playbook" evolution (ACE: Generator, Reflector, Curator) rather than wholesale rewrites. Any self-authored skill should still go through validation, evals and human-gated PRs before it reaches a shared marketplace.

### Cited Findings
- *Progressive disclosure*: only about 100 tokens of name and description per skill load at startup. Bodies load on activation and resources on demand, which is what makes large skill libraries feasible. — [agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- *Deferred tool search, API side*: Claude's tool search keeps tool schemas out of context. Tools are marked `defer_loading: true`, and the model gets a search tool, either regex (`tool_search_tool_regex_20251119`) or BM25 (`tool_search_tool_bm25_20251119`). It loads matching schemas on demand, and whole MCP servers can be deferred via `mcp_toolset` with per-tool overrides. These are secondary write-ups. — [oldeucryptoboi deep dive](https://oldeucryptoboi.substack.com/p/tool-search-deep-dive); [azukiazusa.dev](https://azukiazusa.dev/blog/trying-claude-tool-finder.md)
- *Deferred tool search, Claude Code defaults*: sources disagree.
  - One says MCP tools are deferred by default, with `tst-auto` and `standard` modes.
  - Another says deferral kicks in automatically when MCP tool descriptions exceed 10% of context.
  - The opt-out is variously given as `ENABLE_TOOL_SEARCH=false` or disallowing `MCPSearch`.

  Not every MCP server supports deferral. — [developersdigest MCP Tool Search](https://www.developersdigest.tech/guides/mcp-tool-search); [claudelog](https://claudelog.com/faqs/what-is-tool-search-in-claude-code/); [dev.to gentic_news](https://dev.to/gentic_news/how-claude-codes-tool-search-saves-90-of-your-context-window-1j1f)
- *Relevance-based suggestions*: a marketplace entry can carry a `relevance` block of project signals so that Claude Code suggests the plugin when a session matches. Users see these suggestions only when an admin lists the marketplace in `pluginSuggestionMarketplaces`. — [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md); [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Auto-update (Claude)*:
  - Background auto-update is off by default per marketplace. A user enables it in `/plugin` → Marketplaces, or an admin sets `"autoUpdate": true` in managed `extraKnownMarketplaces`.
  - Updates arrive only when the computed version changes.
  - Background checks never prompt for credentials; on failure the old checkout stays (`CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1`).
  — [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md)
- *Bundles*: a plugin that is only a `name` plus a `dependencies` array is a valid bundle. Installing it installs every dependency, and publishing a new bundle version adds plugins for everyone on the next update. — [Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md)
- *Install-time trust gates*:
  - Cross-marketplace dependencies install only if the root marketplace lists the target in `allowCrossMarketplaceDependenciesOn`, which stops one catalog from silently pulling in unreviewed ones.
  - `command` sources and `headersHelper` commands require explicit per-user acceptance of the exact command string, and are never run during bulk or background updates.
  — [Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md); [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md)
- *Gemini auto-update*: Gemini CLI supports `--auto-update` at install, and its gallery auto-ingests tagged repos daily after validation. — [Gemini extension reference](https://geminicli.com/docs/extensions/reference/)
- *ACE (Agentic Context Engineering), arXiv:2510.04618*:
  - Submitted 2025-10-06 by Zhang et al.; v3 revised 2026-03-29.
  - Treats contexts as evolving "playbooks" maintained by a Generator, a Reflector and a Curator.
  - Uses incremental delta updates, not full rewrites, to avoid "brevity bias" and "context collapse".
  - Reports +12.3% over ReAct+ICL and +11.9% over ReAct+GEPA in offline adaptation.

  ICLR 2026 venue per a secondary listing (unverified). — [arXiv abs](https://arxiv.org/abs/2510.04618); [arXiv html v3](https://arxiv.org/html/2510.04618v3); [LINER review](https://liner.com/en/review/agentic-context-engineering-evolving-contexts-for-selfimproving-language-models)
- *RIZZ, arXiv:2606.20638*: describes ACE as generalizing Dynamic Cheatsheet, and extends it with branch-level, family-level and global playbooks for continual adaptation of black-box agents. This is the interference-control problem a growing skill library faces. — [RIZZ arXiv](https://arxiv.org/pdf/2606.20638)
- *skill-creator*: Anthropic's skill-creator skill creates, edits and optimizes skills, runs evals, benchmarks with variance analysis and tunes descriptions for trigger accuracy. Bundled scripts reportedly include `run_eval.py`, `run_loop.py`, `improve_description.py`, `quick_validate.py` and `aggregate_benchmark.py`. These are third-party mirrors. — [moltchat wiki mirror](https://moltchat-agent-commons.onrender.com/wiki/skill-creator_skill_(anthropics%2Fskills)); [agentskillsfinder](https://agentskillsfinder.com/skills/skill-creator)

### Inferences
- *Safeguard pipeline for agent-authored skills*:
  1. The agent drafts in a sandbox branch.
  2. `skills-ref validate` and `claude plugin validate` run.
  3. Trigger evals run (positives plus near-miss negatives).
  4. A task eval compares with-skill vs without-skill.
  5. A human reviews the PR.
  6. The change is tagged and released.

  ACE's results argue that edits should be small, itemized deltas rather than full rewrites. Cross-marketplace allowlists and command-acceptance gates are the platform-native trust boundaries to preserve.
- *Keep active context small*: rely on relevance blocks and tool-search deferral rather than enabling every plugin. Description quality then becomes the main lever for both discovery and context cost.

### Gaps
- Voyager (skill library, likely arXiv 2305.16291), Reflexion (likely arXiv 2303.11366), SkillWeaver and similar 2023–2025 skill-library papers were not retrieved this session. Their findings and IDs are unverified and should be checked before citing.
- No official Anthropic page on a "skill registry" API or runtime skill search was found. Official Claude Code tool-search defaults were not fetched (code.claude.com/docs/en/mcp would resolve the conflicting reports above).

## Q3. Maintenance: semver, changelogs, deprecation, pinning, linting, drift detection, update bots, monorepo vs per-plugin repos.

### Takeaway
Claude Code now has real package-manager semantics:
- semver `version` that decides when updates are delivered
- per-plugin git tags `<plugin>--v<version>` created by `claude plugin tag`
- semver-range dependencies resolved against those tags
- `ref`/`sha`/`sha256` pinning
- release channels via two catalogs
- an append-only `renames` map plus `forceRemoveDeletedPlugins` for retirement

A monorepo marketplace with per-plugin tags is directly supported. There is no first-party deprecation state and no first-party Renovate-style bot for skills was found.

### Cited Findings
- *Version semantics*:
  - Users get a new copy only when the computed version changes. That version comes from `plugin.json` first, then the marketplace entry.
  - Either bump `version` on every release or omit it entirely to track commits by SHA. Pushing commits without bumping a set `version` delivers nothing.
  - Setting `version` in both places makes plugin.json win silently, and validate warns.
  — [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md)
- *Release tags*:
  - Tag releases `<plugin-name>--v<version>`. The prefix lets one marketplace repo host many independently versioned plugins.
  - `claude plugin tag --push` validates the plugin, checks that plugin.json and the marketplace entry agree on version, requires a clean tree and refuses existing tags. `--dry-run` is supported.
  — [Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md)
- *Dependency ranges*:
  - Dependencies take npm-semver ranges (`~2.1.0`, `^2.0`, `>=1.4`, `=2.1.0`), resolved to the highest satisfying tag. Pre-releases need an opt-in suffix (`^2.0.0-0`).
  - Conflicting ranges fail the install with "has conflicting version requirements". An exact pin `=2.1.0` freezes auto-update for that dependency.
  - `claude plugin list` shows the resolved version with a 12-char SHA suffix.
  - `claude plugin prune` removes orphaned auto-installed dependencies.
  — [Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md)
- *Unpinned risk*: without constraints, a dependency floats to the latest release, and an upstream MCP tool rename breaks every dependent plugin. — [Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md)
- *Release channels*: Claude Code has no built-in channel concept. Run channels as two marketplaces with different `name`s whose entries point at different `ref`s (e.g., `stable` and `latest`), or have users pin a catalog ref with `#stable`. — [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md)
- *Rename and retirement*:
  - `name` is the stable identifier; change only `displayName` for cosmetic renames.
  - For a real rename or removal, add to the top-level `renames` map (old→new, or old→`null`). It is append-only history, chains are followed, and cycles fail validation.
  - `forceRemoveDeletedPlugins: true` uninstalls removed plugins at session start.
  - There is no deprecation state; the documented workaround is remove + `renames:null` (+ force-remove).
  — [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md); [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Repo migration (Gemini)*: Gemini CLI handles moved extensions with a `migratedTo` field. — [Gemini extension reference](https://geminicli.com/docs/extensions/reference/)
- *Monorepo support*:
  - `git-subdir` sources fetch one subdirectory of a monorepo by sparse/partial clone.
  - Relative-path plugins in a monorepo marketplace are tagged by the marketplace maintainer.
  - Symlinks within a marketplace are dereferenced into the cache, so a meta-plugin can re-export sibling skills.
  - Only submodules that hold plugin files are fetched (v2.1.295+).
  - Avoid Git LFS: pointer files arrive instead of content.
  — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md); [Host and maintain](https://code.claude.com/docs/en/plugins/host-marketplace.md); [Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md)
- *What `claude plugin validate` checks*: JSON syntax, required fields, naming rules, `..` paths, unknown keys (warnings), each relative-path plugin's plugin.json, version mismatches, renames chains, header misuse, and Claude Desktop name compatibility. `--strict` is available. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md); [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- *What it misses*: missing source directories, remote fetch errors, and entry `hooks` written as paths. These surface only at install or load, so CI must also run a real install. — [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces); [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Skill linting*: `skills-ref validate` lints SKILL.md frontmatter and naming. — [agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- *MCP linting*: validate `server.json` before publishing; it catches over-long descriptions and bad name patterns. — [dev.to: publishing 7 servers](https://dev.to/zebudata/what-we-learned-publishing-7-mcp-servers-to-the-official-registry-1f7i)
- *Integrity pins*: use `sha` (40-char) for git sources and `sha256` for archives. `npm` sources never run install scripts. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Upstream drift*: format churn is visible in the docs themselves. Many fields carry minimum-version gates (v2.1.222–v2.1.296), and validator messages changed wording across versions (e.g. pre-v2.1.285 "Invalid input"). MCP is reported to have moved Tasks from core to an extension and deprecated HTTP+SSE in 2026-07-28 under a 12-month deprecation policy. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md); [MCP 2026-07-28 changelog mirror](https://modelcontextprotocol.info/specification/2026-07-28/changelog/)

### Inferences
- *Recommended layout*: one monorepo marketplace, with plugins under `plugins/` and `metadata.pluginRoot` set.
  - Version plugins individually and tag them with `claude plugin tag`.
  - Generate `CHANGELOG.md` per plugin from conventional commits.
  - Keep `renames` append-only.
  - Use `stable` and `latest` catalogs for channels.
  - Pin external plugins by `sha` and external MCP packages by exact version.
- *CI matrix*:
  - lint: `skills-ref validate`, `claude plugin validate --strict`, the Gemini extension validator and `server.json` schema validation
  - a smoke `claude plugin install` against a temp marketplace
  - generator idempotency, so that regenerated per-platform manifests produce no diff
- *Drift detection*: pin the `$schema` URLs and minimum CLI versions. Run a scheduled job that fetches upstream schemas, changelogs and llms.txt (code.claude.com publishes `llms.txt`) and opens an issue on diff.
- *Update bots*: with no skills-specific bot found, a Renovate custom regex manager over `marketplace.json` `sha`/`ref` and `server.json` package versions is the closest equivalent. This is my inference, not a documented product.

### Gaps
- No source found for a Renovate or Dependabot manager targeting `marketplace.json`, SKILL.md or `server.json`.
- No official changelog convention for skills was found; the Agent Skills spec has no version field.
- Gemini CLI extension versioning rules beyond "Latest release" + `--ref` + `migratedTo` were not retrieved.

## Q4. Quality and AI improvement: evaluating skills and agents, regression-testing prompts, measuring benefit vs token cost, telemetry-driven pruning.

### Takeaway
Skill evaluation has two layers.
- *Trigger accuracy*: does the description fire on the right queries and not on near misses? skill-creator optimizes this with a train/test split.
- *Outcome uplift*: does the task succeed more often, or more cheaply, with the skill than without it?

Tooling for the first layer exists in skill-creator. The second layer, and telemetry-based pruning, have no first-party product that I could verify.

### Cited Findings
- *Trigger-description optimization (skill-creator, per a third-party blog)*:
  - Splits the eval set 60/40 into train/test.
  - Picks the description with the best test score to limit overfitting.
  - Runs at most 5 iterations.
  - The optimizer moved from an API key to `claude -p` subprocess calls.
  - An open GitHub issue (as of 2026-03-07) reported `run_eval.py` returning a 0% trigger rate.
  — [smartscope skill-creator eval pipeline](https://smartscope.blog/en/generative-ai/claude/skill-creator-eval-pipeline-guide/)
- *Eval-design checklist*: Tessl's registry grades skills with review, quality and evals pages. Its checklist includes near-miss negative queries and roughly 20 queries per optimization run. This is a third-party rubric. — [Tessl skill-creator evals](https://tessl.io/registry/skills/github/anthropics/claude-plugins-official/skill-creator/evals); [Tessl review](https://tessl.io/registry/skills/github/anthropics/skills/skill-creator/review)
- *skill-creator scope*: benchmarking "with variance analysis" is listed as one of its capabilities. — [moltchat mirror](https://moltchat-agent-commons.onrender.com/wiki/skill-creator_skill_(anthropics%2Fskills))
- *Token budgets*: the spec targets about 100 tokens of metadata per skill and under 5k tokens per body. — [agentskills spec](https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx)
- *Tool-search savings*: deferring MCP tools via tool search is reported to save up to about 90% of context (vendor-blog claim, not independently verified). — [dev.to gentic_news](https://dev.to/gentic_news/how-claude-codes-tool-search-saves-90-of-your-context-window-1j1f)
- *Playbook-update evidence*: ACE shows that context/playbook updates can be measured as accuracy deltas on agent benchmarks; it reports +12.3% over ReAct+ICL in offline adaptation. — [arXiv 2510.04618](https://arxiv.org/abs/2510.04618)

### Inferences
- *Per-skill eval suite*: maintain `evals/` per skill containing:
  1. trigger positives and near-miss negatives, with a precision/recall gate in CI
  2. 3–10 task fixtures scored by an LLM judge plus deterministic checks, run with-skill vs baseline
  3. a token and latency cost record

  Fail a PR if uplift is not positive or trigger precision regresses.
- *Pruning*: a skill that rarely triggers, or that shows no uplift, is a removal candidate. Retire it through `renames: null` so installs migrate cleanly.

### Gaps
- No official documentation was found for a `claude plugin eval` command. Treat it as unverified or nonexistent.
- No first-party telemetry or usage-analytics API for skill or plugin invocation counts was found.
- No retrieved sources on Terminal-Bench, SWE-bench usage for skill evaluation, or LLM-as-judge rubrics specific to skills.

## Q5. Notable marketplaces and curated collections: structure and contribution process.

### Takeaway
The official Claude directory (`claude-plugins-official`) takes submissions through a web form with automated plus manual security review, not open PRs. The Gemini gallery auto-indexes tagged repos. Codex has a curated directory, with third-party submissions pending. For MCP, the official registry (namespace-verified) feeds downstream directories. Reserved-name and impersonation checks in Claude Code protect the official catalogs. Contribution details for anthropics/skills, Smithery and mcp.so were not verified.

### Cited Findings
- *Claude directory surface*: Anthropic's plugin directory appears in Claude Code as the `claude-plugins-official` marketplace. — [claude.com submit docs](https://www.claude.com/docs/plugins/submit); [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- *Claude directory review (third-party, auto-generated documentation; unverified)*: external authors submit through a web form (clau.de/plugin-directory-submission). PRs to the community repo are auto-closed, and the repo is a read-only mirror. Review clones the submission at its SHA, runs the validation suite, scans for secrets, disallowed APIs and unsafe patterns, and adds manual security review. — [instagit: official submission](https://instagit.com/anthropics/claude-plugins-official/how-do-plugin-authors-submit-plugins-to-the-directory); [instagit: security vetting](https://instagit.com/anthropics/claude-plugins-official/what-is-the-security-vetting-process-for-external-claude-plugins); [instagit: community direct PRs](https://instagit.com/anthropics/claude-plugins-community/direct-prs-plugin-submissions-claude/)
- *Reserved names*: Claude Code reserves official and community catalog names (`claude-plugins-official`, `claude-plugins-community`, `agent-skills`, `anthropic-agent-skills`, `knowledge-work-plugins`, `life-sciences`, `claude-for-legal`, etc.). They are accepted only from `github.com/anthropics/`, and impersonating names stop loading. — [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md)
- *Gemini gallery*: indexes public extensions automatically, crawling tagged repos daily. An extension appears if it passes validation, with no submission step. — [Gemini release extensions](https://geminicli.com/docs/extensions/releasing/)
- *Codex directory*: the official Plugin Directory is curated. Repo-level and personal marketplaces sit under `.agents/plugins/`. Awesome lists such as `hashgraph-online/awesome-codex-plugins` and `awesome-ai-plugins` aggregate community plugins. — [Codex marketplace blog](https://codex.danielvaughan.com/2026/04/11/codex-marketplace-plugin-distribution/); [awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins); [awesome-ai-plugins](https://github.com/hashgraph-online/awesome-ai-plugins)
- *Community skill lists*: e.g., `JackyST0/awesome-agent-skills`. — [awesome-agent-skills](https://github.com/JackyST0/awesome-agent-skills)
- *MCP directories*: a 2026 roundup lists where to publish servers (official registry, GitHub MCP Registry, Smithery, etc.). The GitHub MCP Registry builds on the official registry for vetted discovery. — [apideck MCP directories 2026](https://www.apideck.com/blog/mcp-server-directories); [roxyapi](https://roxyapi.com/blogs/mcp-registries-where-to-list-your-server); [composio](https://composio.dev/content/github-mcp-registry)
- *Third-party quality signal*: Tessl's registry publishes review, quality and evals scorecards for skills from anthropics/skills, claude-plugins-official and community repos. — [Tessl skill-creator review](https://tessl.io/registry/skills/github/anthropics/skills/skill-creator/review); [Tessl quality](https://tessl.io/registry/skills/github/boisenoise/skills-collections/skill-creator/quality)

### Inferences
- *For a cross-LLM toolkit*: choose a non-reserved, distinctive marketplace `name`. Mirror the official review gates in CI: validate, secret scan, run install at a pinned SHA, and require human review. Ship `CONTRIBUTING.md`, a skill template that passes `skills-ref` and a PR template that requires eval results.
- *Auto-listing*: tagging releases also makes the extensions listable in the Gemini gallery automatically. Publish MCP servers to the official registry under an `io.github.<org>/*` namespace so downstream directories pick them up.

### Gaps
- No primary-source data on anthropics/skills CONTRIBUTING, CI checks or templates (the GitHub API was not enabled for that repo in this session).
- No retrieved data on Smithery or mcp.so submission, scanning or quality processes.
- The instagit.com claims about the Claude directory review pipeline are unverified against Anthropic primary docs.
