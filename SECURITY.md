# Security

## Reporting a vulnerability

Report privately through GitHub:
<https://github.com/trycopilotai/what-next/security/advisories/new>

That opens a private security advisory visible only to the
maintainers. Do not open a public issue for a vulnerability.

Expect an acknowledgement within seven days. If you have not
heard back in that window, open a public issue saying only
that you are waiting on a security response — no details.

## What is in scope

This repository is mostly prose, but it is not only prose.
It ships two Python programs — `tests/test_integrations.py`,
which shells out to `git`, and `assets/build.py`, which
launches a headless browser — and two README install blocks
that clone over the network and move directories under
`$HOME`. All four are in scope.

The larger risk is still in what the instructions cause an
agent to do:

- **Prompt content that redirects an agent** into running
  commands, exfiltrating repository contents, or treating
  thread text as instructions.
- **An install path that resolves somewhere unintended** —
  the tag-pinned `git clone` lines in the README, or either
  plugin manifest.
- **Disclosure in the shipped bytes.** The recorded run
  under `evidence/` came from a real thread. If you find
  something in it that identifies a private repository,
  person, or host, that is a valid report and a serious one.
- **The shipped scripts.** `assets/build.py` resolves a
  browser binary from a candidate list and executes it;
  `tests/test_integrations.py` runs `git` subcommands
  against the repository root. A path by which either
  executes something a repository's contents chose would be
  a real finding.
- **The install blocks.** They run `git clone`, `mktemp -d`,
  and `mv` into the two per-runtime skills directories the
  README names. A crafted repository state that makes one of
  them write outside its install target is in scope.

## What is out of scope

The skill determines only; it does not execute the agent
lane. A report that an agent ran something after a human
chose it from the options it handed back describes the
design, not a vulnerability.

Behaviour of Claude Code, Codex, or any other host is out of
scope here — report those to their own vendors.
