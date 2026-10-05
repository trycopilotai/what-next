"""Packaging contract for the what-next skill repository.

The repository ships no product code — this suite and
`assets/build.py` are the only programs. What can break is
the packaging: the symlink orientation both runtimes rely on, the
two plugin manifests agreeing with each other, and the Codex
interface strings agreeing across the manifest and the agent
file. Each test below watches one of those.

Runs offline with no third-party packages.
"""

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "what-next"

PROVENANCE_INFIXES = (".gpt.", ".claude.", ".codex.")

# Spelled out because the README spells them out.
NUMBERS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}

SHARED_MANIFEST_FIELDS = (
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "skills",
)


def require_own_repository():
    """git resolves to the nearest enclosing repository.

    Unpacked inside another checkout, `git ls-files` would list
    that repository's files and the provenance tests would pass
    having audited the wrong tree entirely.
    """
    top = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if Path(top).resolve() != ROOT.resolve():
        raise AssertionError(
            f"git resolves to {top}, not {ROOT}. Run the suite from a "
            "clone of this repository, not from an unpacked archive."
        )


def tracked_paths():
    require_own_repository()
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def load(path):
    return json.loads((ROOT / path).read_text())


def human_lane_block(transcript):
    """Just the Human lane section of a recorded run.

    Every guard below scopes to it. Counting `H<n>.` or
    `checked:` anywhere in the file lets a line of editorial
    prose outside the lane stand in for a run item, which is
    how a claim about the run can be made true by writing
    something that is not part of the run.
    """
    import re

    # Fails closed. Returning "" on a missing heading, or
    # taking the first of several, let a renamed or duplicated
    # heading switch off the guards that scope to this block
    # while every test stayed green.
    opens = re.findall(r"^Human lane\s*$", transcript, re.M)
    # Anchored past the word: `Demoted on the gateway` matched
    # a bare prefix and stood in for the real heading.
    closes = re.findall(r"^Demoted on the gate\b", transcript, re.M)
    if len(opens) != 1 or len(closes) != 1:
        raise AssertionError(
            f"transcript has {len(opens)} 'Human lane' and "
            f"{len(closes)} 'Demoted on the gate' headings; "
            "expected exactly one of each"
        )
    after = transcript.split("Human lane", 1)[1]
    return re.split(r"^Demoted on the gate\b", after, flags=re.M)[0]


def demotion_block(transcript):
    """The `Demoted on the gate` section, and only it.

    Bounded at both ends. Splitting on the heading and taking
    everything to the end of the file let an appended decoy
    section supply the bullets these tests inspect, while the
    real ones were stripped. The section ends at the first
    line that is neither blank, nor indented, nor a bullet --
    in this record, the sentence that orders the human items.
    """
    import re

    parts = re.split(r"^Demoted on the gate\b", transcript, flags=re.M)
    if len(parts) != 2:
        raise AssertionError(
            f"expected exactly one 'Demoted on the gate' heading, "
            f"found {len(parts) - 1}"
        )
    lines, kept = parts[1].splitlines(), []
    for line in lines[1:]:
        if line.strip() and not line.startswith((" ", "-")):
            break
        kept.append(line)
    return "\n".join(kept)


def transcript_has_checked_field(transcript):
    """True only if a human-lane item actually carries the field.

    Matching the bare string is wrong twice over: the header's
    disclosure prose names `checked:` while explaining its
    absence, and an indented line anywhere else in the file
    would satisfy an unscoped search.
    """
    import re

    return bool(
        re.search(r"^\s+checked:", human_lane_block(transcript), re.M)
    )


