---
name: implementing-changes
description: How to actually write a change once the problem and approach are clear — slicing work, matching the codebase, handling errors, naming, self-review, and verifying before declaring done. Use this for any feature, fix, or modification you implement, and especially when a change is growing beyond its original size, when you're about to add "flexibility for later", or when you're tempted to say "done" without having run the code.
---

# Implementing Changes

Implementation quality is mostly not about clever code — it is about a sequence of small disciplines: work in slices that always run, write code that belongs to the codebase rather than to you, and never claim "done" on faith. The craft is in the habits.

## Work in the smallest coherent slices

Break the change into steps where *the software works after every step*. A slice is coherent when it compiles, passes tests, and could in principle be merged — even if it is not useful alone yet (a new function with tests but no caller is a fine slice; half a function is not).

Why this matters: when something breaks, the suspect list is one slice long. When priorities shift, you have shippable progress instead of a construction site. When you need review, small diffs get real review — large diffs get skimmed and rubber-stamped.

Prefer vertical slices (a thin path through all layers, working end to end) over horizontal ones (all the models, then all the services, then all the handlers). Vertical slices surface integration surprises — the actual risk — in step one instead of step ten.

## Read before you write

Before editing a file, read it — not just the function you are changing, but enough to know its conventions and its callers. Before changing a function's behavior, find its call sites; they carry assumptions the function signature does not show. The bug you introduce is almost never in the code you wrote — it is in the code that depended on what you changed.

## Match the codebase, not your taste

Write code that reads like the surrounding code: its naming style, its error-handling idiom, its file organization, its comment density. Consistency is a feature — it is what lets anyone navigate any part of the system. If the local pattern is genuinely bad, improving it is its own task with its own diff ([[refactoring-and-legacy-code]]); a feature change that also relitigates style forces reviewers to untangle two changes and doubles the risk of both.

## Build only what the task needs

No speculative parameters, no hooks "for later", no abstraction until there is a second concrete use in hand. The generalized version costs more now, and — the underrated part — the first real second use case almost always wants a *different* generalization than the one you guessed, at which point the premature abstraction is an obstacle rather than a head start. Duplicate once with a clear conscience; abstract on the third occurrence, when the pattern's true shape is visible.

The same discipline sideways: resist "while I'm here" fixes. Unrelated improvements go in a note or their own change, not in this diff.

## Handle errors at the boundaries, loudly

- Validate and sanitize where data enters the system (user input, API responses, file reads) — then trust it internally. Sprinkling defensive checks through every layer obscures where validation actually lives and what is actually guaranteed.
- When an operation can fail, decide *on purpose* what happens: propagate, retry, degrade, or report — never a bare swallowed exception. A silent `catch {}` is a bug that has learned to hide.
- Fail loud and early in development; fail informative in production. Error messages should carry the context needed to act: what operation, on what data, expecting what.

## Name things for what they mean

Names are the interface humans consume. Name for the domain meaning, not the mechanics: `overdue_invoices`, not `filtered_list`. A function's name should let most readers skip its body — that is the test. If naming something is hard, that is design feedback: the thing probably has two responsibilities and wants to be two things.

Write a comment only for what the code cannot say: the *why*, the constraint, the trap ("order matters here: the webhook fires on save"). Comments that restate the code drift into lies as the code evolves.

## Review your own diff before anyone else does

Before handing the change over — to a reviewer, to CI, to the user — read the full diff top to bottom as if someone else wrote it. Every time, this catches: leftover debug prints, commented-out experiments, accidental formatting churn drowning the real change, the file you touched to try something and forgot to revert, the TODO you meant to resolve. Sending an unread diff outsources your proofreading to a more expensive reader.

## Verify — "it compiles" is not "it works"

Done means *observed working*, not "should work":

1. Run the actual thing — the test, the endpoint, the CLI command, the page. Exercise the happy path and at least the most likely failure path.
2. Run the relevant existing test suite, not just your new tests — your change's most dangerous effects are on code you didn't write.
3. Check the acceptance criteria from [[understanding-the-problem]] one by one — it is remarkably easy to build 90% of the ask and lose the last 10% in the fog of implementation.

Report results honestly: "tests pass, verified the timeout path manually" — or, when true, "tests pass but I could not verify the SSO flow locally; needs a staging check." A precise statement of what was and wasn't verified is a mark of competence, not weakness ([[technical-communication]]).

## When the plan meets reality and loses

Mid-implementation you will sometimes discover the approach is wrong — the API doesn't support what the design assumed, the "small change" touches forty files. Do not grind forward on sunk cost, and do not silently pivot to a different scope. Stop, reassess against the original goal, and if the shape of the work has materially changed, say so *now* — a one-paragraph "this is bigger than we thought, here are the options" while there is still room to choose beats a surprise at the deadline ([[scoping-and-estimation]]).
