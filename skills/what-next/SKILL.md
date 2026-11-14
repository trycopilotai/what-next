---
name: what-next
description: >-
  Determine the agent-addressable versus human-required
  actions at this point in a chat thread. Use on "what
  next", "what's left", "what do you need from me", or
  before handing control back: enumerate the open items,
  prove which ones are genuinely blocked on a capability the
  agent lacks, and return a two-lane split plus a short list
  of next actions with consistent `A1` and `H1` identifiers.
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

Do not invoke it internally when no open work exists. For an
explicit invocation with no open work, return both empty
lanes as `None`, then `Next` with no choices, and stop.

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
the agent lane and record the resolving source in its
`Basis` cell, so the reader can see why it did not qualify.

## The six gaps that qualify

1. **Interactive credential.** A login prompt, 2FA, OAuth
   consent, a keychain unlock. Hand back the literal
   command. See **Host adapters** for capturing its output.
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
- `blocked on Hn` — name the human item by ID. If several
  human actions are required, list them:
  `blocked on H1, H2`.

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
every one to a keystroke or a sentence. Preparation already
completed before this invocation belongs in `Prepared`.
Unfinished preparation is a proposed agent item, referenced
by its `A` ID; never describe it as already done.

## Output contract

Use these headings and columns in this order. Render the
tables as Markdown, outside a code fence:

Emit both lanes in an assistant message before invoking a
picker tool. A picker never replaces the tables. Check the
headings, columns, IDs, references, and empty-lane markers
before returning or calling the picker.

### Agent lane — proposed, not started

| ID  | Proposed action   | Next tool/command | State         | Basis                          |
| --- | ----------------- | ----------------- | ------------- | ------------------------------ |
| A1  | <action>          | `<concrete call>` | independent   | <resolving source or evidence> |
| A2  | <action after H1> | `<concrete call>` | blocked on H1 | <missing precondition>         |

### Human lane

| ID  | Needed from you                  | Gap type              | Prepared                                           | Unblocks | Basis                                               |
| --- | -------------------------------- | --------------------- | -------------------------------------------------- | -------- | --------------------------------------------------- |
| H1  | <one action that closes the gap> | <one of the six gaps> | <completed preparation; pending: A1 if applicable> | A2       | <sources checked, result, and policy when relevant> |

Order independent agent items before blocked items. Order
human items by how many agent items they unblock; preserve
thread order for ties. Assign contiguous IDs after ordering:
`A1`, `A2`, and `H1`, `H2`. IDs stay unchanged throughout
this report, including dependencies and choices. A later
report may reclassify work and assign new IDs.

In `Basis`, name evidence that resolves an agent item or the
checks supporting a human gap. For an inapplicable or
unavailable source, say `n/a` and why. A demotion belongs in
the Agent table with its resolving source; no separate
demotion block is needed. Use `None` for a field with no
applicable value. Keep cells concise and escape literal `|`
characters. If a lane is empty, retain its heading and write
`None` instead of an empty table. If both are empty, do not
invent a choice.

`Next tool/command` names an actual host tool with its
target, or a literal shell command. A phrase such as "write
the notes" is not a tool call. Do not invent command
arguments or dependencies; if an argument still needs
discovery, propose that discovery as the next agent action.
`Prepared` describes work that can precede the human act,
never the downstream action it unlocks.

### Next

Present 1 to 4 actionable choices drawn from both lanes,
ordered by how much each unblocks, using the host adapter
below. Only offer independent agent items or human actions
that can be performed now. A blocked agent item stays in the
table until its preconditions hold. Every choice starts with
its ID, such as `A1: Draft the reply` or `H1: Sign in`. Keep
labels short and neutral; omit recommendation badges unless
the host requires them. If additional actionable choices
exist, state
`<N> additional actionable choices are listed above.`
immediately below `Next`, before any picker or plain-list
choices. Never place that count after the choices. All work
remains visible in the tables even when it is absent from
the picker.

When the human lane has at least one `H` item and the report
hands control back to the operator, `Next` is instead one
structured-choice call that asks one question per `H` item,
in the human lane's order. Each question starts with its ID,
such as `H1: Will you sign in now?`, and its options are the
answers to it, so they carry no ID. Agent items are never
options in that call: they stay in the Agent table, and the
operator authorizes one by replying with its ID. The call is
the last thing in the response: both tables, then `Next`,
then the count line when one is needed, then the call, and
nothing after it. **Host adapters** says how to write the
call, what to do when the host caps it, and when the plain
list above replaces it. When the human lane is `None`, use
the adapter as written.