def parse_agent_interface(text):
    """Minimal reader for the one shape openai.yaml has.

    Stdlib only: `interface:` followed by `key: value` pairs
    whose value may sit on the next line and wrap across
    several. Returns whitespace-collapsed strings keyed by
    field, so a test can compare per key instead of searching
    the file for a value anywhere in it -- which is what let a
    swapped pair pass.
    """
    import re

    lines = text.splitlines()
    starts = [
        i
        for i, line in enumerate(lines)
        # Not an exact-line match: `interface: # replacement`
        # introduced a second mapping the uniqueness check
        # below never saw.
        if re.match(r"^interface:\s*(#.*)?$", line)
    ]
    # Reading the first and ignoring the rest let a second
    # mapping carry different values while this test passed on
    # the first. A duplicate key is invalid YAML anyway.
    if len(starts) != 1:
        raise AssertionError(
            f"{len(starts)} top-level `interface:` mappings; expected 1"
        )
    start = starts[0]
    fields, key, buffer = {}, None, []
    for line in lines[start + 1 :]:
        if not line.strip():
            continue
        if not line.startswith("  "):
            break
        match = re.match(r"^  (\w+):(.*)$", line)
        if match:
            if key:
                fields[key] = _collapse(buffer)
            key, buffer = match.group(1), [match.group(2)]
        else:
            buffer.append(line)
    if key:
        fields[key] = _collapse(buffer)
    return fields


def _collapse(parts):
    value = " ".join(" ".join(parts).split())
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def transcript_has_options_list(transcript):
    """True only if the record carries a closing options list.

    Same shape as the `checked:` guard: the contract gained
    the list after the run, so its absence is expected and
    must be declared rather than back-filled.
    """
    return "\nNext\n" in transcript


class TestFilenames(unittest.TestCase):
    def test_no_agent_provenance_infix_in_any_tracked_path(self):
        """Agent-authored drafts are sometimes marked with
        .gpt./.claude./.codex. infixes. Those are interior
        provenance and must never reach a published path."""
        offenders = [
            p
            for p in tracked_paths()
            if any(infix in Path(p).name for infix in PROVENANCE_INFIXES)
        ]
        self.assertEqual([], offenders)

    def test_repository_tracks_files(self):
        self.assertTrue(tracked_paths(), "git ls-files returned nothing")

    def test_no_provenance_infix_in_any_historical_path(self):
        """The current tree is the easy half. A path that
        existed in an earlier commit is published too, and
        `git ls-files` cannot see it."""
        require_own_repository()
        out = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "log",
                "--all",
                "--pretty=format:",
                "--name-only",
                "--diff-filter=A",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        historical = {line for line in out.splitlines() if line}
        offenders = [
            p
            for p in historical
            if any(infix in Path(p).name for infix in PROVENANCE_INFIXES)
        ]
        self.assertEqual([], offenders)
        self.assertTrue(historical, "no historical paths found")


class TestSkillPackage(unittest.TestCase):
    def setUp(self):
        self.package = ROOT / "skills" / NAME
        self.skill = self.package / "SKILL.md"
        self.interface = self.package / "agents" / "openai.yaml"
        self.compat = ROOT / "skill"

    def test_canonical_package_is_a_real_directory(self):
        self.assertTrue(self.package.is_dir())
        self.assertFalse(self.package.is_symlink())

    def test_canonical_files_are_real_files(self):
        for path in (self.skill, self.interface):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())

    def test_compatibility_path_is_a_symlink_into_the_package(self):
        """Both runtimes load skills/<name>/. The top-level
        `skill` symlink is the compatibility path the README
        and both install scripts copy from. Reversing the
        orientation duplicates the skill content."""
        self.assertTrue(self.compat.is_symlink())
        self.assertEqual(Path(f"skills/{NAME}"), self.compat.readlink())
        self.assertEqual(self.package.resolve(), self.compat.resolve())

    def test_frontmatter_carries_name_and_description_only(self):
        lines = self.skill.read_text().splitlines()
        self.assertEqual("---", lines[0])
        end = lines.index("---", 1)
        keys = [
            line.split(":", 1)[0]
            for line in lines[1:end]
            if line and not line[0].isspace()
        ]
        self.assertEqual(["name", "description"], keys)

    def test_frontmatter_name_matches_the_directory(self):
        """Scoped to the frontmatter block. Searching the whole
        file let a body mention satisfy it."""
        lines = self.skill.read_text().splitlines()
        frontmatter = lines[1 : lines.index("---", 1)]
        self.assertIn(f"name: {NAME}", frontmatter)

    def test_skill_stays_under_five_hundred_lines(self):
        self.assertLess(len(self.skill.read_text().splitlines()), 500)


