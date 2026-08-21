# what-next

Ask an agent what is left and you usually get a list padded
with questions it could have answered itself. what-next
makes an item earn the human lane: five sources must fail to
resolve it first, and it must then map to one of exactly six
capability gaps.

In the recorded run, two of six human items were demoted.

Each demotion names the source that settled it, and the run
is in [`evidence/`](evidence/) — one run, on this project's
own release thread, so a demonstration rather than a
benchmark.

It writes the gap, not the task. "Deploy the service" is
never the human action; "run `gcloud auth login`" is.

It determines only. Running it does not execute the agent
lane — that lane is a proposal you authorize.

## What it returns

A two-lane table, then one to four next actions — through
the host's picker where there is one, as a plain list where
there is not.

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

Every agent item is tagged `independent` or
`blocked-on: <human item>`. Without those tags one human
blocker reads as a stop on everything, which is the most
common way this analysis goes wrong.

## The six gaps

An item reaches the human lane only by mapping to one of
these. Nothing else qualifies.

1. **Interactive credential** — a login prompt, 2FA, OAuth
   consent, a keychain unlock.
2. **Physical or GUI-modal** — a device to plug in, an OS
   permission dialog, a restart, a hardware key tap.
3. **Policy-barred outward action** — the host's policy
   where it states one; otherwise five verbs and no others:
   publishing, sending, deploying, deleting, spending.
4. **Private judgment** — a preference held only in your
   head.
5. **Access you do not hold** — an account, a paywalled
   source, a machine off the network.
6. **Another person's act** — a reply, a review, a
   signature, a meeting.

Unfamiliarity, effort, reassurance, re-confirmation, and any
question a test or a `grep` would settle are explicitly not
gaps.

## Use it

### Claude Code

Save this as `install.sh` and run it. It sets `set -eu` and
an `EXIT` trap, so pasting it straight into an interactive
shell will end that shell if the clone fails.

```sh
set -eu
release=v0.1.4
install_parent="$HOME/.claude/skills"
install_target="$install_parent/what-next"
mkdir -p "$install_parent"
install_tmp="$(mktemp -d "$install_parent/.what-next.XXXXXX")"
install_stage="$install_tmp/package"
rollback_install() {
  if [ ! -e "$install_target" ]; then
    if [ -e "$install_tmp/previous" ]; then
      mv "$install_tmp/previous" "$install_target"
    fi
  fi
  rm -rf "$install_tmp"
}
trap rollback_install EXIT
git clone --quiet --depth 1 --branch "$release" \
  https://github.com/trycopilotai/what-next \
  "$install_tmp/what-next"
mkdir -p "$install_stage"
cp -R "$install_tmp/what-next/skill/." "$install_stage/"
if [ -e "$install_target" ]; then
  mv "$install_target" "$install_tmp/previous"
fi
mv "$install_stage" "$install_target"
trap - EXIT
rm -rf "$install_tmp"
```

