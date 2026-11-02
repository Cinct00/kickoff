---
name: change-review
description: "Review a pull request, branch or local diff from its structural change map instead of a raw diff: symbol-level changes, a risk-ranked review order, callers outside the diff that a change may break, affected and missing tests, dependency changes, plus a visual report (PR comment with a Mermaid dependency view, interactive HTML) and a token-budgeted pack for AI reviewers. Use when reviewing or self-reviewing changes, preparing a PR description, explaining what a PR does, or feeding a PR to an AI reviewer."
---

# Change review

A raw diff shows lines. Reviewers need to know what changed structurally, what it can break, and where to look first. `codemap review` answers that from the repository index, at a fraction of the tokens of reading the patch and the changed files.

Run it like any codemap command (MCP tool `codemap`, `codemap` on PATH, or `python3 <codemap plugin>/scripts/codemap.py`).

## 1. Get the change map

| Situation | Command |
|---|---|
| Your branch or uncommitted work vs the default branch | `codemap review` |
| A specific range | `codemap review --base origin/main --head HEAD` |
| A GitHub PR, locally | `git fetch origin pull/<N>/head:pr-<N>` then `codemap review --base origin/main --head pr-<N>` (the index reflects your checkout, so check out `pr-<N>` for accurate impact) |

The default text brief (~1k tokens) gives the summary, **attention** items, the **review order** with reasons, and per-file symbol changes: `~` signature changed, `-` removed, `→` renamed or moved, `*` modified, `+` added.

## 2. Review in risk order

1. **Verify every attention item first.** "Signature changed but N files outside this change still use it" and "removed but still referenced" are the commonest real bugs in AI-written and large PRs. Confirm each with `codemap show path:line` at the listed call sites.
2. **Walk files in the review order.** Risk combines dependency centrality, churn, public API changes, callers outside the diff, sensitive paths (auth, data, infra, CI) and test coverage. Read changed symbols with `codemap show <Symbol>`; read neighbours with `refs`, `callers`, `impact`.
3. **Check the tests line.** "Likely affected, not changed" tests should be run; "changed code with no tests" deserves a question or a test.
4. **Dependencies:** new packages need a reason; version bumps need a changelog glance.
5. Pair with the `reviewing-code` judgment skill for what to look for. For a deep pass, hand each high-risk file's section of the pack to the `pr-review-toolkit` agents.

## 3. For AI reviewers (including you)

`codemap review --format context --budget 8000` produces a risk-ordered pack: summary, attention, dependencies, affected tests, then each file's symbol changes and hunks, highest risk first, until the budget is spent, with the rest listed by name. Give this to a reviewer instead of the full patch. Measured on 18 real commit ranges: 84–99% fewer tokens than patch + changed files on 7–251-file changes; 59–78% on 4-file PRs, where it adds structure rather than cutting much.

## 4. Show it visually

- **PR comment**: `codemap review --format md` prints Markdown with a Mermaid dependency view (GitHub renders it) and a review-order table. Post it only with the user's yes.
- **Every PR automatically**: `toolkit.py adopt <repo> --review-workflow` adds a workflow that posts and updates that comment, writes the job summary (works on fork PRs too) and uploads the interactive HTML report and the AI-review pack as an artifact.
- **Locally**: `codemap review --format html --out change-map.html` gives a self-contained page with a clickable dependency graph, risk-ordered files, symbol changes and coloured diffs.
- `--format json` for other tools.

## Limits

Signature and reference analysis is name-based with import awareness, not type checking: dynamic dispatch, reflection and string-based wiring are invisible, and overloaded names can produce extra "callers". Treat attention items as leads to verify, not verdicts.
