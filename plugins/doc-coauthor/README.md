# Document Co-Authoring System

A multi-agent pipeline for producing structured, high-quality documents through a three-stage workflow: context intake, drafting, and reader simulation review.

---

## Overview

The document co-authoring system separates the writing process into three isolated stages, each handled by a dedicated sub-agent. The coordinator skill manages state and routes commands — sub-agents have no memory of prior invocations and work only with what they are given.

This isolation is intentional: the review stage simulates a reader who has never seen the authoring process, which produces more genuine feedback than a reviewer with full context.

**Supported document types:** Decision docs, RFCs, PRDs, Architecture specs, Technical specs, Proposals

<!-- BEGIN GENERATED:install -->
## Install

Claude Code:

```
/plugin marketplace add Cinct00/ai-toolkit
/plugin install doc-coauthor@ai-toolkit
```

GitHub Copilot CLI:

```bash
copilot plugin marketplace add Cinct00/ai-toolkit
copilot plugin install doc-coauthor@ai-toolkit
```

Any other Agent Skills client: copy or link `skills/*` into `~/.agents/skills/` (or run `python3 scripts/toolkit.py install --target skills` from the toolkit).

## Contents

| Skill | Description |
|---|---|
| [`doc-coauthor`](skills/doc-coauthor/SKILL.md) | Co-author a substantial document (RFC, PRD, decision doc, architecture or technical spec, proposal) through three isolated stages: context intake, drafting, and a reader-simulation review by a sub-agent with zero author… |

| Agent | Description |
|---|---|
| [`doc-context`](agents/doc-context.agent.md) | Stage 1 sub-agent for the doc co-authoring system. Processes raw user context and returns a structured summary, assumed document structure, key assumptions, risks, and optional clarifying questions. Invoked by the doc-c… |
| [`doc-draft`](agents/doc-draft.agent.md) | Stage 2 sub-agent for the doc co-authoring system. Receives a structured context package or a refinement package and returns a complete document in a single pass. Simulates the full brainstorm-curate-draft-edit loop int… |
| [`doc-review`](agents/doc-review.agent.md) | Stage 3 sub-agent for the doc co-authoring system. Receives only the finished document and its meta — no authoring history, no prior drafts, no context from the writing process. Simulates a genuine fresh reader, identif… |
<!-- END GENERATED:install -->

---

## Architecture

```
User
 │
 ▼
doc-coauthor (skill — runs in the main session, holds state, routes)
 ├── /doc start  ──▶  doc-context  (sub-agent: context processing)
 ├── /doc draft  ──▶  doc-draft    (sub-agent: document generation)
 └── /doc review ──▶  doc-review   (sub-agent: reader simulation + QA)
```

The coordinator is a **skill** rather than an agent so it works the same in Claude Code,
GitHub Copilot and any Agent Skills client: it runs in the main session (where delegating
to sub-agents is always allowed) and falls back to single-agent mode where no delegation
tool exists.

### Components

| Component | File | Role |
|-----------|------|------|
| Coordinator | [skills/doc-coauthor/SKILL.md](skills/doc-coauthor/SKILL.md) | Routes commands, holds session state |
| Stage 1 | [agents/doc-context.agent.md](agents/doc-context.agent.md) | Parses raw input into structured context |
| Stage 2 | [agents/doc-draft.agent.md](agents/doc-draft.agent.md) | Generates and refines the document |
| Stage 3 | [agents/doc-review.agent.md](agents/doc-review.agent.md) | Reader simulation and structural QA |

---

## Workflow

### Stage 1 — `/doc start`

The user provides raw context about what they want to write. The coordinator passes this to `doc-context`, which returns:

- **Context Summary** — a 2-4 sentence briefing on the document's purpose
- **Assumed Document Structure** — numbered sections with rationale for each
- **Key Assumptions** — inferences made from incomplete input
- **Risks and Edge Cases** — topics the document should address
- **Clarifying Questions** — up to 5 genuine gaps that inference cannot fill

The user reviews the output and either answers the clarifying questions or proceeds directly to drafting.

### Stage 2 — `/doc draft`

The coordinator assembles a Draft Package (context summary, assumptions, structure, and any additional user input) and passes it to `doc-draft`. The agent generates a complete document in a single pass using a disciplined process:

1. Generate 10-15 candidate points per section
2. Cull to the 4-6 strongest based on audience and goal
3. Check for redundancy with adjacent sections
4. Draft the section
5. Self-edit pass (remove filler, strengthen weak sentences)
6. Cross-document pass (flow, contradictions, tone consistency)

The output includes:
- Full document in clean markdown
- "What I decided" — 3-5 bullets on structural and content choices

**Refinement rounds** are supported between draft and review. The user provides feedback; the coordinator passes the current draft and feedback to `doc-draft` for a targeted revision pass.

### Stage 3 — `/doc review`

The coordinator passes the current draft to `doc-review` with zero authoring context. The agent:

1. Generates 8-10 realistic reader questions
2. Attempts to answer each using only the document content
3. Marks each as ✓ (clear), △ (partial), or ✗ (missing/misleading)
4. Runs structural quality checks:
   - Internal contradictions
   - False assumptions about reader knowledge
   - Redundancy across sections
   - Filler sentences
   - Inconsistent tone or register
   - Weak or missing transitions
   - Sections that don't earn their place
5. Fixes all issues it can resolve without author knowledge
6. Escalates only issues requiring factual input or unresolved decisions

The output includes:
- Reader simulation table (questions + answer quality)
- Issues found and fixed (what changed and why)
- Escalations (only if necessary)
- Full revised document in clean markdown

---

## Session State

The coordinator tracks the following across the session:

```
doc_type         — type of document being written
audience         — intended readers
goal             — what the document needs to achieve
constraints      — length, format, scope limits
context_summary  — output from doc-context stage
assumptions      — inferences doc-context made
structure        — agreed section outline
current_draft    — most recent version of the document
review_complete  — boolean, set after /doc review runs
```

Sub-agents are stateless — they receive only what they need for their stage and nothing more.

---

## Design Principles

**Isolation over convenience.** Each sub-agent receives a scoped context package rather than the full conversation history. This prevents context bleed and keeps each stage predictable.

**No coordinator authoring.** The coordinator routes and stores — it never writes content, brainstorms, or analyzes. All creative and analytical work is delegated to sub-agents.

**Verbatim output passing.** The coordinator presents sub-agent output verbatim. It does not summarize, compress, or editorialize.

**Genuine reader simulation.** The review agent is explicitly isolated from the authoring context so its reader simulation reflects what an actual reader would experience.

---

## Usage Example

```
> /doc-coauthor   (or just: "help me write an RFC")

[Orchestrator activates, explains workflow]

> /doc start
I need to write an RFC for replacing our current job queue with a Kafka-based system.
The audience is the platform team. Main concern is migration risk.

[doc-context returns structured summary, assumed structure, questions]

> /doc draft

[doc-draft returns full RFC draft]

> Make the migration risk section more concrete, add a rollback plan

[doc-draft applies refinement]

> /doc review

[doc-review returns reader simulation + revised document]
```
