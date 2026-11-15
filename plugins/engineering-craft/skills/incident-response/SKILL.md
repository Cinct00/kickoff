---
name: incident-response
description: How to handle production incidents — mitigate before diagnosing, preserve evidence, communicate on a cadence, escalate early, and turn the mess into systemic fixes via blameless postmortems. Use this when production is down or degraded, users are reporting errors, an alert is firing, a bad deploy just went out, data looks wrong, or any time the words "is prod broken?" appear.
---

# Incident Response

An incident is not a debugging session with higher stakes — it is a different activity with different rules. In normal debugging, understanding comes first. In an incident, *stopping the harm* comes first, understanding second, and the process runs on communication. Speed matters, but the panicked responder who fixes forward with untested changes is the classic way a Sev-2 becomes a Sev-1.

## Mitigate first, diagnose later

The instinct to root-cause immediately is wrong here. Users bleed while you investigate, and most incidents can be *stopped* long before they are *understood*:

- **Roll back** the recent deploy — even if you're not sure it's the cause. It usually is, and rollback is cheap to try.
- **Flip the flag** — disable the feature behind it.
- **Shed the load** — rate-limit, degrade the expensive path, serve cached/stale.
- **Fail over** — reroute from the sick node/region/dependency.

Root cause analysis happens *after* the bleeding stops, from evidence, without a timer running. The strong default under pressure: **roll back rather than fix forward.** A fix written in panic and deployed without review is a second incident wearing a cape. Fix forward only when rollback is truly impossible (the migration already ran), and then with a second pair of eyes even at 3am.

## First five minutes: what changed?

Most incidents are caused by a change: a deploy, a config edit, a feature flag, a dependency's release, a certificate expiring, a data or traffic shape shift. The fastest diagnostic question is not "what's wrong?" but "**what's different?**" Check the deploy log and the change history against the incident start time before diving into any code. Correlation isn't proof — but it's an excellent place to start rolling back.

While you look, snapshot the evidence *now*: logs get rotated, metrics get downsampled, auto-scaling replaces the sick instance and its state with it. Copy the error logs, screenshot the graphs, save a heap dump if relevant — thirty seconds of preservation saves the postmortem from "we'll never know."

## Someone runs the incident — and it might as well be you

The failure mode of group response is five people silently debugging the same log file while nobody rolls anything back. The fix is a role, not a hero: the **incident commander** — coordinating, deciding, communicating, and deliberately *not* deep-diving (delegation is the job; you cannot run the incident from inside a stack trace). If you're first on scene and no one has the role, say "I'm running this until someone senior takes over" — claiming it is a service, not a power grab. Escalate early and shamelessly: waking a colleague for a false alarm costs an apology; not waking them costs an hour of outage. Nobody competent resents the page; everybody remembers the hour.

## Communicate on a cadence, even when nothing changed

Silence during an incident reads as "nobody is handling this," and it summons a second incident: the flood of "any update?" pings that consume the responders. Post to the incident channel on a fixed rhythm — every 15–30 minutes by severity — with four lines: **impact** (who/what, how bad, since when), **status** (mitigated / investigating / monitoring), **what we're doing**, **next update at HH:MM**. "Still investigating, next update 14:30" is a *good* update — it buys calm. Keep a timestamped log as you go ("14:07 rolled back v2.3.1, error rate unchanged") — it's how joiners onboard without interrupting, how handoffs survive, and it becomes the postmortem timeline for free ([[technical-communication]]: bad news, plainly, with a plan).

## Verify the recovery — the second dip is the embarrassing one

"The graph is going down" is not "resolved." Confirm the actual user experience works end to end, check for collateral state (a queue that backed up and now needs draining, cron jobs that missed their window, caches full of errors cached during the outage), and *watch through the next danger window* — the next traffic peak, the next scheduled run — before declaring victory. Declaring resolved and dipping again an hour later costs more trust than the original incident did.

## The postmortem: fix the system, not the person

Within a few days, while memory is fresh, write it: timeline, impact quantified, root cause, what went well/poorly in the response, and action items. Two rules make it worth doing:

- **Blameless is an accuracy requirement, not a nicety.** "Alex broke prod" is always false one level down: the interesting truth is that the system let a config typo reach production with no validation, no canary, and no alarm until users called. If people fear blame, your next postmortem gets fiction — and you fix nothing. Ask "what made this mistake *possible* and *invisible*?", never "who?"
- **Action items get owners and dates or they are decoration.** The highest-value ones make the *class* of failure impossible or visible: validate config at deploy time, alert on the symptom that went unseen for 40 minutes, add the missing rollback lever, write the regression test ([[debugging-systematically]], [[testing-strategy]]). "Be more careful" is not an action item — carefulness was already fully deployed.

An incident is the most expensive lesson your systems will ever buy. The postmortem is how you avoid paying tuition twice.