class TestPluginManifests(unittest.TestCase):
    def setUp(self):
        self.claude = load(".claude-plugin/plugin.json")
        self.codex = load(".codex-plugin/plugin.json")

    def test_shared_fields_are_identical(self):
        for field in SHARED_MANIFEST_FIELDS:
            with self.subTest(field=field):
                self.assertEqual(self.claude[field], self.codex[field])

    def test_name_matches_the_skill_directory(self):
        self.assertEqual(NAME, self.claude["name"])

    def test_skills_points_at_the_package_root(self):
        self.assertEqual("./skills/", self.codex["skills"])

    def test_codex_manifest_carries_an_interface(self):
        self.assertIn("interface", self.codex)

    def test_agent_interface_agrees_with_the_codex_manifest(self):
        """openai.yaml and the Codex manifest describe the same
        surface to the same runtime. Drift between them is
        invisible until a user sees two different labels.

        Compared key by key. The earlier spelling asserted that
        each manifest value appeared somewhere in the file, so
        swapping short_description and default_prompt would
        have passed while the property it names was false."""
        fields = parse_agent_interface(
            (ROOT / "skills" / NAME / "agents" / "openai.yaml").read_text()
        )
        interface = self.codex["interface"]
        for key, expected in (
            ("display_name", interface["displayName"]),
            ("short_description", interface["shortDescription"]),
            ("default_prompt", interface["defaultPrompt"][0]),
        ):
            with self.subTest(key=key):
                self.assertIn(key, fields)
                self.assertEqual(" ".join(expected.split()), fields[key])

    def test_store_copy_never_promises_a_picker(self):
        """Picker availability depends on host and mode.
        Store copy cannot qualify the claim in the
        space it has, so it must not make it — the Codex
        longDescription promised one and no test caught it."""
        for name in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
            with self.subTest(surface=name):
                self.assertNotIn("picker", (ROOT / name).read_text().lower())

    def test_prose_mentions_a_picker_only_with_its_fallback(self):
        """Longer prose may name the picker, but only alongside
        the text fallback."""
        for name in ("README.md", "SECURITY.md"):
            text = (ROOT / name).read_text().lower()
            with self.subTest(surface=name):
                if "picker" in text:
                    self.assertIn("plain list", text)


