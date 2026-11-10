---
name: refactoring-and-legacy-code
description: How to change code safely when it is old, untested, load-bearing, or scary — characterization tests, seams, small reversible steps, and incremental replacement instead of rewrites. Use this when modifying legacy code, cleaning up technical debt, restructuring modules, deleting old code, working in a codebase with poor tests, or whenever anyone (including you) proposes "let's just rewrite it".
---

# Refactoring and Legacy Code

Legacy code is code that makes money and makes you afraid — both at once. The fear is rational: it encodes years of fixes for problems nobody remembers having. The discipline of this skill is how to change such code without triggering the problems it silently solves, and how to leave it less scary than you found it.

## The prime rule: never change behavior and structure in the same step

Every change is one of two kinds, and mixing them is how refactors break production:

- **Refactoring**: structure changes, behavior provably identical.
- **Feature/fix**: behavior changes, structure as untouched as possible.

Keep them in separate commits at minimum, separate PRs when substantial. The reason is diagnostic: when a mixed change breaks something, you cannot tell whether the restructuring or the behavior change did it — you've destroyed your own evidence. And a reviewer facing 400 lines of moved code hiding 10 lines of real change will verify neither. When a feature requires restructuring first, do it as "make the change easy, then make the easy change" — refactor commit, then feature commit.

## Pin current behavior before touching it

Untested code you're about to change needs a safety net *first*. Write **characterization tests**: run the code, observe what it actually does, and assert exactly that — including the weird parts. You are not testing what the code *should* do (nobody knows anymore); you are photographing what it *does* do, so any change you cause is visible.

The crucial discipline: when characterization reveals something bizarre — rounding down instead of half-even, silently skipping records with null emails — **pin the bizarre behavior too**. Some downstream consumer may depend on it. Changing it might be right, but that is a behavior change: separate step, deliberate decision, its own announcement.

Cheap characterization tricks: golden-master tests (feed in recorded real inputs, snapshot the outputs, diff after refactoring), and running old and new implementations side by side on production traffic, comparing results before cutting over.

## Ask the fence why it's there

Before deleting or "fixing" anything inexplicable — the sleep(2), the double-check, the special case for one customer ID — find out why it exists. `git blame` the line, read the commit message, find the PR, find the incident. Two outcomes:

- **There was a reason and it still holds** → the weirdness stays, and now it gets a comment explaining itself so the next person doesn't repeat your investigation.
- **There was a reason and it's obsolete** (or there was never a reason) → delete with confidence, citing the evidence.

The code that looks the most wrong is the code most likely to encode an invisible requirement. Confusion is data, not noise.

## Move in steps small enough to be boring

The codebase should build, pass tests, and be shippable after *every* step — rename, then move, then split, each verified independently. Use mechanical/tool-assisted transformations (IDE renames, automated codemods) over hand-editing when possible; use the compiler as a fence (change a signature, fix every red mark) in typed languages.

Small steps are not caution theater — they change the failure mode. When a big-bang refactor breaks, you debug an ocean and often end up reverting a week. When a boring step breaks, the diff is twenty lines and the revert is one click. Momentum through many safe steps is far faster than one heroic leap plus its recovery.

## Improve what you touch — and stay on your leash

The boy-scout rule (leave code better than you found it) is how codebases heal: name the variable properly, add the missing test, extract the copy-pasted block *in the area your task already touches*. The leash: your improvement must not dominate the diff or the risk of the change you came to make. "I came to fix a bug and refactored the module" means the bug fix now carries the refactor's risk and awaits the refactor's review. When you spot something bigger, write it down (a ticket, a note) and finish your actual task — captured debt is manageable; ambushed debt is not.

## Replace systems strangler-style, never big-bang

The full rewrite ("it'll be faster to start over") fails so reliably it has a pattern named against it. The rewrite must chase years of accumulated edge-case knowledge while the old system keeps evolving; meanwhile the business runs on the thing you've stopped maintaining. The odds are bad and the failure is total.

Instead, strangle: put a routing layer in front of the old system, move one behavior at a time to the new one, compare outputs in shadow mode, cut traffic over slice by slice, and delete the old path as each slice proves out. It feels slower; it is the version that *finishes*. Value ships from month one, knowledge transfers incrementally, and at every point you can stop and still be better off — which is precisely the property big-bang lacks.

## Delete like you mean it

Dead code is not neutral — every reader pays to determine it's dead, every grep returns it, every refactor drags it along. When something is unused: delete it, don't comment it out ("in case we need it" is what version control is; `git log` remembers). Verify deadness by callers and, when in doubt, by telemetry — log the entry point in production for a few weeks before removing. Deleting a thousand lines with confidence is one of the highest-value contributions there is, and it takes exactly the same care as adding them: read [[exploring-unfamiliar-code]] for finding true usage, and pin behavior at the boundaries before amputating near live tissue.
