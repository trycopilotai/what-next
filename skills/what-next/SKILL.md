---
name: what-next
description: >-
  Determine the agent-addressable versus human-required
  actions at this point in a chat thread. Use on "what
  next", "what's left", "what do you need from me", or
  before handing control back: enumerate the open items,
  prove which ones are genuinely blocked on a capability the
  agent lacks, and return a two-lane split plus a short list
  of next actions.
---

# What Next

Split the open work in a thread into two lanes — what an
agent can execute now, and what only the human can do — and
hand the second lane back as a decision rather than as
prose.

Sorting items into two buckets is not the hard part.
Anything sorts into two buckets. The hard part is proving an
item belongs in the human lane before it goes there. Most of
this skill is that proof.

## When to use

- The operator asks "what next", "what's left", "what do you
  need from me", or "what can you do without me".
- A thread has accumulated open commitments and it is no
  longer obvious what is blocked.
- You are about to end a turn and need to know whether you
  are allowed to. See **Turn boundary**.
- A plan finished and the residue needs routing.

Do not run it on a thread with no open work. Answer the
question and stop.

## The rule that decides the split

**Name the next tool call.**

If you can name a concrete tool call or shell command that
advances the item, and every precondition for that call
already holds, the item is **agent-addressable** — however
long, tedious, or unfamiliar it is.

Otherwise, name the exact precondition you cannot satisfy.
That precondition is the human-required action. The task is
not.

This distinction carries the whole skill. "Deploy the
service" is never the human action; "run
`gcloud auth login`" or "authorize the deploy" is. Write the
gap, not the task.

## Demotion gate

Run this before anything enters the human lane. An item
qualifies only after a bounded search has failed to resolve
it. Work the sources in order and stop at the first one that
settles it:

1. The repo, its dataset, and its tracked state.
2. Earlier messages in this thread.
3. The document, diff, or artifact under discussion.
4. `git log`, branch state, PR and CI status.
5. The public web, including the operator's own public
   profiles and sites.

**The bound: one lookup per source, per item.** Five checks,
not five exhaustive searches. If they do not settle it, the
gate has done its job and the item may proceed.

Name the source that settled anything you demote. The
following are **not** capability gaps:

- **Unfamiliarity.** You have not done it before.
- **Effort.** It is long or tedious.
- **Reassurance.** You want to be told you are on track.
- **Re-confirmation.** The operator already authorized this
  class of work; asking again withdraws it.
- **A settleable question.** If a test, a `grep`, or a build
  would answer it, that is agent work. Run it.

An item that fails the gate is agent work. Classify it into
the agent lane, and report it in the `Demoted on the gate`
block with the source that settled it, so a reader can see
both that it was considered and why it did not qualify.

## The six gaps that qualify

1. **Interactive credential.** A login prompt, 2FA, OAuth
   consent, a keychain unlock. Hand back the literal
   command. In Claude Code, tell the operator to run it
   `!`-prefixed so its output lands in the thread.
2. **Physical or GUI-modal.** A device to plug in, an OS
   permission dialog, a restart, a hardware key tap.
3. **Policy-barred outward action.** Where the host states a
   policy, that policy decides, and you quote it. If the
   host authorizes an action it is agent work, no matter how
   outward it feels.

   Where the host states none — most repositories state none
   — fall back to five verbs and no others: publishing,
   sending, deploying, deleting, spending. Anything else is
   agent work. Say which of the two you applied, so the
   operator can see whether they are reading their own rule
   or this default. Never invent a third rule, and never
   carry a classification over from another repository.

4. **Private judgment.** A preference or constraint held
   only in the operator's head — which offer, which framing,
   what to spend.
5. **Access you do not hold.** An account, a paywalled
   source, a machine that is off the network.
6. **Another person's act.** A reply, a review, a signature,
   a meeting.

Nothing else. An item that maps to none of these six is
agent work.

## Dependency pass

Tag every agent-lane item:

- `independent` — runnable right now.
- `blocked-on: <human item>` — name which one.

This is what makes the split actionable. Without it, one
human blocker reads as a stop on everything, and the most
common failure of this analysis is an agent idling on
independent work while it waits for an unrelated answer. The
tags also order the handback: the human item that unblocks
the most agent work goes first.

