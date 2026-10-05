# Contributing

This repository contains one canonical skill, documentation,
a historical record, and synthetic client runs. The only
code is the test suite and the asset builder — no product
code — and the suite asserts on README prose. Read that part
before you edit anything.

## Run the checks first

```sh
make check
```

That is unittest discovery under `tests/`, and CI runs it on
every pull request across Python 3.11 and 3.13. It needs
`python3` and `git`, and it needs a real clone — several
assertions read `git ls-files` and `git log --all`, so a
source ZIP with no history fails with a `CalledProcessError`
rather than a useful message.

**It asserts on the README.** Two tests in particular will
fail on an innocent-looking prose edit:

- `test_readme_claim_arithmetic_holds_in_the_transcript`
  counts the human items and demotions in the recorded run
  and requires the README sentence to match them. Change the
  sentence without changing the run and the suite goes red —
  by design, because that sentence is the only thing this
  repository counts about its own evidence. Its other
  evidence claims are qualitative and are asserted
  separately, one test each:
  `test_readme_discloses_the_run_is_not_independent`,
  `test_manifest_declares_the_transcript_edited_and_says_how`,
  and
  `test_every_demotion_names_the_source_that_settled_it`.
- `test_readme_pins_both_installs_to_the_manifest_version`
  requires each of the two install blocks to carry its own
  `release=` pin, at the tag the plugin manifests ship. It
  counts per block, so a second pin in the same block does
  not cover an unpinned one.

If you change either, change the thing it describes too.

Markdown formatting is checked separately by
[`trycopilotai/lint`](https://github.com/trycopilotai/lint),
pinned in `.github/workflows/lint.yml`. Prose wraps at 60
columns. To run it locally:

```sh
git clone --depth 1 --branch v0.1.7 \
  https://github.com/trycopilotai/lint /tmp/lint
python3 /tmp/lint/lint.py --cwd . --language markdown --read-only
```

## What is most useful

Open an issue for any of these.

- **A run where the split was wrong.** The gate putting
  something in the human lane that an agent could have
  settled, or the reverse. Paste the thread's open items and
  what the skill returned.
- **An independent run.** The historical recorded run is the
  skill applied to this repository's own release thread by
  the agent that built it. A run on an ordinary bug-fix or
  review thread, by anyone else, is the single most valuable
  thing this repository can receive.
- **A seventh gap.** The list of six is deliberately closed.
  If you hit something genuinely human-required that maps to
  none of them, that is the most interesting bug report
  here. Give the item, why no gap fits, and what you would
  add.

## Pull requests

Yes, they are welcome, including prose-only changes to
`skills/what-next/SKILL.md`. That file is the product, so a
change to it is the most substantial contribution possible
here.

The bar is whether the change makes a determination sharper,
and the way to show that is a before-and-after on the same
input: the thread's open items, what the skill returned
before, and what it returns after. "This wording reads
better" is not reviewable. "This wording is what stopped the
gate being skipped" is.

## House rules

Keep `skills/what-next/SKILL.md` under 500 lines — the suite
enforces it. Frontmatter carries `name` and `description`
and nothing else.

The top-level `skill` is a symlink to `skills/what-next/`.
Do not reverse that orientation; the canonical directory is
`skills/what-next/`, and both install scripts copy through
the symlink.

Commit with your own identity and no AI co-author trailer.

## Scope

The skill determines only. A change that makes it execute
the agent lane is out of scope by design, not by oversight.
