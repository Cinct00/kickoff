---
name: testing-strategy
description: How to decide what to test, at what level, and how to write tests that catch real regressions without calcifying the code — edge case enumeration, mocking boundaries, determinism, and regression tests. Use this when writing tests for new code, deciding test coverage for a change, fixing or judging flaky tests, reviewing a test suite, or whenever the question "is this tested enough?" or "why is this test so brittle?" comes up.
---

# Testing Strategy

A test suite has exactly one job: to let you change code with confidence. Every test either contributes to that — by failing when behavior someone depends on breaks — or detracts from it, by failing when implementation details change, by flaking, or by burning minutes on every run. "More tests" is not the goal; *trustworthy* tests are.

## Test behavior, not implementation

The test should assert what the code *promises* (given this input, this output; given this action, this observable effect) — never how it delivers it (which internal methods were called, in what order, with what intermediate state). The practical test: **could a correct refactor break this test?** If yes, the test is wired to implementation and will punish exactly the improvements you want to make. Tests coupled to internals don't protect behavior — they protect the current draft of the code.

This is the root cause of "we can't refactor anything without rewriting a hundred tests" — a suite like that is a liability wearing a safety vest.

## Choose what to test by risk, not by ritual

Coverage percentage is a flashlight, not a target — it shows untested regions; it says nothing about whether the tested ones are tested *well*. Aim effort where bugs are expensive and likely:

- **Always test**: logic with branches, calculations, parsing/serialization, anything touching money/auth/user data, every boundary in the input domain, every public contract others depend on.
- **Test lightly**: straight-line glue code, framework boilerplate, trivial delegation.
- **The non-negotiable**: every bug that reaches you gets a regression test that fails before the fix and passes after ([[debugging-systematically]]). Bugs are the empirical record of where your intuition about "what needs testing" was wrong — a suite grown from real bugs beats a suite grown from ceremony.

## Enumerate edge cases systematically

Intuition finds the happy path; checklists find the bugs. Run the input through the standard gauntlet:

- **Cardinality**: empty, exactly one, many, more-than-fits (pagination limits, buffer sizes).
- **Boundaries**: zero, negative, the min/max, off-by-one on every threshold and range end.
- **Malformed**: null/missing, wrong type, truncated, duplicate, contradictory fields.
- **Text**: empty string, whitespace-only, unicode (emoji, RTL, combining chars), very long, contains the delimiter/quote/HTML you use.
- **Time**: timezone boundaries, DST transitions, end of month/year, clock skew, leap day.
- **Concurrency/repetition**: called twice (is it idempotent?), called in parallel, out of order, retried after partial success.

Not every case applies everywhere — but *ask* every question, and test the ones where the answer is not obviously safe.

## Pick the cheapest level that catches the real failure

Unit tests are fast and precise; integration tests catch what units can't (wiring, queries, contracts); end-to-end tests catch what nothing else can, at 100x the cost and 100x the flake rate. The classic pyramid — many unit, fewer integration, few e2e — is right as a default, with one refinement: put the test at the level where *this codebase's real regressions* happen. If your bugs live in SQL queries and service boundaries, unit-testing pure functions to 100% while mocking every query is testing where the light is good instead of where you dropped the keys.

## Mock at the boundaries you don't control — and nowhere else

Fake the external world: third-party APIs, the network, payment providers, anything slow, nondeterministic, or not yours. Do **not** mock your own internals just to isolate a class from its neighbor — every internal mock is an assumption about a collaborator frozen into a test, and when the real collaborator changes, your tests keep passing while production breaks. A test suite that mocks its own database everywhere verifies only that the code agrees with itself.

When you mock an external service, mock its *failure modes* too — timeouts, 500s, malformed responses. The happy-path mock tests the integration you'll never worry about.

## Make tests deterministic or delete them

A flaky test is worse than no test: it costs a run every time, and it trains everyone to click "re-run" on failures — which is the reflex that eventually waves a real bug into production. The usual culprits and their cures:

- **Real time** → inject/freeze the clock. **Sleeps** → replace with explicit waits on conditions.
- **Real randomness** → seed it. **Shared state** (DB rows, files, globals, test order) → isolate per test; any test must pass alone and in any order.
- **Real network** → fake it (see mocking).

When a flake appears, fix it or delete the test *that day* — quarantine rots.

## Write tests that read as specification

The name states behavior and condition: `test_refund_rejected_when_order_already_shipped`, not `test_refund_2`. The body follows arrange–act–assert, visibly. Prefer duplication over cleverness in tests — a reader should understand a failing test without decoding helpers, fixtures three files away, or a loop generating twenty cases. Assert the *specific* expected value, not merely "no exception was thrown". When a test fails six months from now, its name plus its assertion message should tell the story without archaeology: `assert result.status == "rejected"` with a message beats `assert result` with none.

## The meta-rule

Watch what your tests do over six months. Tests that have never failed and never could (asserting mocks return what you stubbed) are dead weight — delete them. Tests that fail on every refactor but never caught a bug are coupling — rewrite them against behavior. Tests that caught real regressions are the treasury — study what makes them work and write more like those.
