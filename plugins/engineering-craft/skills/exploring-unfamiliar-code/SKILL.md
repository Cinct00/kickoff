---
name: exploring-unfamiliar-code
description: How to orient quickly in an unfamiliar codebase or an unfamiliar corner of a familiar one — building a working mental model without reading everything. Use this whenever starting work in a repo you don't know, picking up a service another team owns, answering "where does X happen?" questions, onboarding onto a project, or any time you catch yourself scrolling through files without a strategy.
---

# Exploring Unfamiliar Code

The goal of exploration is a *working mental model*, not complete knowledge. You need to know enough to make your change safely and predict its blast radius — nothing more. Reading a codebase like a novel, file by file, is the slowest possible way to get there. Explore like an investigator: follow specific questions through the code and let everything irrelevant stay unread.

## Start from the edges

Every codebase has entry points where the outside world comes in. Find them first — they anchor everything else:

- **Services**: route definitions, request handlers, RPC/queue consumers, cron/scheduled jobs.
- **CLIs**: the `main` function, argument parser, command registry.
- **Libraries**: the public exports — what the README tells users to call.
- **Frontends**: the top-level routes/pages and the state store.

Also read, in order of payoff per minute: the README, the build/config file (dependencies tell you the tech stack and its idioms), the directory tree two levels deep, and the CI config (it tells you how the project defines "working").

## Trace one representative flow end to end

Pick one concrete operation close to your task — one HTTP request, one CLI invocation, one message — and follow it from entry to effect (response, DB write, file output). Note each layer it passes through. This single trace teaches you the codebase's layering, naming conventions, error-handling style, and where the bodies are buried, faster than any amount of broad skimming.

While tracing, keep a scratch note: files visited, one-line role of each, and anything that surprised you. Surprises are load-bearing — they mark the spots where your assumptions and the codebase disagree, which is exactly where your change will go wrong.

## Read the tests as documentation

Tests are the only documentation guaranteed to be true (they pass, or you would know). Test names enumerate the behaviors someone cared enough to pin down. Fixtures and factories show you what the data actually looks like — often more accurately than the schema. A test file for the module you are changing is usually the fastest way to learn its contract and its edge cases.

## Search by the right handle

Choosing what to grep for is a skill in itself:

- **Have an error message or UI string?** Search for the literal string — it takes you straight to the code that produced it. Strip the variable parts ("user 4211 not found" → search "not found").
- **Have a concept but no name?** Search for the *data*: a column name, a config key, an env var, a URL path segment. Data names are more stable than function names.
- **Found a function?** Search for its callers before reading its body. Knowing who calls it and when tells you what it is *for*; the body only tells you what it does.
- **Nothing hits?** The feature may live behind an abstraction (codegen, metaprogramming, config-driven dispatch) or a different vocabulary (what you call "delete", the code calls "archive"). Search for the observable behavior instead — the DB table, the API response field.

## Use history as a source

`git blame` and `git log` answer the questions code cannot:

- "Why is this weird?" — blame the weird line and read the commit message and the PR it belonged to. Weirdness with a reason must be preserved; weirdness without one can go ([[refactoring-and-legacy-code]] — Chesterton's fence).
- "How do people change this area?" — `git log --oneline -- path/` shows you the shape and size of typical changes, and who to ask.
- "Is this dead?" — code untouched for years while everything around it churns is either rock-solid or unused; callers will tell you which.

## Pattern-match before inventing

Before writing anything new, find two or three existing features similar to yours and read how they are built. If every endpoint in the codebase validates input in the handler and yours does it in the model, yours is wrong even if it is better — consistency is what keeps a codebase navigable for the next person. Copy the local pattern; if the pattern itself is bad, improving it is a separate, deliberate task.

## Timebox and change strategy

Exploration has diminishing returns and no natural stopping point, so impose one. If 20–30 minutes of searching has not answered your question, the strategy is wrong, not your effort. Escalate deliberately:

1. Different handle (see search section above).
2. Run it — a debugger breakpoint or a print statement in a real execution beats an hour of static reading, especially in dynamic languages where "who calls this" is unanswerable by grep.
3. Ask someone — with what you have tried so far, which turns "help me" into a five-minute answer.

## You know enough when

- You can predict which files your change touches, before touching them.
- You can name what might break — the callers, the consumers, the assumptions.
- You can explain the relevant flow to someone else in a few sentences.

That is the exit condition. Resist the pull to keep reading "for context" — you will learn more from making the change and being corrected by the tests than from another hour of reading.
