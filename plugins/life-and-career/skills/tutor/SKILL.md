---
name: "tutor"
description: "Builds a persistent, personalised tutor app for a technical subject — diagnostic quiz, phased roadmap, AI lessons with practice and saved progress — published as an artifact the user comes back to. Use when the user wants a course or tutor for a language, framework or domain, or wants to resume one. Not for a one-off explanation (use learn)."
---

# Tutor

Builds one **published artifact** per subject that the learner keeps coming back to. It has three stages on one page:

1. **Assessment**: a short diagnostic that also teaches.
2. **Roadmap**: phased topics, adapted to the score and the learner's background.
3. **Tutor**: AI lessons per topic, practice tasks, free-form questions and saved progress.

## When this skill is the right one

| The user wants | Use |
|---|---|
| A course or tutor they will return to over weeks | **this skill** |
| One concept explained now ("what is a borrow checker?") | `learn` |
| A quick self-test on something | quiz card (`quiz_display`) |
| Help designing their own study routine | `learning-anything` |
| A real course or certificate | `learn-with-coursera` (needs the Coursera connector) |

## Step 0: Check for an existing tutor

Before building anything, list the user's artifacts (`Artifact` with `action: "list"`) and look for a tutor on this subject. If one exists, read it and update that artifact instead of creating a second. "Like we did for C#" means: read the C# tutor and reuse its structure.

## Step 1: Gather context (ask only what is missing)

Pull from memory, the conversation, and earlier tutor artifacts first. Ask the user only for gaps, in one AskUserQuestion call.

| Info | Why it matters |
|---|---|
| Subject and scope | e.g. "Rust for low-latency services", not just "Rust" |
| Background | Languages and systems they already know; this drives every analogy |
| Goal | Job migration, side project, interview; this shapes Phase 4 |
| Style | Practical vs theory-first; time per session |

## Step 2: Design the content (before writing any code)

**Assessment**: 5–6 multiple-choice questions spanning distinct sub-domains (e.g. Rust: ownership, traits, error handling, concurrency, async, unsafe/FFI). The distractors should be plausible mistakes someone with this background would make. Each answer reveals a 2–3 sentence explanation tied to their background.

**Roadmap**: 4 phases with 4–6 topics each:

```
Phase 1 — Foundation      core primitives, taught through their existing language
Phase 2 — Idioms          standard patterns, tooling, testing
Phase 3 — Depth           performance, internals, the hard parts
Phase 4 — Applied         their goal domain (e.g. a market-data connector in Rust)
```

The score picks the recommended starting phase. A learner can still open any topic.

**Lesson contract** (bake into the lesson prompt):
- Lead with intuition, then the mechanism, then runnable code.
- Relate the topic to their background ("like `IDisposable` in C#, except…").
- Keep it to 300–500 words unless they ask for more. Be direct; don't over-hedge.
- If a free-form question jumps ahead, answer it and flag "we go deeper on this in Phase N".
- End every lesson with:
  - **Try it**: one small task they run themselves.
  - **Recall**: 2 questions answered from memory, with an answer reveal.
  - **Next**: 1–2 follow-up questions they could ask.
- Retrieval beats rereading: when a topic is marked done, schedule a recall check 3 days later and again 10 days later, and surface due checks at the top of the Tutor stage.

## Step 3: Build and publish

Load `artifact-design` and `artifact-capabilities` first; they are authoritative for page structure and APIs. Follow the user's saved design preferences.

Declare `capabilities: { sample: {}, db: {}, user: {} }`.

- **Lessons and chat** use `sample`. It is memoryless, so every call sends the lesson-contract instructions, the learner profile, the roadmap, and the conversation so far as a messages array ending on the user turn. Stream with `onText`. Use `modelTier: "default"` and pass `cache: false` for chat. If `use("sample")` is `null`, hide the chat and show topic outlines only.
- **Progress** uses `db`, private per person: `data/users/<user.id()>/tutor/<subject-slug>` holds `{doneTopics, quizScore, recallDue: {topic: isoDate}, lastTopic}`. Load it on open with a 10 s timeout, and write once per change. Never use `window.storage` (gone) or call the API with `fetch` (blocked; use `sample`).
- **Layout**: three stages with soft transitions. Topic chips get a done state. Chat has a max-height and scroll. Code blocks render as markdown. There is a typing indicator while a lesson streams, with a few subject-flavoured loading lines (Rust: "Checking lifetimes…").

Publish with a title like "Rust Tutor", then run one `ArtifactData` list on the progress path to confirm it is writable.

## Quality checklist

- [ ] No existing tutor for this subject was duplicated
- [ ] Every analogy and example uses the learner's real background, with no placeholder text
- [ ] Assessment covers distinct sub-domains, and the distractors are realistic
- [ ] Phase 4 is about their actual goal
- [ ] Chips in the Tutor stage match roadmap topics exactly
- [ ] Each lesson ends with Try it, Recall and Next
- [ ] Progress survives a reload, and recall checks come due
- [ ] The page works (with chat hidden) when `sample` is unavailable

## Examples

**"Build me a Rust tutor — I write C# market-data connectors"**
- Assessment: ownership vs GC, `Result` vs exceptions, traits vs interfaces, `Send`/`Sync`, async runtimes.
- Phase 1: ownership and borrowing through C# references and `Span<T>`; enums and `match` vs class hierarchies.
- Phase 4: zero-copy parsing, lock-free queues, tokio vs a busy-poll loop, FFI with an existing C# service.

**"I want to learn SQL from scratch"**
- Beginner profile: build from first principles with relatable examples.
- Roadmap: queries → joins and aggregation → schema design → performance.

**"Help me get better at system design"**
- Roadmap: fundamentals → core patterns → distributed systems → real-world architectures.
- Lessons tie each concept to a practical engineering decision.