class TestLaunchSurface(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / "README.md").read_text()
        self.version = load(".claude-plugin/plugin.json")["version"]

    def test_readme_pins_both_installs_to_the_manifest_version(self):
        """Each product install carries its own `release=` pin.

        Counted per block. The earlier spelling counted two
        occurrences anywhere in the file, which both landing in
        one block would have passed while the other install
        cloned whatever `$release` happened to hold."""
        import re

        blocks = [
            block
            for block in re.findall(
                r"```(?:sh|text)\n(.*?)```", self.readme, re.S
            )
            if "git clone" in block
        ]
        self.assertEqual(2, len(blocks))
        for index, block in enumerate(blocks):
            with self.subTest(block=index):
                # Every assignment, not just the presence of the
                # right one: a later `release=main` in the same
                # block is what the clone would actually use.
                assignments = re.findall(r"^\s*release=(\S+)", block, re.M)
                self.assertEqual([f"v{self.version}"], assignments)

    def test_readme_never_pins_the_install_to_a_branch(self):
        """Every --branch must resolve to the shipped tag, either
        literally or through the `release` variable each block
        sets. --branch develop passed the old spelling."""
        import re

        refs = re.findall(r"--branch (\S+)", self.readme)
        self.assertTrue(refs, "no --branch found in the README")
        allowed = {f"v{self.version}", '"$release"', "$release"}
        for ref in refs:
            with self.subTest(ref=ref):
                self.assertIn(ref, allowed)

    def test_readme_presents_each_invocation_form(self):
        """`/what-next` is a substring of the repository URL,
        which appears four times, so a bare assertIn could not
        fail. Each form is anchored in backticks instead."""
        for form in (
            f"`/{NAME}`",
            f"`/{NAME}:{NAME}`",
            f"`${NAME}`",
            f"`${NAME}:{NAME}`",
        ):
            with self.subTest(form=form):
                self.assertIn(form, self.readme)

    def test_readme_never_offers_the_chatgpt_selector_for_codex(self):
        """Codex selects skills with `$`; `@` is the ChatGPT
        form. The README offered `@what-next` as the Codex
        marketplace invocation, which does not work, and the
        old forms test asserted its presence."""
        self.assertNotIn(f"`@{NAME}`", self.readme)

    def test_readme_names_both_runtime_install_roots(self):
        for root in ("$HOME/.claude/skills", "$HOME/.agents/skills"):
            with self.subTest(root=root):
                self.assertIn(root, self.readme)

    def test_security_policy_names_this_repositorys_reporting_path(self):
        """The old spelling matched any advisories URL, including
        one pointing at somebody else's repository."""
        security = (ROOT / "SECURITY.md").read_text()
        repository = load(".claude-plugin/plugin.json")["repository"]
        self.assertIn(f"{repository}/security/advisories/new", security)

    def test_social_preview_is_1280_by_640(self):
        """GitHub renders the social card at 1280x640. A
        wrong-sized asset is cropped silently."""
        import zlib

        png = ROOT / "assets" / "social-preview.png"
        self.assertTrue(png.is_file())
        data = png.read_bytes()
        header = data[:24]
        self.assertEqual(b"\x89PNG\r\n\x1a\n", header[:8])
        width = int.from_bytes(header[16:20], "big")
        height = int.from_bytes(header[20:24], "big")
        self.assertEqual((1280, 640), (width, height))
        # A crafted 24-byte header carries any dimensions you
        # like. Walk the chunks and decompress the image data,
        # so the file has to be a real render rather than a
        # plausible prefix. Scanning for the bytes `IDAT`
        # instead would also match inside compressed data.
        chunks, offset = [], 8
        while offset + 8 <= len(data):
            length = int.from_bytes(data[offset : offset + 4], "big")
            kind = data[offset + 4 : offset + 8]
            start = offset + 8
            chunks.append((kind, data[start : start + length]))
            offset = start + length + 4
        self.assertEqual(b"IEND", chunks[-1][0])
        idat = b"".join(body for kind, body in chunks if kind == b"IDAT")
        self.assertTrue(idat, "no IDAT chunk")
        rows = zlib.decompress(idat)
        # Each row is one filter byte plus `width` samples of
        # however many channels the colour type carries.
        self.assertEqual(0, len(rows) % height)
        stride = len(rows) // height
        self.assertEqual(0, (stride - 1) % width)


