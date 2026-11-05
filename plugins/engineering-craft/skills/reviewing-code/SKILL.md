---
name: reviewing-code
description: How to review code effectively — understanding intent first, hunting correctness bugs over style, verifying claims instead of trusting the diff, ranking findings by severity, and writing comments that land well. Use this when reviewing a PR or diff, when asked "can you look at my code?", when auditing a change before release, and when deciding whether to approve, request changes, or let a nit go.
---

# Reviewing Code

A review has two customers: the codebase, which needs defects caught before they ship, and the author, who needs to stay fast and motivated. A good review serves both — it is rigorous about correctness and generous about everything else. The most common review failure is inverting that: nitpicking style for twenty comments while a race condition sails through approved.

## First, understand what the change is trying to do

Read the description, the linked ticket, and the tests *before* judging any line. The tests are the author's statement of intended behavior — often clearer than the description. A review conducted without knowing the intent produces comments about the code that exists instead of the code that should exist; you cannot spot "this doesn't handle the case the ticket mentions" if you never read the ticket.

If the intent itself seems wrong — solving the wrong problem, a design that won't survive contact — raise *that* first and skip the line comments. There is no point polishing code that shouldn't exist in this shape ([[understanding-the-problem]], [[architecting-solutions]]).

## Review the blast radius, not just the diff

The diff shows what changed; the bugs live in what the change *touches*. For anything non-trivial, open the surrounding code:

- **Callers**: the function's behavior changed — do all existing call sites survive the new behavior? The diff won't show them.
- **Assumptions**: the field is nullable now — who reads it assuming it isn't?
- **Siblings**: the bug was fixed here — does the same copy-pasted pattern exist elsewhere, unfixed?
- **Contracts**: does this change an API response, an event shape, a stored format that something outside this repo depends on?

Reviewing only the green and red lines is how "the diff looked fine" becomes an incident. The diff lies by omission; the repo doesn't.

## Hunt in priority order

Spend attention where defects are expensive, in roughly this order:

1. **Correctness**: wrong logic, unhandled edge cases (empty, null, boundaries, duplicates — the gauntlet from [[testing-strategy]]), error paths that swallow or corrupt, off-by-ones.
2. **Concurrency & state**: races, missing idempotency on retried operations, partial-failure states, shared mutable state.
3. **Security**: unvalidated input reaching queries/shell/HTML, authz checks missing on new endpoints, secrets in code or logs.
4. **Data safety**: irreversible migrations, deletes without safeguards, precision loss on money.
5. **Operability**: will this be debuggable at 3am? Are failures logged with context? Can it be rolled back?
6. **Maintainability**: naming, structure, duplication — matters, but never at the expense of 1–5 getting your best attention.
7. **Style**: only what a linter *doesn't* already catch, and lightly. If style comments keep recurring, the fix is a linter rule, not more comments.

## Verify claims — don't review on trust

"Tests pass" — do they test the new behavior, or just still pass? "Handles the timeout case" — find the line that handles it. If the change is risky and you can run it, run it. For every finding you're about to raise, do the opposite too: try to *disprove* it by reading the actual code path. A review comment that's wrong costs the author an investigation and costs your future comments their credibility. The reviewer's currency is being right.

## Rank findings; report signal, not volume

A review with two confirmed bugs beats a review with twenty maybes — the author can act on it. For each finding, state the **concrete failure scenario**: not "this might have issues with empty input" but "if `items` is empty, line 42 divides by zero — crashes the report endpoint for any user with no orders." If you can't construct the scenario, either dig until you can or frame it honestly as a question. Label severity plainly: blocking (bug, will break) / should-fix (will bite later) / nit (take or leave, prefixed "nit:" so the author can triage at a glance).

## Write comments the author can use

- **Comment on the code, never the coder**: "this leaks the connection on the error path" — not "you forgot to close the connection."
- **Questions when unsure, statements when sure.** A genuine "what happens if the webhook fires twice here?" both respects the author's context and often catches real bugs. But don't dress certainty as a question — "did you mean to drop the index?" when you know they didn't is passive aggression with a question mark.
- **Give the direction, or the fix, with the objection.** "This N+1s on large accounts — batch it with `preload`" is actionable; "this is inefficient" is homework.
- **Say what's good.** "This test matrix is exactly right" is information too — it tells the author what to keep doing, and it makes the hard comments land as engineering rather than hostility.

## Approve like an adult

- **Nits alone never block.** Approve with comments and trust the author to take what's useful.
- **"Not how I'd do it" is not a finding.** If it's correct, tested, and consistent with the codebase, your alternative design is a preference. The bar is "is this good?", not "is this mine?"
- **Big diffs get worse reviews** — that's a fact about humans. Push back on grab-bag PRs ([[implementing-changes]] argues for slices from the author's side); rubber-stamping 2,000 lines because review is exhausting is how the worst bugs ship.
- **Be prompt.** A day-old unreviewed PR is a teammate blocked and a merge conflict brewing. Reviews are load-bearing work, not interruptions to it.