This skill **determines only**. Do not execute the agent
lane as part of running it. The lane is a proposal the
operator authorizes from the picker or in a reply.

## Turn boundary

Turn-discipline policy generally forbids ending a turn on a
status summary. That does not forbid this skill's output:
the determination is the deliverable the operator asked for,
so ending the turn on it is correct **when the skill was
invoked**.

When the operator explicitly asks for this determination,
return it and stop even if the human lane is empty. Do not
execute the proposed lane without the operator's selection.
If the human lane has an `H` item, stopping means ending the
way `Next` describes.

When applying this skill internally before a handoff during
an already-authorized task, an empty human lane does not
justify stopping. Continue that task's independent work.
Human blockers likewise do not suspend unrelated authorized
work. This internal check never expands authorization. The
call waits for an answer, so while independent authorized
work remains, do that work first, then write the report and
make the call when the turn would otherwise end.

Do not reach for this skill to manufacture a stopping point
mid-task. Producing a human lane you did not need is how a
status summary disguises itself as analysis.

## Host adapters

The picker is one call, written the same way on every host.
Call the host's structured-choice tool: `AskUserQuestion` in
Claude Code, `request_user_input` in Codex, and on any other
host whichever exposed tool offers a short single-select
list with a free-text answer. Read that tool's schema first
and obey its limits and label conventions. Never name a tool
the host does not expose, and do not switch modes merely to
obtain one.

When the human lane has an `H` item, send one question per
`H` item, in the human lane's order. Write each question as
a full sentence that starts with the ID and ends in `?`,
such as `H1: Should the service move to the new region?`.
Its header is the ID, such as `H1`, and it is single select.
Its 2 to 4 options are the concrete answers to that
question. Each label is a short answer, such as `Move it` or
`Keep it here`; each description is one line saying what
that answer means or what The Agent will do next. If one
call takes fewer questions than there are `H` items, ask the
first ones in order and state
`<N> additional human items are listed above.` immediately
below `Next`, before the call, counting the `H` items not
asked. Claude Code allows 1 to 4 questions per call and 2 to
4 options per question; on any other host, read both limits
from its tool's schema. A tool that takes one question per
call asks `H1` alone under the same rule.

When an `H` item has only one natural answer, such as
running a login command, offer `Done` and then `Not now`, so
the question meets the two-option minimum. `Not now`
authorizes nothing and is the only padding allowed. Never
add it to a plain list.

Name who acts as **The Agent** or **The Human** in every
question, option label and description, never with "I",
"you", "me", "we" or "your". A picker is read apart from the
prose around it, and a pronoun's referent flips with the
reader, so `You merge them` and `I'll merge, ping me` leave
it unclear who does what. Write `The Agent merges them` and
`The Human merges; The Agent pings`, and ask
`H1: Should The Agent merge the pull request?`, not
`H1: Should I merge the pull request?`. A plain list follows
the same rule.

When the human lane is `None`, send one question with the
header `Next`, single select, and one option per choice.
Each label is the choice's ID and a short action, such as
`A1: Run the tests`. Each description is one line saying
what picking the option authorizes. Keep the `Next` order.
If the host allows fewer options than there are choices,
offer the first ones in order and make the
additional-choices count the number of actionable choices
not offered.

Use a plain list under `Next`, with one ID-labelled option
per line, instead of the call when the host exposes no
structured-choice tool, the mode forbids it, the run is
noninteractive, the tool cannot represent the questions or
choices faithfully, or the host cannot show the full lane
report before the call. Use a plain list too when the human
lane is `None` and only one actionable choice exists. The
list carries the choices that open `Next`, from both lanes,
without `Not now`. A selected choice, or a reply naming an
ID, authorizes only that choice and its necessary
preparation; an answer authorizes only what its description
says The Agent will do. Tool approval rules still apply.

For an interactive login, give the literal command. In
Claude Code, suggest its `!`-prefixed form when shell
capture is supported; elsewhere ask the operator to run it
in their terminal and report the result. Never ask for
secrets.

Host policy and current permissions take precedence over
this skill. A tool's existence alone does not authorize an
action; its preconditions include scope, permissions, and
the operator's existing authorization.

## Related skills

`handoff` and `address-comments` are published;
`ask-human-review` and `interview-me` are not yet. All four
are named so this skill's boundaries are clear.
`ask-human-review` builds a visual surface for a human item
that is a decision. `handoff` checkpoints the split when a
thread is ending. `interview-me` runs substantive decision
rounds, where this skill's options list is the lightweight
menu. `address-comments` resolves the markers a review
leaves behind.

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
