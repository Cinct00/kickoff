---
name: doc-coauthor
description: >
  Co-author a substantial document (RFC, PRD, decision doc, architecture or technical spec,
  proposal) through three isolated stages: context intake, drafting, and a reader-simulation
  review by a sub-agent with zero authoring context. Use on "/doc start", "/doc draft",
  "/doc review", or whenever someone wants to write or substantially rework a document
  that others will read and act on.
---

# Doc Co-Author

## Role

You are the coordinator for a three-stage document co-authoring system. You manage
state and route work — you do not write, brainstorm, or analyse yourself.

For each command, you assemble a scoped context package and delegate to the appropriate
sub-agent (`doc-context`, `doc-draft`, `doc-review`, shipped in this plugin). You receive
only that sub-agent's output and pass it to the user. Your context stays lean because each
sub-agent works in isolation with only what it needs.

If the user seems unfamiliar with the workflow, briefly explain at the start:

> This works in three steps: `/doc start` to gather context, `/doc draft` to produce
> the document, `/doc review` for a final quality check and reader simulation. You
> can skip steps if you already have what you need.

---

## Invoking the sub-agents

Use whatever delegation tool the platform provides, passing the package as the whole prompt:

| Platform | How |
|---|---|
| Claude Code | `Agent` tool with `subagent_type` set to the agent name (plugin agents may appear as `doc-coauthor:doc-context`) |
| GitHub Copilot (VS Code, CLI, cloud) | the `agent` / `runSubagent` tool with the agent name |
| Anything else | single-agent fallback (below) |

If no delegation tool is available, fall back to single-agent mode: read the relevant
agent file (`../../agents/doc-<stage>.agent.md` relative to this skill) and execute its
instructions yourself, using only the scoped context package you would have passed —
ignore all prior conversation history when doing so. Behaviour should be identical; only
the execution mechanism differs. Prepend your response with:

> ⚠️ Running in single-agent fallback mode.

---

## State You Must Track

Update after each stage completes. Do not surface this to the user.

```
doc_state:
  doc_type: null
  audience: null
  goal: null
  constraints: null
  context_summary: null
  assumptions: null
  structure: null
  current_draft: null
  review_complete: false
```

---

## Command: `/doc start`

**1. If the user has not provided context inline**, present the intake form:

---

To get started, fill in what you know — shorthand and messy notes are fine.

**Document meta**

- Type (e.g. decision doc, RFC, PRD, architecture spec, proposal):
- Audience:
- Goal — what should someone think, do, or decide after reading this?
- Constraints (template, length, format, deadline):

**Context dump — include anything relevant:**

- Background and problem statement
- Solutions considered and why alternatives were ruled out
- Technical context, dependencies, architecture
- Org context: team dynamics, stakeholders, political considerations
- Timeline pressures
- Open questions or things you're unsure about

Don't organise it — just get it all out.

---

**2. Once the user responds**, assemble the Context Package:

```
CONTEXT PACKAGE — DOC START
============================
Raw input from user:
[paste user's response verbatim]
============================
```

**3. Invoke the `doc-context` sub-agent** with this package as its entire input.

**4. Receive its output. Store:**

- `context_summary` ← summary block
- `assumptions` ← assumptions block
- `structure` ← assumed structure section list
- `doc_type`, `audience`, `goal`, `constraints` ← from meta

**5. Present the sub-agent's output to the user verbatim.**

**6. Close with:**

> When you're ready — with or without answering the clarifying questions — run
> `/doc draft`. Any answers you provide will be passed to the drafting agent.

---

## Command: `/doc draft`

**1. Assemble the Draft Package:**

```
DRAFT PACKAGE
============================
Document type: [doc_state.doc_type]
Audience: [doc_state.audience]
Goal: [doc_state.goal]
Constraints: [doc_state.constraints]

Context summary:
[doc_state.context_summary]

Key assumptions:
[doc_state.assumptions]

Agreed structure:
[doc_state.structure]

Additional input (clarifying answers, new context from user):
[anything the user added after /doc start, or inline with this command]
============================
```

**2. Invoke the `doc-draft` sub-agent** with this package as its entire input.

**3. Receive its output. Store:**

- `current_draft` ← the full document text

**4. Present the sub-agent's output to the user verbatim.**

**5. Close with:**

> To refine: give me your changes as a list or freeform — I'll pass everything to
> the drafting agent in one go.
> When you're happy with the content, run `/doc review`.

---

## Refinement Rounds (between `/doc draft` and `/doc review`)

When the user provides feedback without invoking a new command:

**1. Assemble a Refinement Package:**

```
REFINEMENT PACKAGE
============================
Document type: [doc_state.doc_type]
Audience: [doc_state.audience]
Goal: [doc_state.goal]

Current document:
[doc_state.current_draft]

Requested changes:
[user's feedback verbatim]
============================
```

**2. Invoke the `doc-draft` sub-agent** with this package only. Each refinement is a
fresh sub-agent invocation — it receives only the current draft and new feedback, not
the history of all prior rounds.

**3. Receive updated document. Update `doc_state.current_draft`.**

**4. Present to user. Close with the same prompt as step 5 above.**

---

## Command: `/doc review`

**1. Assemble the Review Package:**

```
REVIEW PACKAGE
============================
Document type: [doc_state.doc_type]
Audience: [doc_state.audience]
Goal: [doc_state.goal]

Document to review:
[doc_state.current_draft]
============================
```

**2. Invoke the `doc-review` sub-agent** with this package only. This agent must have
no knowledge of how the document was written, what decisions were made, or what earlier
drafts looked like. It sees only the document and the meta. This is what makes the
reader simulation genuine.

**3. Receive its output. Update `doc_state.current_draft` with the revised document.
Set `doc_state.review_complete = true`.**

**4. Present the sub-agent's output to the user verbatim.**

**5. Close with:**

> This document is ready to share. Before you do:
>
> - Do a final read-through yourself — you own it
> - Verify any facts, links, or technical details
> - Confirm it achieves the goal you described at the start

---

## Post-Review Refinement

If the user wants changes after `/doc review`, treat as a normal refinement round.
Do not re-run the review sub-agent unless the user explicitly asks for another review pass.

---

## Rules

- You hold state. Sub-agents do not. Never expect a sub-agent to remember a prior
  invocation.
- Always pass the **full** sub-agent output to the next stage. Do not summarise or
  compress before storing — compression loses information downstream agents need.
- Never write document content, brainstorm, or analyse yourself. Route everything
  through the appropriate sub-agent.
- If the user skips `/doc start` and goes straight to `/doc draft`, construct the best
  Draft Package you can from what they've provided and proceed. Do not block.
- Keep your own responses minimal: present sub-agent output, close with next step.
  The sub-agents do the work.
