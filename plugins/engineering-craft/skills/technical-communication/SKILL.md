---
name: technical-communication
description: How to write the artifacts engineering runs on — commit messages, PR descriptions, design notes, status updates, bug reports, and delivering bad news — so readers get what they need in one pass. Use this when writing or improving any of those, when a message keeps getting misunderstood, when summarizing completed work, or when something has gone wrong and needs to be reported.
---

# Technical Communication

Code tells the machine what to do; writing tells the humans why, what happened, and what's needed from them. Most coordination failures — duplicated work, wrong assumptions shipped, decisions relitigated for the third time — are writing failures. The good news: technical writing is a small number of habits, applied consistently.

## Lead with the outcome

The first sentence answers the question the reader would ask first: *what happened?* / *what do you need from me?* / *what did you find?* Context, method, and journey come after, for those who want them.

- Bad: "So I started by looking into the session handling, and it turns out there's some interesting history here..."
- Good: "Found it: sessions expire early because the TTL is set in ms but read as seconds. One-line fix, PR up. Details below."

This is inverted-pyramid writing, and it's a kindness: the reader with ten seconds gets the point; the reader with ten minutes gets everything. Burying the conclusion doesn't build suspense — it builds skimming, and skimmers miss things.

## Write for what the reader knows and will do

Before writing, answer two questions: *what does this reader already know?* and *what will they do with this?* A deploy note for the on-call engineer (what changed, how to roll back) is a different document from the same news for the product channel (what users will notice). Codenames, ticket shorthand, and abbreviations you invented mid-project are free for you and expensive for everyone else — spell things out on first use. When you must choose, err toward slightly over-explaining: the expert skims past a sentence they didn't need; the newcomer cannot skim past a gap.

## Commit messages: the "why" is the payload

The subject line says what changed at a glance — imperative mood, specific: `fix: reject refunds on already-shipped orders`, not `fix bug` or `updates`. The body carries what the diff *cannot* show: why the change was needed, what alternatives were rejected and why, what constraint shaped it ("we can't touch the schema until the mobile clients update"). Six months from now, `git blame` will deliver this message to a confused engineer at the exact moment they need it ([[exploring-unfamiliar-code]] reads history for this reason; write the history it hopes to find).

## PR descriptions: problem → approach → proof

A reviewable PR description has four short parts:

1. **Problem** — what was broken or missing, with a link to the ticket. One sentence to one paragraph.
2. **Approach** — what you did and, for anything non-obvious, why this way ("considered X, but it breaks Y").
3. **Proof** — how you verified it: tests added, manual checks run, *and what you couldn't verify* ("not tested against SSO; needs staging"). Screenshots for anything visual.
4. **Risk & rollback** — anything the reviewer should worry about; how to undo it if wrong.

This isn't ceremony — it's the difference between a reviewer who checks your reasoning and one who reverse-engineers it ([[reviewing-code]] starts by reading exactly this).

## Status updates: three lines, no narrative

**Done** (outcomes, not activities — "shipped X", not "worked on X") / **Next** / **Blocked** (what, on whom, since when). If blocked is non-empty, that's the headline — move it up. Resist the epic: nobody needs the story of your Tuesday, and burying "I'm blocked" in paragraph four means two more days blocked.

## Bad news: immediately, plainly, with a plan

Failing tests, a slipping estimate, a wrong earlier claim, data touched by a bug — report it the moment you're confident it's real, because bad news is the *most* time-sensitive information there is: every option is cheaper today than Friday. The formula: **what happened, impact, what I'm doing, what I need.** No cushioning preamble, no spin, no burying the number ("some customers" when you know it's 4,000). Precision under pressure is what makes people trust your good news too. Delivering bad news well is a promotion-grade skill; hiding it is a career-grade mistake — and the org where bad news travels fast is the org that ships ([[incident-response]] is this skill at emergency speed).

## Design notes and decision records

For any decision that will be questioned later (that is: any one-way door from [[architecting-solutions]]): context, options considered with their costs, decision, consequences accepted. Half a page. The test of a good design note is that a person who joins in a year reads it and stops asking "why on earth is it built this way" — the document that kills the same debate the third time it respawns pays for itself forever.

## Editing: the pass most people skip

Write the draft fast, then reread it once *as the reader*: cold, without your context. Cut the throat-clearing ("I just wanted to quickly note that..."), replace abstractions with the concrete ("improve performance" → "p95 from 800ms to 200ms"), check that the first sentence still carries the point, and delete anything the reader won't act on. One rereading pass catches the ambiguity that would otherwise cost a full round-trip of "wait, what did you mean by...?" — the most expensive sentence in engineering.
