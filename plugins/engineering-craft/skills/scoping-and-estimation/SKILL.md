---
name: scoping-and-estimation
description: How to size work honestly, slice it into shippable increments, handle uncertainty with spikes, and renegotiate scope when reality disagrees with the plan. Use this when asked "how long will this take?", when planning a feature or sprint, when a task balloons mid-flight, when deciding what to cut under deadline pressure, or when breaking an epic into tickets.
---

# Scoping and Estimation

Estimates go wrong for one root reason: they are guesses about the *known* part of the work, and the schedule is eaten by the unknown part. The craft is not predicting better — nobody predicts well — it is structuring work so that being wrong is cheap: slicing for early feedback, probing uncertainty before committing to it, and renegotiating the moment the picture changes instead of at the deadline.

## Slice vertically: every increment ships something real

Break work into slices that each deliver observable value end to end — a thin path through all the layers — rather than horizontal strata ("first all the models, then all the APIs, then the UI").

- Horizontal: three weeks of foundation, integration surprises discovered in week four, nothing demoable until the end. If priorities shift mid-way, you own a basement with no house.
- Vertical: "users can upload one file (no progress bar, 10MB cap)" ships in week one — and immediately teaches you about the auth quirk and the proxy limit that would otherwise have ambushed week four.

Vertical slices front-load the risk discovery and mean that *stopping at any point still leaves value shipped*. That property — stoppable without loss — is the definition of a well-scoped plan.

## Estimate by comparison, in ranges, with "done" defined

- **Compare, don't introspect.** "This is like the export feature, which took two weeks" beats decomposing into imagined hours — imagination reliably omits the friction. Your history of similar *finished* work is your best data; consult it.
- **Give ranges that encode confidence.** "Three days to two weeks" is honest and useful — it tells the listener the uncertainty is real and where it lives ("three days if the API supports batch, two weeks if we paginate manually"). A false point estimate is a promise you've already broken.
- **Estimate to *done*, not to "code works on my machine".** Done includes tests, review cycles, deployment, documentation, and the integration friction that is always there. If your gut says "two days of coding", the honest estimate for *delivered* is usually near double — not because of padding, but because coding is one line item in delivery.
- **Never silently cut quality to hit a number.** Dropping the tests to make Friday isn't meeting the estimate — it's borrowing at loan-shark rates and hiding the loan.

## Spike the unknowns before pricing them

When an estimate hinges on something nobody knows — "can their API even do this?", "does the legacy importer handle unicode?" — don't average your hopes into a number. Cut a **spike**: a timeboxed investigation (hours to a couple of days) with a *specific question* going in and a decision coming out. Prototype the risky 10% first; throw the prototype away without guilt (its output is the answer, not the code). "One day to find out whether this is a one-week or two-month feature" is the cheapest insurance in engineering — and the estimate you give after the spike is real, where the one before it was a coin flip in a suit.

## Watch for the balloon, and say so the day you see it

Mid-task, the signals that scope has changed: the "small change" is touching its fifteenth file; each layer of the onion reveals another; the third "while I'm in here" has appeared; you're solving a problem the ticket never mentioned. When you notice, **stop and reassess against the original goal** — don't grind forward on sunk cost, and don't silently absorb the growth into nights and weekends (that hides the true cost from the people planning around it, and it isn't sustainable anyway).

The renegotiation message is short ([[technical-communication]] — bad news, immediately, with a plan): *what changed, what it means for the estimate, options.* "The import rework turns out to require touching billing. Options: (a) full version, +2 weeks; (b) ship without legacy formats, on time; (c) pause and re-scope. I'd pick (b)." Delivered the day you discover it, this is competence and everyone can still choose; delivered at the deadline, the same facts are a failure and nobody can.

## Cut scope by features, hold the line on quality

When the deadline is fixed and the work doesn't fit, the negotiable dimension is *what* ships, never *how well*:

- **Cut whole features, not their integrity.** "Ships without CSV export" is a clean cut — visible, priced, restorable later. "Ships with untested CSV export" is a hidden defect scheduled for production.
- **Ship the walking skeleton**: the smallest version that genuinely works — fewer options, lower limits, manual steps where automation was planned — each limitation *stated*, not discovered.
- **Distinguish deferred from dropped.** Deferred work gets a ticket with context while it's fresh; otherwise "phase two" is where scope goes to be forgotten and rediscovered as an outage.

## Calibrate on your own history

After each project of any size, spend five minutes: what did I estimate, what did it take, where did the difference come from? The gap is almost never coding speed — it's the category you forgot (review latency, environment fights, the dependency that wasn't ready, the meeting tax). Your personal multiplier between "feels like" and "took" is remarkably stable; learn it once and apply it forever. This habit is the difference between engineers whose estimates are trusted and engineers whose estimates get mentally doubled by everyone who hears them.
