# Security Best Practices for Agent Skill / Plugin / MCP Toolkits (2025–2026)

Research date: 2026-11-03. Method note: page fetching (WebFetch) was blocked by this session's network allow-list for snyk.io, owasp.github.io, modelcontextprotocol.io and research.checkpoint.com, so findings below come from web search result content (which quotes primary pages, but not always in full). Where a claim rests only on a secondary/aggregator page, it is flagged. Items before 2025 are marked [pre-2025].

## Q1. What threats are specific to skills, plugins, hooks and MCP servers, and what incidents and research are documented (2025–2026)?

### Takeaway
Skill and MCP marketplaces are now a live supply-chain attack surface, with documented malicious-skill campaigns (ClawHavoc on ClawHub, ~1,200 skills), the first malicious MCP server in the wild (postmark-mcp, Sep 2025), malware that weaponized locally installed AI CLIs (s1ngularity/Nx, Aug 2025), repeated Claude Code CVEs where repo-controlled hooks/MCP config ran before the trust prompt, and prompt-injection takeovers of AI agents in GitHub Actions ("PromptPwnd"). Scanners alone are demonstrably bypassable (Trail of Bits, June 2026).

### Cited Findings

**Malicious skills in marketplaces (empirical studies)**
- Snyk "ToxicSkills" (Feb 2026) scanned 3,984 agent skills (ClawHub / skills.sh); 76 confirmed malicious payloads; 1,467 skills (36.82%) had at least one security issue; prompt injection present in 36% — [Snyk via search](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) (page fetch blocked; figures from search snippet).
- "Malicious Agent Skills in the Wild: A Large-Scale Security Empirical Study" (arXiv 2602.06547, v1 6 Feb 2026, v2 14 Mar 2026; reported as USENIX Security 2026): 98,380 skills from two community registries, 157 confirmed malicious skills with 632 vulnerabilities; mean 4.03 vulnerabilities per malicious skill and a median of three kill-chain phases — [arXiv](https://arxiv.org/abs/2602.06547)
- Same study: two archetypes, "Data Thieves" (credential exfiltration via supply-chain techniques) and "Agent Hijackers" (subverting agent decision-making via instruction manipulation); one actor accounted for 54.1% of confirmed cases using templated brand impersonation (i.e., typosquat/impersonation) — [arXiv](https://arxiv.org/html/2602.06547v1/)
- Same study: "shadow features" (capabilities absent from public docs) appear in 0% of basic attacks but 100% of advanced ones; some skills exploit the platform's hook system and permission flags; responsible disclosure led to 93.6% removal within 30 days — [arXiv](https://arxiv.org/html/2602.06547v1/)
- ClawHavoc campaign: OWASP Agentic Skills Top 10 cites 1,184 malicious skills across 12 publisher accounts; an arXiv paper cites over 1,200 (counts differ) — [OWASP AST01 via search](https://owasp.github.io/www-project-agentic-skills-top-10/ast01); [arXiv 2603.00195](https://arxiv.org/html/2603.00195v1)
- Palo Alto Unit 42 published an analysis of OpenClaw's skill marketplace as an emerging AI supply-chain threat — [Unit 42](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/)
- Multi-scanner study (arXiv, May 2026) over 67,453 OpenClaw skill versions; per a secondary summary the three main scanner families agree on only 0.69% of flagged skills — [arXiv 2605.28588](https://arxiv.org/html/2605.28588v1) (agreement figure via secondary summary; unverified against paper)
- A blog analysis noted that scanning caught malicious skills but not the publisher accounts behind them (identity/governance gap) — [Tobira](https://blog.tobira.ai/ai-agent-skill-marketplace-security/)

**Scanner bypass**
- Trail of Bits, "The sorry state of skill distribution" (3 Jun 2026): bypassed the malicious-skill detectors of ClawHub, Cisco skill-scanner and the three scanners integrated into skills.sh; techniques took under an hour to build in three of four cases — [Trail of Bits](https://blog.trailofbits.com/2026/06/03/the-sorry-state-of-skill-distribution/); [CSA summary](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-skill-scanner-bypass-20260610-csa/)
- Bypass techniques: ~100,000 prepended newlines before malicious logic (ClawHub); arbitrary Git repos and binary payloads; exfiltration hidden in precompiled bytecode; instructions hidden in a Word document's ZIP structure; prompt injection framing an attacker-controlled package registry as an "internal corporate mirror" to fool LLM-based semantic scanners — [The Hacker News](https://thehackernews.com/2026/06/fake-ai-agent-skill-passed-security.html); [CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-skill-scanner-bypass-20260610-csa/)
- Trail of Bits recommends curated repositories, strict control over who can introduce skills, and version pinning — [CSA summary of ToB](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-skill-scanner-bypass-20260610-csa/)
- Cisco's own docs: rules alone catch ~7.7% of malicious skills at HIGH severity with a 4.0% false-positive rate (v2.2.1; ~8% in v2.3.0), hence the recommendation to enable its LLM judge — [PyPI cisco-ai-skill-scanner 2.2.1](https://pypi.org/project/cisco-ai-skill-scanner/2.2.1/); [PyPI 2.3.0](https://pypi.org/project/cisco-ai-skill-scanner/2.3.0/)

**MCP-specific threats: tool poisoning, rug pull, shadowing, toxic flows**
- Tool poisoning (Invariant Labs, Apr 2025): a poisoned description on a benign "add" tool instructed the agent (PoC against Cursor) to read `~/.ssh/id_rsa` and the MCP config and exfiltrate them; the tool need not be invoked, since loading its description into context is enough — [Invariant mcp-injection-experiments](https://github.com/invariantlabs-ai/mcp-injection-experiments); [CSA note](https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-tool-poisoning-ai-agent-exfiltration-2/)
- WhatsApp rug pull + shadowing: a "random fact of the day" server swaps to a malicious tool interface on second load and manipulates a separate trusted whatsapp-mcp server to leak messages to an attacker number — [Invariant repo](https://github.com/invariantlabs-ai/mcp-injection-experiments)
- MCP spec allows tool definitions to change between `tools/list` responses with no built-in integrity check, hash pinning or required re-approval — [DEV summary](https://dev.to/robat_das_3c6e956212f6408/mcp-tool-poisoning-attacks-hidden-tool-descriptions-and-rug-pulls-2i3m) (secondary)
- GitHub MCP "toxic agent flow" (Invariant, May 2025): an agent following instructions in a public issue pulled private-repo data into context and published it in a public PR; described as architectural, not a server bug — [Invariant blog](https://invariantlabs.ai/blog/mcp-github-vulnerability) (via secondary summaries)
- First malicious MCP server in the wild: `postmark-mcp` on npm (Sep 2025), an impostor of the official `@activecampaign/postmark-mcp`; from v1.0.16 a single line added a BCC of every outgoing email to `phan@giftshop.club` — [Snyk](https://snyk.io/blog/malicious-mcp-server-on-npm-postmark-mcp-harvests-emails/); [Semgrep](https://semgrep.dev/blog/2025/so-the-first-malicious-mcp-server-has-been-found-on-npm-what-does-this-mean-for-mcp-security/); [Dark Reading](https://www.darkreading.com/application-security/malicious-mcp-server-exfiltrates-secrets-bcc). Version range disputed (1.0.16 vs 1.0.18) — [Qualys](https://threatprotect.qualys.com/2025/09/30/malicious-mcp-server-on-npm-postmark-mcp-exploited-in-attack/)

**Hook / config-based code execution (Claude Code CVEs)**
- Check Point (CVE-2025-59536, CVSS 8.7): malicious hook commands and MCP settings in a repo's `.claude/settings.json` could execute before the trust prompt; fixed Sept 2025, published 3 Oct 2025 (advisory GHSA-ph6w-f82w-28w6). Some coverage gives the hooks bug a different ID (CVE-2025-59356) — [Check Point Research](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/); [Dark Reading](https://www.darkreading.com/application-security/flaws-claude-code-developer-machines-risk)
- CVE-2026-21852 (CVSS 5.3): project config could set `ANTHROPIC_BASE_URL` to redirect API traffic and leak the API key; fixed in 2.0.65+, published 21 Jan 2026 — [Threat Landscape](https://threatlandscape.io/blog/analyzing-cve-2025-59536-cve-2026-21852-agent-configuration-risks)
- CVE-2026-25725: code already running inside the sandbox could write `.claude/settings.json` with SessionStart hooks that run with host privileges on next restart (sandbox escape via config write) — [SentinelOne](https://www.sentinelone.com/vulnerability-database/cve-2026-25725/) (aggregator)
- CVE-2026-40068 (CVSS 7.7, May 2026): trust-bypass in versions 2.1.63–2.1.83 abusing git-worktree trust logic to run malicious hooks — [SentinelOne](https://www.sentinelone.com/vulnerability-database/cve-2026-40068/) (aggregator)
- Anthropic's plugin security page: an installed plugin can execute arbitrary code on the machine with the user's privileges, and permission rules and the sandbox do not cover code a plugin runs on its own — [Claude Code docs: plugin security](https://code.claude.com/docs/en/plugins/security)

**AI CLIs weaponized by supply-chain malware**
- s1ngularity / Nx (26 Aug 2025): malicious Nx versions (20.9.0–21.8.0 and @nx scoped packages) ran a postinstall `telemetry.js` that invoked the local `claude`, `gemini` and `q` CLIs with flags such as `--dangerously-skip-permissions`, `--yolo`, `--trust-all-tools` to search the filesystem for secrets, then exfiltrated them to `s1ngularity-repository*` repos created via the victim's authenticated `gh` CLI — [Socket](https://socket.dev/blog/nx-packages-compromised); [Wiz](https://www.wiz.io/blog/s1ngularity-supply-chain-attack)
- Scale: ~1,700 users and >2,000 secrets in phase one; 2,180 GitHub accounts affected overall; entry point reported as a flawed GitHub Actions workflow in the Nx repo — [BleepingComputer](https://bleepingcomputer.com/news/security/ai-powered-malware-hit-2-180-github-accounts-in-s1ngularity-attack)

**Prompt injection into CI agents (PromptPwnd)**
- Aikido's "PromptPwnd" class: workflows interpolate untrusted text such as `github.event.issue.body` directly into AI agent prompts (issue triage, PR labeling); hidden instructions made agents in GitHub Actions run commands and post secrets into the issue thread; affected integrations of Gemini CLI, Claude Code, OpenAI Codex and GitHub AI Inference — [CSA note](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-github-actions-security-20260503-csa-st/); [Cybersecurity News](https://cybersecuritynews.com/prompt-injection-github-actions/); [eSecurity Planet](https://www.esecurityplanet.com/threats/ai-agents-create-critical-supply-chain-risk-in-github-actions/)
- Gemini CLI was separately compromised through prompt injection in GitHub Actions — [Cybersecurity News](https://cybersecuritynews.com/gemini-cli-prompt-injections-github/)
- tj-actions/changed-files compromise (Mar 2025): the action was modified to print CI secrets to logs; >23,000 repos using mutable tags affected — [Decryption Digest](https://www.decryptiondigest.com/blog/github-actions-security-hardening)

**Exfiltration (lethal trifecta) and changing state**
- Simon Willison's "lethal trifecta" (June 2025): an agent is exploitable for exfiltration when it combines access to private data, exposure to untrusted content, and an external communication channel — [Willison blog](https://simonwillison.net/2025/nov/2/new-prompt-injection-papers); [agentwiki summary](https://agentwiki.org/lethal_trifecta)
- MITRE ATLAS added "Exfiltration via AI Agent Tool Invocation" (AML.T0086), which treats an agent's own write-capable tools as the exfil path, plus "Publish Poisoned AI Agent Tool" (AML.T0104) and "AI Agent Tool Poisoning" (AML.T0110); the postmark-mcp case is case study AML.CS0053 and an MCP/Cursor exfil case is AML.CS0045 — [Zenity](https://zenity.io/blog/zenity-labs-and-mitre-atlas-collaborate-to-advances-ai-agent-security-with-the-first-release-of); [StartupDefense CS0053](https://www.startupdefense.io/mitre-atlas-case-studies/aml-cs0053-poisoned-postmark-mcp-server-email-exfiltration); [StartupDefense CS0045](https://www.startupdefense.io/mitre-atlas-case-studies/aml-cs0045-data-exfiltration-via-an-mcp-server-used-by-cursor) (technique IDs via secondary sources)

**Confused deputy / token passthrough / sessions (MCP auth)**
- MCP security best practices: MCP proxy servers that connect to third-party APIs with a static client ID can be abused as confused deputies (the third party may skip consent for a malicious client if the user already authorized), so proxy servers MUST implement per-client consent — [MCP spec: security best practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices); [nhimg](https://nhimg.org/articles/mcp-security-best-practices-expose-the-confused-deputy-risk/)
- Token passthrough is an explicit anti-pattern: servers must not accept tokens not issued to them and forward them downstream; mandatory audience validation is the control — [MCP spec](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices); [Security Boulevard](https://securityboulevard.com/2026/03/mcp-authentication-and-authorization-patterns)
- Session hijacking: an attacker who obtains a server-issued session ID impersonates the client; a third-party checklist claims spec version 2026-07-28 made MCP stateless and recast this as "state handle hijacking" (do not treat cart/workflow IDs as authentication) — [MCP spec](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices); [NeuralTrust](https://neuraltrust.ai/blog/mcp-security-best-practices) (statelessness claim unverified)

**Hijack success rates**
- NIST CAISI ran agent-hijacking experiments using AgentDojo and open-sourced `agentdojo-inspect` — [NIST](https://www.nist.gov/node/1872381)
- A UK AISI test of 13 frontier models reportedly found at least one successful hijack against every model — [CSA note, Apr 2026](https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/CSA_research_note_nist_ai_agent_standards_20260416-csa-styled-1.pdf) (secondary, AI-assisted summary)

### Inferences
- Threat ranking for a Claude Code marketplace that also targets Codex/Gemini CLI/Cursor (highest first): (1) supply-chain compromise or impersonation of the plugin source and its dependencies (pip/npm postinstall, mutable refs); (2) hooks and scripts running arbitrary code with user privileges, outside permission rules and the sandbox; (3) indirect prompt injection through repos, PRs, issues, web pages and tool results, which leads to exfiltration when the lethal trifecta is present; (4) CI agents on PRs holding secrets and write tokens; (5) MCP tool poisoning, rug pulls and shadowing; (6) over-broad tool grants in skills and subagents; (7) secrets in context or logs.
- The s1ngularity case means that a toolkit that documents or ships "yolo" launch scripts (`--dangerously-skip-permissions`) makes later abuse by other malware easier. The toolkit should never ship or recommend such flags outside isolated containers.
- Cross-LLM targeting multiplies the attack surface. A single SKILL.md is interpreted by several agents with different permission models, and OWASP AST10 "Cross-Platform Reuse" names this risk.

### Gaps
- Could not fetch Snyk ToxicSkills, Check Point or Invariant primary pages, so exact methodology and some figures come from search snippets.
- No 2026 study of MCP server vulnerability prevalence comparable to the skills studies turned up in this research pass, and none could be confirmed.
- Exact CVE ID mapping for the 2025 hooks bug is inconsistent across sources (59536 vs 59356). Check GHSA-ph6w-f82w-28w6.

## Q2. Which frameworks apply (OWASP LLM / Agentic / MCP / Skills, MITRE ATLAS, NIST, CoSAI, MCP spec)?

### Takeaway
There are four OWASP lists to map against: LLM Top 10 2025, Agentic Top 10 2026 (ASI01–ASI10, Dec 2025), MCP Top 10 (beta, v0.1), and the newer Agentic Skills Top 10 (AST01–AST10, v0.5/1.0, 2026). The last one matches a skills marketplace most directly. Supplement them with MITRE ATLAS agent techniques, the CoSAI MCP whitepaper (Jan 2026), the MCP spec security best practices, and NIST CAISI work, which is still emerging.

### Cited Findings
- **OWASP Top 10 for LLM Applications 2025** (released 18 Nov 2024 [pre-2025 release, 2025 edition]): LLM01 Prompt Injection remains #1; LLM06 Excessive Agency (excessive functionality, permissions, autonomy) expanded; LLM07 System Prompt Leakage new — [Invicti](https://invicti.com/blog/web-security/owasp-top-10-risks-llm-security-2025); [Aembit](https://aembit.io/blog/owasp-top-10-llm-risks-explained/)
- **OWASP Top 10 for Agentic Applications 2026**, published 9 Dec 2025 by OWASP GenAI Security Project with 100+ contributors: ASI01 Agent Goal Hijack, ASI02 Tool Misuse & Exploitation, ASI03 Identity & Privilege Abuse, ASI04 Agentic Supply Chain Vulnerabilities, … ASI09 Human-Agent Trust Exploitation, ASI10 Rogue Agents — [Cycode](https://cycode.com/blog/owasp-top-10-agentic-applications/); [SecureW2](https://securew2.com/?p=72008); [AIGL](https://www.aigl.blog/owasp-top-10-for-agentic-applications-2026/) (ASI05–ASI08 names not confirmed in these results)
- ASI01 is the agentic counterpart of prompt injection: the attacker steers the agent's goal through content it reads (documents, emails, tool outputs) — [Modulos](https://docs.modulos.ai/frameworks/owasp-top-10-agentic)
- **OWASP MCP Top 10**: in Phase 3 beta; MCP03 Tool Poisoning (with rug pulls, shadowing), MCP04 Software Supply Chain; Microsoft's mapping notes it reflects v0.1 — [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/); [Microsoft mapping](https://microsoft.github.io/agent-governance-toolkit/compliance/mcp-owasp-top10-mapping/)
- **OWASP Agentic Skills Top 10**: AST01 Malicious Skills (Critical; key mitigation is signing plus behavioral scanning), AST02 Supply Chain Compromise, AST03 Over-Privileged Skills, AST04 Insecure Metadata, AST05 Untrusted External Instructions, AST06 Weak Isolation, AST07 Update Drift, AST08 Poor Scanning, AST09 No Governance, AST10 Cross-Platform Reuse; covers OpenClaw SKILL.md, Claude Code, Cursor/Codex and VS Code. Version labeling conflicts (v0.5 June 2026 PDF vs "1.0 2026 Edition") — [OWASP AST10 PDF](https://owasp.org/www-project-agentic-skills-top-10/docs/OWASP-Agentic-Skills-Top10-v0.5.pdf); [GitHub](https://github.com/OWASP/www-project-agentic-skills-top-10); [Abnormal](https://abnormal.ai/learning/owasp-agentic-skills-top-10)
- **MITRE ATLAS**: Zenity contributed 14 agent-focused techniques/sub-techniques in Oct 2025; there is no dedicated MCP technique yet; a CSA gap analysis lists six agentic gap categories, including MCP server risk — [Zenity](https://zenity.io/blog/zenity-labs-and-mitre-atlas-collaborate-to-advances-ai-agent-security-with-the-first-release-of); [CSA gap analysis](https://labs.cloudsecurityalliance.org/research/csa-research-note-atlas-agentic-gap-analysis-20260327/). Version counts conflict (v5.1.0: 16 tactics/84 techniques per DeepInspect vs 15/66 per CSA) — [DeepInspect](https://www.deepinspect.ai/blog/mitre-atlas-ai-controls-mapping)
- **CoSAI MCP Security whitepaper** (8 Jan 2026): 12 core threat categories, "almost forty" threats spanning identity, access control, input handling, data protection, transport, supply chain and operational governance; separates traditional threats amplified by AI from novel threats — [CoSAI PDF](https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf); [CoSAI blog](https://coalitionforsecureai.org/securing-the-ai-agent-revolution-a-practical-guide-to-mcp-security); tier split (7 MCP-specific / 8 / 19 conventional) per [CoSAI-based deck](https://docs.google.com/presentation/d/15PsR0-3rNeeBE_PssU--sk_n9aXMrMVb/htmlpresent)
- **NIST**: CAISI RFI on AI agent security (Federal Register 8 Jan 2026, docket NIST-2025-0035, >500 responses) will inform an SP 800-53 control overlay for AI agent systems; COSAiS project (Aug 2025) is developing single- and multi-agent overlays, with no publication date as of Apr 2026; AI Agent Standards Initiative launched 17 Feb 2026 — [Federal Register](https://www.govinfo.gov/content/pkg/FR-2026-01-08/html/2026-00206.htm); [NCCoE slides](https://www.nccoe.nist.gov/sites/default/files/2026-05/Cyber-AI-Profile-Working-Session-Extending-Tech-Content-Slides-Slido.pdf); [CSA note](https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/04/CSA_research_note_nist-caisi-ai-agent-security-agenda-2026_20260414-csa-styled.pdf)
- **MCP spec security best practices**: confused deputy (per-client consent for proxy servers), token passthrough (forbidden, validate audience), session hijacking, SSRF, local server compromise, scope minimization — [MCP spec](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices); [Microsoft MCP for Beginners: Security](https://github.com/microsoft/mcp-for-beginners/blob/main/02-Security/README.md)
- **Meta "Agents Rule of Two"** (31 Oct 2025): in one session an agent should satisfy at most two of: processing untrustworthy inputs, accessing sensitive systems/private data, changing state or communicating externally; otherwise it needs human-in-the-loop — [Willison](https://simonwillison.net/2025/nov/2/new-prompt-injection-papers); [Oso](https://www-webflow.osohq.com/learn/agents-rule-of-two-a-practical-approach-to-ai-agent-security)

### Inferences
- For the toolkit's SECURITY.md and review checklist, the most useful primary mapping is OWASP AST01–AST10 for skill content and distribution, with ASI01/02/03/04 for runtime agent behaviour and MCP03/04 for MCP servers. Cite LLM01/LLM06 for general prompt injection and excessive agency.
- NIST guidance is not yet prescriptive for agents. NIST AI RMF (2023 [pre-2025]) works as a governance umbrella, but in 2026 it offers no concrete control set for skills.

### Gaps
- Full ASI05–ASI08 names were not confirmed from primary text in this pass. From prior knowledge they are probably Unexpected Code Execution, Memory & Context Poisoning, Insecure Inter-Agent Communication and Cascading Failures, which needs verification at genai.owasp.org.
- Full OWASP MCP Top 10 entry names beyond MCP03/MCP04 were not retrieved.
- The CoSAI category names were not retrieved verbatim.

## Q3. What concrete controls should toolkit authors implement, prioritized by impact and effort?

### Takeaway
The highest-impact controls are cheap. Pin and curate everything (marketplace sources by commit SHA, MCP servers by exact version or hash, GitHub Actions by SHA). Grant least privilege per skill and subagent. Ship no auto-running hooks that touch the network or secrets. Run anything that reads untrusted content in a sandbox with an egress allow-list. Harden CI agents (no secrets or write tokens on untrusted triggers). Scanning (Cisco skill-scanner, Snyk agent-scan/mcp-scan, zizmor) is necessary but bypassable, so it must sit behind human review and provenance.

### Cited Findings

**Platform controls (Claude Code)**
- Sandboxing uses OS-level enforcement (Seatbelt on macOS, bubblewrap on Linux/WSL2) for all subprocesses. Network goes through a proxy outside the sandbox that allows only approved domains. Writes are limited to the working directory by default. A new domain triggers an approval prompt — [Claude Code docs: sandboxing](https://code.claude.com/docs/en/sandboxing)
- If the sandbox cannot start (missing deps or unsupported platform), Claude Code by default warns and runs commands unsandboxed. A third-party article claims the opposite, so the official docs should be trusted and fail-closed configured explicitly — [Claude Code docs](https://code.claude.com/docs/en/sandboxing); contradicted by [jiangren](https://jiangren.com.au/en/learn/ai-engineer/claude-code-sandboxing)
- Permission rules decide which tool calls may be attempted. The sandbox limits what Bash and its children can touch, and it does not automatically constrain every MCP server — [jiangren](https://jiangren.com.au/en/learn/ai-engineer/claude-code-sandboxing) (secondary)
- Managed settings: `strictKnownMarketplaces` (allow-list of marketplace sources, e.g. `[{"source":"github","repo":"acme/plugins"}]`), `blockedMarketplaces`, `allowManagedHooksOnly` (blocks user, project and plugin hooks; managed and SDK hooks still load), `pluginTrustMessage` (custom install warning). Marketplace `headersHelper` commands are blocked unless declared in managed settings — [Claude Code docs: managed settings](https://code.claude.com/docs/en/managed-settings); [plugin security](https://code.claude.com/docs/en/plugins/security); [Claude support: manage plugins](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization)
- `extraKnownMarketplaces` in a repo's `.claude/settings.json` applies only once the contributor trusts the folder and is otherwise silently ignored — [Claude Code docs: plugins/org (zh-CN)](https://code.claude.com/docs/zh-CN/plugins/org)

**Scanning tools**
- Cisco AI Defense `skill-scanner` (Apache-2.0; `pip install cisco-ai-skill-scanner`): `scan`, `scan-all`, `scan-repo`; supports Codex and Cursor Agent Skills format, plus `--lenient` for Claude Code `.claude/commands/*.md`; optional LLM judge, behavioral dataflow analysis, VirusTotal — [GitHub](https://github.com/cisco-ai-defense/skill-scanner); [PyPI](https://pypi.org/project/cisco-ai-skill-scanner/2.3.0/)
- NVIDIA SkillSpector is the other open-source skill scanner — [agentic-ai docs](https://agentic-ai.readthedocs.io/en/latest/SecurityFrameworks/skill-scanners/)
- Invariant `mcp-scan` (now part of Snyk agent-scan) detects tool poisoning, rug pulls, cross-origin escalation and prompt injection in installed MCP servers, with an LLM classifier — [mcpplaygroundonline](https://mcpplaygroundonline.com/blog/mcp-security-tool-poisoning-owasp-top-10-mcp-scan); [pipelab](https://pipelab.org/learn/mcp-tool-poisoning/)
- CI workflow scanners for prompt-injection-prone agent setups: `ci-agent-audit`, `gh-prompt-scan`, meant for manual review rather than as a guarantee — [ci-agent-audit](https://github.com/layer8labs8/ci-agent-audit); [gh-prompt-scan](https://pypi.org/project/gh-prompt-scan/)
- `zizmor` flags unpinned actions, template injection from untrusted input, dangerous `pull_request_target` and over-permissive `GITHUB_TOKEN`; pin zizmor itself to a fixed version — [Decryption Digest](https://www.decryptiondigest.com/blog/github-actions-security-hardening); [pydevtools](https://pydevtools.com/handbook/how-to/how-to-pin-github-actions-by-sha-for-python-projects/)

**GitHub Actions hardening for agent CI**
- Pin actions to full 40-char SHAs (with a `# vX.Y.Z` comment that Dependabot can bump); `pinact` automates the rewrite — [pydevtools](https://pydevtools.com/handbook/how-to/how-to-pin-github-actions-by-sha-for-python-projects/); [microsoft/finops-toolkit PR](https://github.com/microsoft/finops-toolkit/pull/2242)
- Never check out PR head code under `pull_request_target`. Use `pull_request` (read-only for forks) to execute code, and keep `pull_request_target` for label or comment operations without checkout. Set `permissions: {}` at workflow level and grant per job — [Decryption Digest](https://www.decryptiondigest.com/blog/github-actions-security-hardening)
- For AI agents in CI: do not interpolate `github.event.*.body` into prompts, restrict agent tools (especially issue/PR write), treat AI output as untrusted, and minimize token scopes — [CSA PromptPwnd note](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-github-actions-security-20260503-csa-st/); [Cybersecurity News](https://cybersecuritynews.com/prompt-injection-github-actions/)

**Provenance / signing**
- Building blocks: Sigstore keyless signing (Fulcio cert + Rekor log), in-toto/DSSE attestations, SLSA provenance; `smithmark` issues signed capability declarations for MCP servers and skills; `agent-bom skill_verify` checks Sigstore provenance of skill/instruction files. The MCP Registry attestation field is only proposed (RFC), and no entries carry it yet (self-reported by smithmark) — [smithmark](https://github.com/sns45/smithmark); [agent-bom](https://glama.ai/mcp/servers/msaad00/agent-bom/tools/skill_verify); [agentpatterns.ai](https://agentpatterns.ai/security/tool-signing-verification/)
- Recommended pattern: sign in CI with Cosign, attach signature and SLSA provenance, verify at agent startup, and diff live tool schemas against the signed baseline to catch rug pulls — [agentpatterns.ai](https://agentpatterns.ai/security/tool-signing-verification/)
- OWASP AST01's key mitigation is cryptographic signing plus behavioral scanning — [Abnormal summary of AST10](https://abnormal.ai/learning/owasp-agentic-skills-top-10)

**MCP server authoring**
- Validate token audience; no token passthrough; per-client consent for proxy servers; minimize scopes; session/state IDs are not authentication — [MCP spec](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices)
- Publish under a scoped, verifiable package name. postmark-mcp succeeded by impersonating the official scoped package with an unscoped name — [Snyk](https://snyk.io/blog/malicious-mcp-server-on-npm-postmark-mcp-harvests-emails/)

### Inferences
Prioritized control list (Impact H/M/L, Effort L/M/H). Items marked "prior knowledge" rest on Claude Code features I know of but could not re-verify in this session, so check them against docs before implementing.

| # | Control | Threat addressed | Impact | Effort |
|---|---------|------------------|--------|--------|
| 1 | Pin marketplace sources and plugin refs to commit SHAs; pin MCP servers to exact versions (npx/uvx `pkg@x.y.z`, ideally with lockfile hash); pin GitHub Actions by SHA; Dependabot/Renovate to bump | Supply chain, rug pull, update drift (AST02/AST07, MCP04) | H | L |
| 2 | Least privilege per skill and subagent: set `allowed-tools` in SKILL.md frontmatter and `tools:` in subagent definitions (prior knowledge); read-only skills get Read/Grep/Glob only; no wildcard Bash; give scripted Bash patterns specifically (e.g., `Bash(python3 scripts/foo.py:*)`) | Excessive agency (LLM06, AST03, ASI02) | H | L |
| 3 | Ship recommended `permissions.deny` rules (prior knowledge): deny Read of `.env*`, `~/.ssh/**`, `~/.aws/**`, credential files; deny `curl`/`wget` to arbitrary hosts; deny `git push --force` | Secrets leakage, exfil | H | L |
| 4 | Hooks policy: no network calls, no secret reads, no downloading or executing remote code in hooks; hooks are small, readable, and quote all inputs; document every hook in README; prefer opt-in. Remind enterprise users of `allowManagedHooksOnly` | Hook RCE (CVE-2025-59536 class), AST06 | H | L |
| 5 | Never ship or recommend `--dangerously-skip-permissions`/`--yolo` outside a disposable container or VM; document a container recipe with egress allow-list | s1ngularity-style abuse | H | L |
| 6 | Sandbox by default for skills that read untrusted repos, PRs or web content: enable Claude Code sandbox with a narrow domain allow-list; configure fail-closed; for other CLIs (Codex/Gemini) document their sandbox equivalents or use devcontainers | Exfil, lethal trifecta | H | M |
| 7 | CI hardening for any agent-on-PR workflow: `pull_request` not `pull_request_target`; `permissions: {}` + per-job minimal; no secrets on fork PRs; never interpolate issue/PR bodies into prompts (pass via file and frame as data); agent has no write tools, or writes go through a separate non-LLM step; run zizmor + ci-agent-audit | PromptPwnd, tj-actions class | H | M |
| 8 | Automated CI gate on every marketplace PR: Cisco skill-scanner (with LLM judge) + mcp-scan/agent-scan + secret scanning (gitleaks/trufflehog/GitHub push protection) + pip-audit/npm audit + custom lint (below). Failures block merge | Malicious skills (AST01/AST08) | H | M |
| 9 | Mandatory human review by CODEOWNERS for any change to hooks, scripts, `allowed-tools`, MCP config, or network-touching code; two-person review for new contributors | Scanner bypass (ToB) | H | L–M |
| 10 | Provenance: signed tags/commits, GitHub artifact attestations (SLSA build provenance) on releases, publish a hash manifest of every skill/script; optionally Sigstore-sign skill bundles | AST01/AST02, impersonation | M–H | M |
| 11 | MCP servers: prefer local stdio servers you author; pin; review tool descriptions for hidden instructions; re-approve on tool-definition change (hash tool schemas and diff); OAuth audience validation, no token passthrough | MCP03 tool poisoning, rug pull, confused deputy | M–H | M |
| 12 | Name-squat defense: reserve plugin and package names on PyPI/npm, use scoped names, and state canonical install URLs in README/SECURITY.md | Typosquatting (54% of malicious skills used brand impersonation) | M | L |
| 13 | Secrets hygiene: scripts read secrets from env, never echo them; redact in logs; no secrets in SKILL.md examples; deny reading `.env` | Secrets in context | M | L |
| 14 | SBOM (CycloneDX/SPDX) for Python script dependencies and MCP servers per release | Vulnerable deps | M | L |
| 15 | Human-in-the-loop for state-changing or external-communication actions (push, publish, send, deploy), aligned with Rule of Two | ASI09, exfil | H | L (doc) |

### Gaps
- Exact current syntax and precedence of Claude Code `permissions.deny`, skill `allowed-tools`, and the sandbox fail-closed setting were not verified from primary docs in this session (fetch blocked).
- Equivalent controls in Codex CLI, Gemini CLI and Cursor (sandbox modes, approval policies) were not researched here.
- Whether Snyk agent-scan is free or open-source in late 2026 was not confirmed.

## Q4. Which design patterns resist prompt injection, and how do they apply to skills that read untrusted repos and PRs?

### Takeaway
No filter reliably stops prompt injection. The robust approach is architectural: break the lethal trifecta or Rule-of-Two combination per session, and use patterns that keep untrusted data from choosing actions (Action-Selector, Plan-Then-Execute, Dual LLM, Code-Then-Execute/CaMeL, Map-Reduce, Context-Minimization).

### Cited Findings
- "Design Patterns for Securing LLM Agents against Prompt Injections" (arXiv 2506.08837, June 2025; authors from Google, Microsoft, IBM, ETH Zurich, EPFL) proposes six patterns: Action-Selector, Plan-Then-Execute, LLM Map-Reduce, Dual LLM, Code-Then-Execute, Context-Minimization — [arXiv](https://arxiv.org/abs/2506.08837); [arXiv HTML v3](https://arxiv.org/html/2506.08837v3)
- Action-Selector maps requests to predefined tool calls and never reads tool outputs ("LLM-modulated switch statement"), which makes it the most secure and least flexible pattern — [arXiv](https://arxiv.org/pdf/2506.08837)
- Plan-Then-Execute fixes the allowed tool sequence before reading untrusted data. Injection cannot add new tools but can still alter arguments — [arXiv](https://arxiv.org/html/2506.08837v3)
- Code-Then-Execute generalizes this into an explicit program and is the basis of Google DeepMind's CaMeL ("Defeating Prompt Injections by Design", arXiv 2503.18813) — [arXiv 2506.08837](https://arxiv.org/html/2506.08837v3)
- An analysis of what each pattern leaves open: [ARMO](https://www.armosec.io/blog/design-patterns-for-securing-llm-agents/); "You Cannot Filter Your Way Out of Prompt Injection" — [HackerNoon](https://hackernoon.com/you-cannot-filter-your-way-out-of-prompt-injection)
- 2026 adaptive evaluation of out-of-band prompt-injection defenses in agents — [arXiv 2606.26479](https://arxiv.org/pdf/2606.26479)
- Meta's Rule of Two adds "changing state" to the trifecta. Willison called it "the best practical advice for building secure LLM-powered agent systems today" in the absence of reliable defenses — [Willison](https://simonwillison.net/2025/nov/2/new-prompt-injection-papers)
- Critique: the Rule of Two is a clean per-session rule but leaves residual risk across turns, tools and delegated tasks — [Ken Huang](https://kenhuangus.substack.com/p/the-rule-of-two-vs-reality-why-metas)
- The GitHub MCP toxic flow (public issue → private repo data → public PR) shows the trifecta in a developer-tool setting — [Invariant](https://invariantlabs.ai/blog/mcp-github-vulnerability)

### Inferences
How to apply these to skills that review untrusted repos or PRs:
- **Split reader and actor (Dual LLM / subagent quarantine):** a read-only subagent (tools: Read/Grep/Glob, no Bash, no network, no write) reads the untrusted PR and returns structured, schema-constrained findings (JSON with enums and line refs). The parent agent, which may hold write tools, consumes only the structured output and never the raw text. In Claude Code this maps to a subagent with a restricted `tools:` list.
- **Plan-Then-Execute for PR review:** fix the action set before reading the diff (for example, "post one review comment to PR #N"). Writes go through a deterministic script that validates arguments: target PR fixed, no URLs or mentions, size limits.
- **Break the trifecta per skill:** a skill that reads untrusted content gets no network egress (sandbox allow-list empty, or only the code host) and no secrets in env. A skill that needs secrets or network must not read untrusted content. Document each skill's trifecta profile in its frontmatter or README.
- **Context-Minimization:** strip the PR body and comments from the prompt where possible, and pass the diff as a file framed as data, not as instructions.
- **Human approval** for any step that combines all three properties (for example, an agent that reads a PR and also pushes or comments with repo-write tokens).
- The skill text itself should state that instructions found in files, PRs and tool output are data. This is a weak, defense-in-depth layer and must not be relied on alone.

### Gaps
- CaMeL's own evaluation numbers (utility and security on AgentDojo) were not retrieved in this pass.
- No published evaluation was found of these patterns applied specifically to Claude Code subagents.

## Q5. What should a SECURITY.md, a contribution review checklist and an automated CI security gate contain for a skills marketplace?

### Takeaway
No standard template exists yet for skills marketplaces. Practice converges on the OWASP AST10 risks plus Trail of Bits' advice (curation, controlled contributors, pinning). A SECURITY.md should state the trust model and reporting path. The checklist should focus on hooks, scripts, tool grants, network and hidden content. The CI gate layers scanners, but because scanners are bypassable, it must end in mandatory human review.

### Cited Findings
- Trail of Bits recommends curated repositories, strict control over who can introduce skills, and version pinning, since all tested scanners were bypassed — [Trail of Bits](https://blog.trailofbits.com/2026/06/03/the-sorry-state-of-skill-distribution/)
- Bypass vectors a gate must handle: huge whitespace padding, binary or bytecode payloads, archives and Office files (ZIP) with hidden instructions, references to external git repos, and injection aimed at LLM scanners — [The Hacker News](https://thehackernews.com/2026/06/fake-ai-agent-skill-passed-security.html)
- Advanced malicious skills use undocumented "shadow features" and abuse hooks and permission flags — [arXiv 2602.06547](https://arxiv.org/html/2602.06547v1/)
- Hidden instructions in tool names, descriptions and input schemas are the tool-poisoning vector — [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/); [Speakeasy](https://www.speakeasy.com/resources/mcp-tool-poisoning)
- Scanners such as ci-agent-audit and gh-prompt-scan are intended to support manual review, not to guarantee safety — [ci-agent-audit](https://github.com/layer8labs8/ci-agent-audit)
- Scanner families agree rarely (0.69% overlap reported), which argues for running several — [arXiv 2605.28588](https://arxiv.org/html/2605.28588v1) (via secondary summary)
- Claude Code lets admins append a custom `pluginTrustMessage` to the install warning, so a marketplace can point users at its SECURITY.md — [plugin security docs](https://code.claude.com/docs/en/plugins/security)

### Inferences
**SECURITY.md contents**
1. Supported versions; private reporting channel (GitHub private vulnerability reporting / security advisories); response SLA; safe-harbor statement.
2. Trust model: plugins run code with user privileges, and permission rules and the sandbox do not cover plugin-run code (quote Anthropic). List which components execute code (hooks, scripts, MCP servers) and when.
3. Canonical sources: the official repo URL, install command, and pinned-SHA guidance; a warning about lookalike names.
4. Per-skill security profile: tools granted, network domains, secrets used, trifecta classification, whether it reads untrusted content.
5. Recommended user hardening: sandbox enabled, deny rules, no `--dangerously-skip-permissions`, enterprise `strictKnownMarketplaces` / `allowManagedHooksOnly` snippet.
6. Supply-chain posture: signed releases, attestations, SBOM, dependency pinning, how to verify.
7. CI agent guidance for anyone reusing the toolkit's workflows (PromptPwnd mitigations).
8. Framework mapping (OWASP AST10, ASI, MCP Top 10).

**Contribution review checklist (human, CODEOWNERS-enforced)**
- Does it add or modify hooks? Check what triggers them, whether they touch network or secrets, and whether inputs are quoted. Any `SessionStart` or `PreToolUse` hook needs extra scrutiny.
- Are scripts readable source (no binaries, `.pyc`, minified or obfuscated code, base64 blobs, eval/exec of fetched content)?
- Network: are all outbound domains listed and justified? Is anything downloaded or executed at runtime (`curl | sh`, `pip install` at runtime, `npx` without a version)?
- Tool grants: `allowed-tools`/`tools:` minimal, with no unrestricted Bash. Does the description match the behaviour, with no shadow features?
- Hidden content: zero-width or bidi Unicode, HTML comments, very long whitespace runs, instructions in referenced files, archives or Office docs.
- Prompt-injection posture: does it read untrusted input? Is it split into reader and actor? Does it carry no secrets or egress?
- Secrets: no keys, tokens or real hostnames; no reads of `~/.ssh`, `.env`, cloud creds.
- MCP: pinned version, scoped package, tool descriptions reviewed, auth follows the MCP spec (audience validation, no passthrough).
- Dependencies pinned with hashes; licence OK.
- Cross-platform: behaviour reviewed under Codex/Gemini/Cursor semantics (their permission models differ, AST10).
- New-contributor PRs get two reviewers.

**Automated CI gate (blocking)**
1. Workflow hygiene: the gate runs on `pull_request` with `permissions: contents: read`, no secrets, actions pinned by SHA; zizmor on `.github/workflows`.
2. Static content lint (custom, cheap): reject binaries/archives/Office files in skill dirs; reject files above a size limit or lines above N chars; flag zero-width/bidi Unicode and long whitespace runs; flag `curl|wget|nc|base64 -d|eval|exec|subprocess(..., shell=True)|requests.post` and URLs not on an allow-list; flag reads of credential paths; validate frontmatter schema (required `allowed-tools`, no wildcard Bash).
3. Diff-aware triggers: any change under `hooks/`, `scripts/`, `.mcp.json`, `plugin.json` permissions, or `allowed-tools` applies a `security-review-required` label and requires a CODEOWNER.
4. Skill scanners: Cisco skill-scanner (`scan-repo`, with LLM judge if a key is available) plus Snyk agent-scan/mcp-scan for MCP configs. Run several because their findings rarely overlap.
5. Secret scanning (gitleaks/trufflehog + GitHub push protection) and dependency audit (pip-audit, npm audit, OSV-Scanner); SBOM generation.
6. Python SAST (Bandit/Semgrep) on scripts.
7. Release job (protected, on tag only): build bundle, emit hash manifest, GitHub artifact attestation / Sigstore sign, publish SBOM.
8. Optional: a behavioural test that runs each script in a network-denied container and fails on unexpected egress attempts.

### Gaps
- No published, authoritative SECURITY.md template specific to skills marketplaces was found. The above is synthesized.
- No data was found on how Anthropic's official plugin marketplace or the community "awesome" marketplaces review submissions in 2026.
