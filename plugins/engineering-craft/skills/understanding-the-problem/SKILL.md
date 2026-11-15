---
name: understanding-the-problem
description: How to take an ambiguous task, ticket, or request and turn it into a clear problem statement with acceptance criteria before writing any code. Use this at the start of every non-trivial task — especially when a request is vague ("make it faster", "fix the login thing"), when the requester prescribes a solution instead of describing a problem, when estimates are being asked for, or when you feel the urge to start coding immediately. If you cannot state what "done" looks like in one sentence, use this skill.
---

# Understanding the Problem

Most wasted engineering effort is not bad code — it is good code solving the wrong problem. The minutes spent here are the highest-leverage minutes of any task. The goal of this skill is simple: before you touch an editor, be able to say *what problem you are solving, for whom, and how you will know it is solved.*

## Restate the task in your own words

Write one or two sentences: "The user wants X because Y. It is done when Z."

If you cannot fill in Y (why they want it) or Z (what done looks like), you do not understand the task yet. This restatement is not busywork — it is the cheapest possible test of your understanding, and it frequently exposes gaps before they become rework.

## Separate the symptom from the problem

Requests usually arrive as symptoms or as prescribed solutions, not as problems:

- "Add a retry to this API call" — the *problem* might be that the upstream service is flaky, and a retry papers over it while making timeouts worse.
- "The page is slow, add caching" — the *problem* might be an N+1 query that caching would hide until the cache misses.
- "Add an admin override flag" — the *problem* might be a broken permission model that will need ten more flags next quarter.

When a request prescribes a solution, ask (or work out from context): *what is happening that made you want this?* Solve that. It is fine to end up implementing exactly what was asked — but arrive there deliberately, not by default.

## Take inventory of constraints

Spend a few minutes listing what boxes the solution in. The usual suspects:

- **Compatibility** — existing API consumers, stored data, config files, URL formats. Anything already depended on.
- **Conventions** — how does this codebase already solve similar problems? A solution that fights the codebase costs more forever.
- **Performance and scale** — what is the real current load, and what is realistic growth? (Get numbers, not vibes.)
- **Security and privacy** — does this touch auth, user data, money, or anything user-supplied?
- **Time** — is this a production fire, a sprint task, or a long-term investment? The right solution differs for each.

You do not need a document — a five-line list is enough. The point is to *look* before assuming the space is unconstrained.

## Define "done" as something observable

Turn the task into acceptance criteria you could hand to someone else to verify:

- Bad: "improve error handling"
- Good: "when the payment API times out, the user sees a retry prompt instead of a blank page, and the failure is logged with the order ID"

Include the negative space: what is explicitly *out of scope*? Writing down "not handling the bulk-import path in this change" prevents both scope creep and the awkward "I assumed you'd also do..." conversation.

## Decide what to ask and what to assume

You cannot ask about everything, and asking about everything erodes trust as much as asking about nothing. The dividing line:

- **Ask** when the decision is genuinely the requester's to make (product behavior, user-visible trade-offs), when getting it wrong is expensive to reverse (data migrations, public API shapes), or when two readings of the request lead to materially different work.
- **Assume and state** when a conventional default exists. Pick the obvious option, write "I assumed X — flag if wrong" in your plan or PR description, and proceed. A stated assumption costs the reader one sentence; an unstated one costs a rework cycle.

Batch your questions. One message with three crisp questions beats three interruptions.

## Do the five-minute reconnaissance

Before committing to an approach or an estimate, look at the actual territory:

1. Read the ticket/request twice, including linked issues and prior discussion — the answer to your first question is often already there.
2. Open the code area involved. Is it 50 lines or 5,000? Tested or untested? Recently touched or fossilized?
3. Check whether this has been tried before — search closed PRs, old branches, code comments. A previous failed attempt is the most informative document you will find.

Estimates and plans made before reconnaissance are guesses wearing a suit.

## Anti-patterns to catch in yourself

- **Coding as comprehension** — starting to implement in order to figure out what is needed. Exploration is fine; call it a spike, timebox it, and expect to throw it away.
- **Silent scope inflation** — "while I'm here I'll also fix..." Understand and deliver the asked-for thing first; file the rest.
- **Answer shopping** — asking questions until someone tells you to do the thing you already decided to do. If you have decided, say so and state your reasoning instead.
- **Mistaking activity for progress** — a day of work on the wrong problem is worth less than an hour spent confirming the right one.

## Output of this skill

By the end you should have, written down (a scratch note, the ticket, or the top of your PR draft):

1. The problem restated in one or two sentences, with the *why*.
2. Acceptance criteria — observable, testable, including what is out of scope.
3. The constraint list.
4. Open questions sent to the right person, and stated assumptions for everything else.

Then, and only then, move on to design ([[architecting-solutions]]) or straight to implementation for small tasks ([[implementing-changes]]).
