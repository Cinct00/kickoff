---
name: architecting-solutions
description: How to design a solution before building it — generating options, weighing trade-offs, choosing where to spend design effort, and writing decisions down. Use this for any task bigger than a one-file change - new features, new services, schema changes, API design, choosing between libraries or approaches, "how should we structure this?" questions, and whenever someone (including you) proposes jumping straight to the first workable idea.
---

# Architecting Solutions

Design is the act of choosing trade-offs *on purpose*. Every solution has costs — the only question is whether you picked them or they picked you. This skill is not about producing architecture documents; it is about a repeatable way of thinking that scales from a function signature to a system, and takes minutes for small decisions and days only for the rare big ones.

## Generate at least two real options

The first workable idea is rarely the best one, but it is always the most seductive one, because you already have it. Force a second genuine option (not a straw man) before committing. Useful generators:

- **The dumb version** — what is the crudest thing that would work? A cron job instead of an event system. A JSON column instead of three tables. Often the dumb version is the right version, and when it isn't, it becomes your baseline for judging what the complexity of the smart version is buying.
- **The opposite version** — if option A is push, sketch pull. If A is compute-on-write, sketch compute-on-read. Inverting the main axis reliably produces a real alternative.
- **The buy version** — does the platform, the framework, or an existing internal service already do this? The best code is code you don't own.

For each option, one honest paragraph: how it works, what it costs, what breaks it. If you can't say what breaks an option, you don't understand it yet.

## Classify the decision: one-way or two-way door

Spend design effort proportional to the cost of being wrong.

- **Two-way doors** (easy to reverse): internal function structure, most library choices behind an interface, UI layouts, naming. Decide fast, ship, and let reality vote. Extended deliberation here is waste.
- **One-way doors** (expensive to reverse): data schemas and anything that accumulates state, public API shapes and wire formats, event/message contracts, anything third parties integrate against, the split between services. These deserve the second opinion, the design note, the extra day.

The most common architecture failure is inverted effort: weeks debating a folder structure (two-way) while a schema ships unreviewed (one-way).

## Design the data first, the interface second, the code last

- **Data**: get the schema, the ownership, and the lifecycle of state right first. Code is easy to change; data that has accumulated is not. Ask: who writes this, who reads it, how does it get deleted, what happens when its shape changes?
- **Interface**: write the function signature, the API endpoint, the event payload *before* the implementation. Sketch the call site: write the three lines of code a consumer would write to use it. If those lines are awkward, the design is wrong, and you just found out at the cheapest possible moment.
- **Code**: falls out of the first two more often than not.

## Ask what happens when it fails

For every component and dependency in the design, run the failure catechism: what happens when it is *slow*? *down*? *returns garbage*? *called twice*? The answers separate designs that degrade from designs that collapse. You are not required to handle every failure — you are required to *know* what happens and decide it is acceptable. "The queue backs up and we page after 10 minutes" is a fine answer. "Huh, I'm not sure" is not.

Pay special attention to: retries (do they make it worse? is the operation idempotent?), partial failure (step 2 of 3 succeeded — what state are we in?), and anything that fans out.

## Spend novelty carefully

Prefer the technology already in the codebase, even when something newer is somewhat better. Every new tool costs its learning curve, its operational surface, and a permanent tax on everyone who touches the system after you. You get a small novelty budget per project — spend it where the boring option genuinely cannot do the job, and nowhere else.

Same principle inside the code: prefer patterns the codebase already uses. A mediocre pattern applied consistently beats a brilliant pattern applied once.

## Design for the real scale, honestly

Get the actual numbers: current traffic, data volume, growth rate. Design for roughly 10x current — that covers success without paying for fantasy. Designing for 1000x buys distributed-systems complexity that will cost you every single day, in exchange for solving a problem you will most likely never have — and if you do have it someday, you will be rewriting anyway, with far better information than you have now.

## Prefer structures that are easy to delete

Optimize for removability over extensibility. Speculative extension points (plugin systems, strategy patterns, config for things nothing configures) are bets that you can predict the future; they usually lose, and they cost complexity even when unused. A small, concrete, well-isolated module that can be deleted and replaced in an afternoon is worth more than a flexible framework — because the honest answer to "what will this need to do next year?" is "I don't know."

## Write the decision down

For anything one-way-door sized, write a short design note — half a page is usually enough:

```
## Context      — the problem and the constraints (2-4 sentences)
## Options      — the real candidates, one paragraph each, with costs
## Decision     — what we picked and the deciding reason
## Consequences — what we accepted: known limitations, revisit triggers
```

The value is threefold: writing it exposes holes in your thinking before code does; reviewers can engage with the design instead of reverse-engineering it from a diff; and in two years, "why is it built this way?" has an answer ([[technical-communication]] for how to write it well).

## Anti-patterns

- **Resume-driven design** — choosing tech for what it does for you, not the system.
- **Designing in the abstract** — architecture with no sketched call sites, no data samples, no numbers. If there is no concrete example in the design, it is fiction.
- **Consensus as a goal** — a design everyone is lukewarm about is usually worse than one option done with conviction. Seek *review*, not averaging.
- **The big rewrite** — if the design's first step is "replace the existing system", go read [[refactoring-and-legacy-code]] and come back with a strangler plan.

When the design is settled, size the work ([[scoping-and-estimation]]) and build it in slices ([[implementing-changes]]).
