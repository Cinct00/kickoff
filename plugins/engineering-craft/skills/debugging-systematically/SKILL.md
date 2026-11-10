---
name: debugging-systematically
description: A hypothesis-driven method for diagnosing and fixing bugs — reproduction, bisection, instrumentation, and verifying the real cause instead of patching symptoms. Use this whenever there is a bug, error, crash, failing test, flaky behavior, "works on my machine" situation, or unexplained output — even when the fix looks obvious, and especially after two failed fix attempts, which is the signal that guessing has replaced method.
---

# Debugging Systematically

Debugging is not a search for the fix — it is a search for the *explanation*. Once you truly know why the system misbehaves, the fix is usually five minutes of typing. Every undisciplined shortcut ("let me just try changing this") trades that understanding for a lottery ticket. The method below feels slower than guessing; over any bug that matters, it is dramatically faster.

## Step 0: Read the error. All of it.

The error message is the only witness that was actually there. Read the whole thing — the exception type, the message, the *bottom* frames of the stack trace (the top is often framework noise; the bottom-most frame in *your* code is where to look), the caused-by chain, the line numbers. A remarkable fraction of debugging time is spent rediscovering facts the error message stated outright.

If there is no error — just wrong behavior — write down precisely: *expected X, observed Y*. Vague symptoms ("it's broken") produce vague investigations.

## Step 1: Reproduce it, then shrink it

A bug you cannot reproduce is a bug you cannot verify is fixed — any "fix" for it is superstition. Get a reproduction, then make it *small and fast*: fewer steps, less data, no UI if a unit test can trigger it, milliseconds instead of minutes. Every factor you remove from the reproduction is a factor eliminated from the suspect list, and a tight repro loop is what makes the rest of the method cheap.

If it reproduces only sometimes, suspect the usual nondeterminism: timing/concurrency, shared state between runs, time-of-day and timezone, data-dependent paths, environment differences. Make it more frequent (loop it, add load, pin the clock) before hunting it.

## Step 2: Run the hypothesis loop

This is the core discipline. Each iteration:

1. **State a hypothesis** — a specific, falsifiable cause: "the cache returns stale data after a write because invalidation runs async."
2. **Predict an observation** — *before looking*: "then a read 0ms after a write shows the old value, and a read after 1s shows the new one."
3. **Test the prediction** — the cheapest experiment that could prove you wrong.
4. **Confirmed?** Narrow further or fix. **Refuted?** The hypothesis is dead — form a new one from what you just learned. Do not keep half-believing it.

Change **one variable per experiment**. When you change three things and it works, you don't have a fix — you have three suspects and no trial. The prediction step is what separates debugging from wandering: it forces each experiment to carry information either way.

## Step 3: When there's no hypothesis — bisect

If nothing plausible comes to mind, stop theorizing and cut the search space in half. Bisection needs no insight, only a way to test "is it broken at this point?":

- **In time**: did this ever work? Find a good commit and `git bisect` — mechanical, and devastatingly effective. First question regardless: *what changed recently?* Deploys, dependency bumps, config, data shape, traffic. Bugs rarely appear in code nobody touched.
- **In the pipeline**: input → A → B → C → wrong output. Check the intermediate value at B: correct? The bug is in B→C. Repeat. Halving beats staring.
- **In the input**: bug happens with this 400-line file — delete half; still broken? Recurse. Shrink until only the pathological part remains, which usually *names* the bug.

## Instrumentation that answers questions

Add logging/prints that show **state, not location**. `"here 3"` tells you the line ran; `f"order={order.id} status={order.status} total={total}"` tells you what was *true* when it ran — and it is the values that lie, not the control flow. Log at the boundaries between components first (what went in, what came out) to localize before going deep. Use a debugger when inspecting rich state beats printing it; use prints when the bug involves timing (debuggers change timing) or many iterations. Remove instrumentation when done — that's your self-review in [[implementing-changes]].

## When you are stuck

- **Question the "known good".** The most expensive assumptions are the ones you haven't noticed making: Is the code you're editing the code that's running? (Stale build, wrong environment, cached artifact — check with a deliberate syntax error or a marker log.) Is the config what you think? Is the database the one you think?
- **Explain it out loud** to a person, or in writing to nobody. Serializing your understanding forces the gap in it into the open — the classic experience of solving it mid-sentence.
- **Read the reference, not your memory of it.** When a library "misbehaves", check its actual documented behavior. Half of "library bugs" are contract misunderstandings.
- **Leave.** Twenty minutes away genuinely resets a fixated search. The stuck feeling of "I've tried everything" always means "I've tried everything within one framing."

For gnarly multi-day bugs, keep a log: hypotheses tried, experiments run, results. It stops you from re-running the same dead experiment on day three, and it is the seed of the postmortem if this came from production ([[incident-response]]).

## Fix the cause, prove it, then look for siblings

- **Fix where the fault is, not where the symptom shows.** If a null creeps in at parse time and crashes at render time, a null-check at render hides the disease and keeps the corrupt state. Trace back to where reality and the code's model first diverged; fix there.
- **Prove the fix**: reproduction fails before, passes after. Both halves — a fix you never saw fail proves nothing.
- **Add the regression test** — the reproduction is already 90% of one ([[testing-strategy]]).
- **Hunt the siblings**: the same mistake pattern rarely occurs once. Grep for the pattern you just fixed — same copy-pasted block, same misused API elsewhere. Finding three siblings turns one bug fix into a class of bugs retired.

Finally, ask what would have caught this earlier — a validation, an assertion, a type, an alert — and whether it's worth adding. The best debugging session is the one that makes the next one unnecessary.