Or, **once the marketplace listing is live**, alongside the
other
[trycopilot.ai skills](https://github.com/trycopilotai/skills):

```text
/plugin marketplace add trycopilotai/skills
/plugin install what-next@trycopilotai
```

Invoke the directly installed skill as `/what-next`, or the
marketplace plugin as `/what-next:what-next`.

### Codex

Save this one the same way. The only line that differs from
the block above is `install_parent`.

```sh
set -eu
release=v0.1.4
install_parent="$HOME/.agents/skills"
install_target="$install_parent/what-next"
mkdir -p "$install_parent"
install_tmp="$(mktemp -d "$install_parent/.what-next.XXXXXX")"
install_stage="$install_tmp/package"
rollback_install() {
  if [ ! -e "$install_target" ]; then
    if [ -e "$install_tmp/previous" ]; then
      mv "$install_tmp/previous" "$install_target"
    fi
  fi
  rm -rf "$install_tmp"
}
trap rollback_install EXIT
git clone --quiet --depth 1 --branch "$release" \
  https://github.com/trycopilotai/what-next \
  "$install_tmp/what-next"
mkdir -p "$install_stage"
cp -R "$install_tmp/what-next/skill/." "$install_stage/"
if [ -e "$install_target" ]; then
  mv "$install_target" "$install_tmp/previous"
fi
mv "$install_stage" "$install_target"
trap - EXIT
rm -rf "$install_tmp"
```

Or, once the listing is live, from the marketplace:

```sh
npx -y @openai/codex plugin marketplace add \
  trycopilotai/skills
npx -y @openai/codex plugin add what-next@trycopilotai
```

Invoke the directly installed skill as `$what-next`, or the
marketplace plugin as `$what-next:what-next`. Codex selects
skills with `$`; `@` is the ChatGPT form and is not a Codex
selector.

The four forms are two pairs. A skill you cloned yourself is
addressed by its own name — `/what-next` in Claude Code,
`$what-next` in Codex. A skill installed from a marketplace
is namespaced by the plugin it arrived in, so it takes the
longer form: `/what-next:what-next` and
`$what-next:what-next`. If one is not recognised, it is the
form for the install you did not do. Do not go looking in
`codex plugin list` for it: that lists plugins, not the
selectors their skills answer to.

The `v0.1.4` tagged repository carries Claude Code and Codex
plugin manifests. Both runtimes load the canonical package
under `skills/what-next`; `skill/SKILL.md` resolves to that
package, so the skill content is stored once.

The clone is pinned to a tag rather than to `main`. This
file is an instruction set that steers an agent, so a
mutable branch would silently change what it is told to do.
Read
[`skills/what-next/SKILL.md`](skills/what-next/SKILL.md)
before you invoke it. (`skill/` is a symlink to that
directory, which GitHub's web view will not follow.)

Whether you need to restart depends on the runtime and on
the install route, so all four cases are spelled out.

Claude Code picks up a directly installed skill in the
current session; restart only if the top-level skills
directory did not exist when the session started. For a
plugin it reports either `Plugin is now active.` or
`Run /reload-plugins to activate.` — do whichever it says.

Codex detects a directly installed skill automatically, with
no directory rule, and picks up a plugin-bundled skill in a
session started after the install. If a skill does not
appear, restart Codex.

## When to use it

- You asked "what next", "what's left", "what do you need
  from me", or "what can you do without me".
- A thread has accumulated open commitments and it is no
  longer obvious what is blocked.
- A plan finished and the residue needs routing.

Do not run it on a thread with no open work.

## Evidence

`evidence/transcripts/2026-08-20-release-thread.txt` is a
real run, captured mid-task while this repository was being
prepared for publication. `evidence/manifest.json` records
the skill's SHA-256, the agent and version, the invocation,
and the output hash.

**The protocol has moved since the run.** The output
contract has gained three rules since the recorded run. It
falls short of two of them — it carries no `checked:` field
and ends without an options list. The third, a
`Demoted on the gate` block, the run already satisfies.
Those fields were not back-filled — writing them now would
be inventing what the run did, which is the one thing this
repository argues against. `evidence/manifest.json` lists
every revision, and the transcript's header says which rules
it predates.

**The record is edited, and says so.** The run happened on a
private thread, so before publication a signing key's path,
two script names, and one configuration key were replaced
with prose naming the same things generically. No item was
added or removed and no classification was changed — every
lane, tag, gap type and demotion is as the run produced it.
Two smaller edits are recorded alongside it: the sentences
framing the item counts were reworded, and an options list
composed during review was removed again as improper.
`evidence/manifest.json` carries `"edited": true` with all
three, and a test fails the build if that declaration goes
missing.

**Not measured, stated up front.** There is no benchmark, no
accuracy figure, and no animated demo. One recorded run is
the whole evidence base. That run is not independent: the
protocol was applied to this project's own release thread by
the same agent that was building the repository, so it is a
demonstration that the gate fires, not evidence that the
split generalises to other threads or other agents. An
independent run is the most useful thing a contributor could
add.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The most useful
report is a run where the split was wrong, or a
human-required item that maps to none of the six gaps.

## License

MIT. See [`LICENSE`](LICENSE).

## Not affiliated with GitHub or GitHub Copilot

The `trycopilotai` organisation name is not a claim of any
relationship with GitHub Copilot. This project is not
affiliated with, endorsed by, or sponsored by GitHub, Inc.
GitHub and GitHub Copilot are trademarks of GitHub, Inc.