class TestEvidence(unittest.TestCase):
    def setUp(self):
        self.manifest = load("evidence/manifest.json")

    def test_manifest_hashes_match_the_files_it_names(self):
        """The manifest is the only thing tying the README's
        claim to the recorded run. If it can drift from the
        bytes, it proves nothing."""
        import hashlib

        for record in (
            self.manifest["protocol"],
            self.manifest["interface"],
            self.manifest["result"],
        ):
            with self.subTest(path=record["path"]):
                data = (ROOT / record["path"]).read_bytes()
                self.assertEqual(
                    record["sha256"], hashlib.sha256(data).hexdigest()
                )

    def test_manifest_declares_the_transcript_edited_and_says_how(self):
        """The transcript WAS redacted before publication. An
        earlier version of this test asserted `edited` was
        false, which made CI enforce an untrue claim about the
        repository's only piece of evidence. If the record is
        edited, the manifest must say so and say what changed."""
        result = self.manifest["result"]
        self.assertIs(True, result["edited"])
        redactions = result["redactions"]
        for field in (
            "identifiers",
            "rewording",
            "reverted",
            "preserved",
            "why",
        ):
            with self.subTest(field=field):
                self.assertTrue(redactions[field].strip())

    def test_manifest_revision_list_covers_the_contract_gap(self):
        """The transcript lacks `checked:` and an options list
        because it predates both rules. If the revision note
        does not name them, it reads complete while omitting
        exactly what explains the discrepancy.

        Both halves are asserted. The earlier spelling checked
        only `checked:`, so a note that dropped the options-list
        revision passed while this docstring claimed it could
        not."""
        note = self.manifest["protocol"]["note"]
        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        # Conditioned on the transcript alone. Keying either
        # branch off a word in SKILL.md let a rename there
        # ("options" -> "choices") silently switch the
        # assertion off while the omission remained.
        if not transcript_has_checked_field(transcript):
            self.assertIn("`checked:`", note)
        if not transcript_has_options_list(transcript):
            self.assertIn("options list", note)

    def test_transcript_contains_no_composed_options_list(self):
        """One was written during review to make the record
        satisfy a contract it predates, which made the
        'nothing was added' claim false. The run produced no
        options list and this record must not grow one."""
        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        self.assertNotIn("\nNext\n", transcript)
        self.assertIn("capture", self.manifest)
        self.assertIn("method", self.manifest["capture"])

    def test_protocol_pin_does_not_claim_to_have_produced_the_run(self):
        """The protocol hash tracks the shipped SKILL.md, which
        has been revised since the run. Without this the pin
        silently re-attributes an old transcript to whatever
        the protocol says today — a stamp that re-inks itself."""
        protocol = self.manifest["protocol"]
        self.assertIs(False, protocol["current_at_capture"])
        self.assertIn("never as", protocol["note"])

    def test_transcript_declares_it_predates_contract_changes(self):
        """The contract gained a `checked:` field after this run.
        Back-filling it would invent what the run did; the
        honest alternative is saying so, and this fails if that
        disclosure is dropped while the mismatch remains."""
        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        if not transcript_has_checked_field(transcript):
            self.assertIn("Contract", transcript)
            self.assertIn("output contract has gained", transcript)

    def test_transcript_itself_declares_the_redaction(self):
        """A reader who opens the transcript directly must see
        it too, not only a reader who opens the manifest."""
        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        self.assertIn("Redacted", transcript)
        self.assertIn("IS edited", transcript)

    def test_readme_claim_arithmetic_holds_in_the_transcript(self):
        """The README says two of six human items were demoted.
        Count both numbers out of the transcript rather than
        trusting the sentence: this is the one claim the
        repository makes about its own evidence."""
        import re

        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        kept = len(
            re.findall(r"^H\d+\.", human_lane_block(transcript), re.M)
        )
        block = demotion_block(transcript)
        demoted = len(re.findall(r'^- "', block, re.M))
        readme = " ".join((ROOT / "README.md").read_text().split())

        total = kept + demoted
        self.assertIn(demoted, NUMBERS, f"unmapped demotion count {demoted}")
        self.assertIn(total, NUMBERS, f"unmapped item total {total}")
        self.assertIn(
            f"{NUMBERS[demoted]} of {NUMBERS[total]} human items "
            "were demoted",
            readme,
        )

    def test_every_demotion_names_the_source_that_settled_it(self):
        """The transcript heading promises "with the source that
        resolved each", and the README repeats it. Counting
        demotions does not check it: a bullet stripped of its
        explanation still counts. Each one must carry a reason
        after the em dash."""
        import re

        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        block = demotion_block(transcript)
        bullets = re.findall(
            r'^- ".*?"(.*?)(?=^- "|\Z)', block, re.M | re.S
        )
        # Every bullet in the section must be a quoted, sourced
        # demotion -- an unquoted one would otherwise vanish
        # from both this test and the arithmetic count.
        self.assertEqual(
            len(re.findall(r"^- ", block, re.M)), len(bullets)
        )
        self.assertTrue(bullets, "no demotion bullets found")
        for index, body in enumerate(bullets):
            with self.subTest(demotion=index):
                self.assertIn("—", body)
                reason = body.split("—", 1)[1]
                self.assertGreater(len(reason.split()), 3, reason)

    def test_readme_discloses_the_run_is_not_independent(self):
        """The evidence rests on one run by the same agent that
        built this repository. That disclosure is the reason a
        single run is honest to publish at all, so it must not
        be quietly dropped, and nothing may claim the
        opposite."""
        readme = (ROOT / "README.md").read_text()
        self.assertIn("not independent", readme)
        self.assertIn("the same agent that was building", readme)
        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        for text, name in ((readme, "README.md"), (transcript, "transcript")):
            with self.subTest(surface=name):
                self.assertNotIn("independent run of", text)
                self.assertNotIn("independently verified", text)

    def test_readme_claim_markers_are_present_in_the_transcript(self):
        transcript = (ROOT / self.manifest["result"]["path"]).read_text()
        for marker in (
            "Demoted on the gate",
            "gap type:",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, transcript)


