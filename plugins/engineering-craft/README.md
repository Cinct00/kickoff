# engineering-craft

Judgment skills for software work: understanding the problem, scoping, implementing, exploring code, architecture, debugging, testing, reviewing, refactoring, incidents and technical communication.

Part of [ai-toolkit](../../README.md).

<!-- BEGIN GENERATED:install -->
## Install

Claude Code:

```
/plugin marketplace add gimarais/ai-toolkit
/plugin install engineering-craft@ai-toolkit
```

GitHub Copilot CLI:

```bash
copilot plugin marketplace add gimarais/ai-toolkit
copilot plugin install engineering-craft@ai-toolkit
```

Any other Agent Skills client: copy or link `skills/*` into `~/.agents/skills/` (or run `python3 scripts/toolkit.py install --target skills` from the toolkit).

## Contents

| Skill | Description |
|---|---|
| [`architecting-solutions`](skills/architecting-solutions/SKILL.md) | How to design a solution before building it — generating options, weighing trade-offs, choosing where to spend design effort, and writing decisions down. Use this for any task bigger than a one-file change - new feature… |
| [`debugging-systematically`](skills/debugging-systematically/SKILL.md) | A hypothesis-driven method for diagnosing and fixing bugs — reproduction, bisection, instrumentation, and verifying the real cause instead of patching symptoms. Use this whenever there is a bug, error, crash, failing te… |
| [`exploring-unfamiliar-code`](skills/exploring-unfamiliar-code/SKILL.md) | How to orient quickly in an unfamiliar codebase or an unfamiliar corner of a familiar one — building a working mental model without reading everything. Use this whenever starting work in a repo you don't know, picking u… |
| [`implementing-changes`](skills/implementing-changes/SKILL.md) | How to actually write a change once the problem and approach are clear — slicing work, matching the codebase, handling errors, naming, self-review, and verifying before declaring done. Use this for any feature, fix, or… |
| [`incident-response`](skills/incident-response/SKILL.md) | How to handle production incidents — mitigate before diagnosing, preserve evidence, communicate on a cadence, escalate early, and turn the mess into systemic fixes via blameless postmortems. Use this when production is… |
| [`refactoring-and-legacy-code`](skills/refactoring-and-legacy-code/SKILL.md) | How to change code safely when it is old, untested, load-bearing, or scary — characterization tests, seams, small reversible steps, and incremental replacement instead of rewrites. Use this when modifying legacy code, c… |
| [`reviewing-code`](skills/reviewing-code/SKILL.md) | How to review code effectively — understanding intent first, hunting correctness bugs over style, verifying claims instead of trusting the diff, ranking findings by severity, and writing comments that land well. Use thi… |
| [`scoping-and-estimation`](skills/scoping-and-estimation/SKILL.md) | How to size work honestly, slice it into shippable increments, handle uncertainty with spikes, and renegotiate scope when reality disagrees with the plan. Use this when asked "how long will this take?", when planning a… |
| [`technical-communication`](skills/technical-communication/SKILL.md) | How to write the artifacts engineering runs on — commit messages, PR descriptions, design notes, status updates, bug reports, and delivering bad news — so readers get what they need in one pass. Use this when writing or… |
| [`testing-strategy`](skills/testing-strategy/SKILL.md) | How to decide what to test, at what level, and how to write tests that catch real regressions without calcifying the code — edge case enumeration, mocking boundaries, determinism, and regression tests. Use this when wri… |
| [`understanding-the-problem`](skills/understanding-the-problem/SKILL.md) | How to take an ambiguous task, ticket, or request and turn it into a clear problem statement with acceptance criteria before writing any code. Use this at the start of every non-trivial task — especially when a request… |
<!-- END GENERATED:install -->