## Prep pass

For each human item, name the largest agent-addressable
prefix that reduces it to a single action.

| Human item        | Prefix that shrinks it          |
| ----------------- | ------------------------------- |
| Send the email    | Draft it, staged, path named    |
| Authenticate      | One literal command, rest ready |
| Decide between N  | Build the comparison surface    |
| Merge the PR      | CI green, body written          |
| Reply to a person | Draft in their register         |

A human item with no prefix named is under-analyzed. Reduce
every one to a keystroke or a sentence.

A prefix that was already done before this skill ran belongs
in `prepped:`. A prefix that still needs doing is an
agent-lane item like any other, proposed and not performed —
this skill does not execute its own lane in order to shrink
a human item.

## Output contract

Report the table first — it survives scrollback — then the
options.

```text
Agent lane — proposed, not started
1. <item> — <the exact tool call>  [independent]
2. <item> — <the exact tool call>  [blocked-on: H1]

Human lane
H1. <the gap, not the task>
    gap type: <one of the six>
    checked:  <the sources you ran, or n/a and why>
    prepped:  <what is already done>
    unblocks: <which agent items>

Demoted on the gate
- <item> — <the source that settled it>
```

`checked:` is the load-bearing one. A demotion proves itself
— the item arrives in the agent lane with a command attached
and the reader can re-run it. An item that _stays_ in the
human lane rests on an unfalsifiable negative: five checks
that found nothing. Record which sources you actually ran,
and write `n/a` with a reason for any that cannot apply.
Searching the public web for whether the operator will sign
a key is theatre; say so rather than implying you did it.

Then present 1 to 4 options, drawn from both lanes and
ordered by how much each one unblocks. Keep labels short and
free of appraisal: no "(Recommended)", no verdict on which
option is good. When more than four candidates exist, state
the residue count declaratively in the prose above them
rather than dropping it.

Use the operator's next-action picker where the host has
one. Where it does not — Codex has no picker — end with the
same 1 to 4 options as a plain numbered list under a `Next`
heading, one line each, and stop. The options are the
deliverable; the widget is not.

This skill **determines only**. Do not execute the agent
lane as part of running it. The lane is a proposal, and the
operator authorizes it by choosing from the options.

## Turn boundary

Turn-discipline policy generally forbids ending a turn on a
status summary. That does not forbid this skill's output:
the determination is the deliverable the operator asked for,
so ending the turn on it is correct **when the skill was
invoked**.

The converse binds harder. If the human lane comes back
empty, nothing justifies stopping. Report the empty lane in
one line and return to the task you were already doing —
this skill still does not execute its own agent lane, but an
empty human lane is not a reason to hand control back.

Do not reach for this skill to manufacture a stopping point
mid-task. Producing a human lane you did not need is how a
status summary disguises itself as analysis.

## Related skills

None are published yet; they are named so this skill's
boundaries are clear. `ask-human-review` builds a visual
surface for a human item that is a decision. `handoff`
checkpoints the split when a thread is ending.
`interview-me` runs substantive decision rounds, where this
skill's options list is the lightweight menu.
`address-comments` resolves the markers a review leaves
behind.

## Anti-patterns

- **A padded human lane.** Length is not thoroughness. An
  empty human lane is a valid and common result.
- **A human item written as a task.** "Review the resume" is
  a task. "Pick between the two summary lines, both drafted
  at `<path>`" is a gap.

## Host integration

The host's own policy decides gap type 3, and it varies.
Look for:

- The agent instructions file and any standards it links.
- Tracked TODO or task state.
- Push, publish, and review guardrails.
- In-flight branches, open PRs, unresolved review threads.

Worked example. A host `AGENTS.md` authorizes pushing the
operator's own private repositories as ordinary agent work.
A pending private push is therefore **agent lane**, and
asking permission for it violates the policy rather than
respecting it. The same file bars pushing anything public,
so those pushes are **human lane, gap type 3** — and the gap
to write is "authorize the push", never "push the branch".

Quote the policy in the handback. Two hosts can put the same
action in opposite lanes.