class TestSocialPreviewContrast(unittest.TestCase):
    """The card is the first thing most readers see, and a
    low-contrast one is unreadable rather than merely ugly.

    Colours are parsed from the HTML source. What ships is the
    PNG, so on its own that would check the wrong artifact —
    `assets/social-preview.sha256` records the hash of both
    files as of the render, and the first test below refuses
    to let either drift from it afterwards.

    That is a weaker guarantee than it sounds, and worth
    stating plainly: nothing here proves the PNG was rendered
    from the HTML. Proving that needs a browser, and this
    suite runs offline with no third-party packages.
    `assets/build.py` is the only thing that writes either the
    PNG or the stamp, so the binding rests on that script
    having produced both."""

    def test_committed_assets_match_their_recorded_hashes(self):
        """Both files are bound, in `shasum -a 256` format.

        Stamping only the HTML bound the PNG to nothing: any
        other valid 1280x640 image passed this test, the
        dimension test and the contrast tests together, while
        the card a reader sees was never checked at all.

        Named for what it checks. The earlier name said the
        PNG "was rendered from the current source", which no
        offline assertion can establish -- see the class
        docstring."""
        import hashlib

        recorded = dict(
            reversed(line.split())
            for line in (ROOT / "assets" / "social-preview.sha256")
            .read_text()
            .splitlines()
            if line.strip()
        )
        self.assertEqual(
            {"social-preview.html", "social-preview.png"},
            set(recorded),
        )
        for name, expected in recorded.items():
            with self.subTest(asset=name):
                actual = hashlib.sha256(
                    (ROOT / "assets" / name).read_bytes()
                ).hexdigest()
                self.assertEqual(expected, actual)

    def setUp(self):
        import re

        css = (ROOT / "assets" / "social-preview.html").read_text()
        self.tokens = dict(
            re.findall(r"--([a-z]+):\s*(#[0-9a-fA-F]{6})", css)
        )

    @staticmethod
    def _ratio(fg, bg):
        def lum(value):
            value = value.lstrip("#")
            parts = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
            parts = [
                v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
                for v in parts
            ]
            return (
                0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]
            )

        high, low = max(lum(fg), lum(bg)), min(lum(fg), lum(bg))
        return (high + 0.05) / (low + 0.05)

    def test_every_foreground_clears_wcag_aa_on_the_background(self):
        background = self.tokens["bg"]
        for name in ("fg", "muted", "agent", "human"):
            with self.subTest(token=name):
                ratio = self._ratio(self.tokens[name], background)
                # Compared unrounded. Rounding to 2dp first let
                # 4.4955:1 pass a 4.5:1 gate.
                self.assertGreaterEqual(
                    ratio,
                    4.5,
                    f"--{name} on --bg is {ratio:.4f}:1",
                )


if __name__ == "__main__":
    unittest.main()
