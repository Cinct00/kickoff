---
name: first-principles-thinking
description: How to reason from fundamentals instead of by analogy or convention — decomposing problems into what is actually true and rebuilding from there. Use this when conventional wisdom feels wrong but you can't say why, when everyone does something a certain way and nobody remembers the reason, when a "known impossible" thing matters enough to check, when costs or estimates seem inflated, or when reasoning by analogy ("it's like X, so Y") is driving a big decision.
---

# First-Principles Thinking

Most reasoning is imitation with extra steps: we do things because they resemble things that worked, cost what they've always cost, and are impossible because nobody has done them. This is usually fine — convention is compressed experience, and cheap. First-principles thinking is the expensive alternative for the moments that matter: strip a problem down to what is *actually, verifiably true*, and rebuild the answer from only that.

## The method

1. **State the belief or constraint as a claim.** "This has to cost $50k." "Users won't tolerate more than one step." "We need a bigger team to ship faster." Vague unease can't be examined; a claim can.
2. **Interrogate each supporting assumption**: Is this a *law* (physics, math, regulation — genuinely fixed)? A *fact* (currently true, could change — a price, a technology limit, a market condition)? Or a *convention* (true only because everyone keeps doing it)? The mislabeled ones are where the treasure is: most "laws" in any field are conventions wearing lab coats.
3. **Rebuild from the floor.** Keep only laws and verified facts. Ask: given only these, what is the *minimum* the solution requires? The gap between that floor and the conventional answer is your room to move. (The famous version: rockets "cost" $65M until someone priced the raw materials at 2% of that — the rest was convention.)
4. **Check the rebuild against reality cheaply** before betting on it. First-principles reasoning produces brilliant insights and confident nonsense with the same feeling of clarity; a small test distinguishes them.

## Ask "why" until you hit bedrock

The practical drill: take any "requirement" and ask why it exists, repeatedly. "Reports must go out at 6am." Why? "The team reviews them at 9." Why 9? "Because the meeting was at 9:30 — three years ago, since cancelled." Requirements decay into history astonishingly often — roughly, every rule outlives the reason for it, and only the rule gets written down. Bedrock is reached when the answer is a law, a real constraint, or a person who currently, actively wants it.

One caution inherited from [[refactoring-and-legacy-code]]: Chesterton's fence. "Nobody remembers the reason" is not the same as "there is no reason." The move is to *investigate* the fence, not to bulldoze whatever you can't explain — sometimes the 6am report feeds a process nobody mentioned.

## Analogies are search tools, not proofs

"It's like Uber for X" or "this worked at my last company" are excellent ways to *find* candidate answers and terrible ways to *validate* them. Every analogy imports hidden assumptions from its source domain, and the differences — the parts where X is *not* like Uber — are precisely where plans die. Use the analogy to generate the hypothesis, then re-derive the conclusion from this situation's own facts. If the conclusion only survives inside the analogy, it isn't a conclusion; it's a costume.

## Budget it — this tool is expensive

Reasoning everything from scratch is how you spend a week re-deriving why doors have hinges. Convention is right most of the time, and adopting it is how you move fast ([[architecting-solutions]] makes the same point about boring technology). Reach for first principles when the stakes justify the cost:

- The decision is big and hard to reverse.
- The conventional answer produces persistently bad results and incremental fixes haven't helped.
- You're stuck, and every framing you've tried is inherited.
- Someone states a limit ("can't be done", "that's the price") and a lot hangs on whether it's real.

Elsewhere, take the convention and bank the time.

## Failure modes

- **First-principles as contrarianism.** The point is to *check* the fences, not to conclude that all fences are wrong. Most conventions survive interrogation — that's why they're conventions.
- **Wrong fundamentals.** Reasoning flawlessly from a "fact" that's actually false produces confident error at industrial scale. Verify the floor before building on it ([[evaluating-information]]).
- **Ignoring switching costs.** The rebuilt answer competes against the incumbent *plus* the cost of change. Being 10% better from first principles usually loses to convention in practice — the insight has to clear the migration bar.
- **Solo bedrock.** Your "self-evident fundamentals" carry your blind spots. Walk the decomposition past someone who disagrees with you ([[making-decisions]]).
