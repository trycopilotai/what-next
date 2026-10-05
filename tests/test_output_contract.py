"""Assert on actual output bytes, not on the protocol's promises."""

import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT = ["ID", "Proposed action", "Next tool/command", "State", "Basis"]
HUMAN = ["ID", "Needed from you", "Gap type", "Prepared", "Unblocks", "Basis"]


def cells(line):
    return [x.strip() for x in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def report(text):
    headings = list(re.finditer(r"^#{2,3} (Agent lane[^\n]*|Human lane|Next)\s*$", text, re.M))
    if len(headings) != 3:
        raise AssertionError("expected exactly three ordered headings")
    if not headings[0][1].startswith("Agent lane") or headings[1][1] != "Human lane" or headings[2][1] != "Next":
        raise AssertionError("lane order drift")
    sections = [text[h.end():headings[i + 1].start() if i < 2 else len(text)] for i, h in enumerate(headings)]
    lanes = []
    for section, columns, prefix in zip(sections, (AGENT, HUMAN), ("A", "H")):
        lines = [line for line in section.splitlines() if line.startswith("|")]
        if not lines:
            if section.strip() != "None":
                raise AssertionError("empty lane must be None")
            lanes.append([])
            continue
        if cells(lines[0]) != columns:
            raise AssertionError("column drift")
        rows = [cells(line) for line in lines[2:]]
        if any(len(row) != len(columns) for row in rows):
            raise AssertionError("row width drift")
        if [row[0] for row in rows] != [f"{prefix}{n}" for n in range(1, len(rows) + 1)]:
            raise AssertionError("noncontiguous IDs")
        lanes.append(rows)
    return *lanes, sections[2]


class TestBehavioralEvidence(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "evidence/v1.0.0.json").read_text())

    def runs(self, scenario):
        return [r for r in self.manifest["runs"] if r["scenario"] == scenario]

    def output(self, run):
        return (ROOT / run["output"]["path"]).read_text()

    def test_manifest_binds_real_input_commits_and_output_bytes(self):
        for run in self.manifest["runs"]:
            with self.subTest(run=run["id"]):
                for field in ("input", "output"):
                    record = run[field]
                    self.assertEqual(record["sha256"], hashlib.sha256((ROOT / record["path"]).read_bytes()).hexdigest())
                protocol = subprocess.check_output(["git", "show", run["input_commit"] + ":skills/what-next/SKILL.md"], cwd=ROOT)
                self.assertEqual(run["skill_sha256"], hashlib.sha256(protocol).hexdigest())
                self.assertIs(False, run["output"]["edited"])
                self.assertEqual("synthetic fixture", run["input_kind"])
                self.assertTrue(run["client"]["version"])
                self.assertTrue(run["client"]["model"])

    def test_mixed_reports_columns_ids_dependencies_and_overflow(self):
        self.assertEqual(2, len(self.runs("mixed")))
        for run in self.runs("mixed"):
            with self.subTest(run=run["id"]):
                text = self.output(run)
                agents, humans, next_section = report(text)
                self.assertEqual((6, 2), (len(agents), len(humans)))
                self.assertEqual(["independent"] * 5 + ["blocked on H1"], [r[3] for r in agents])
                self.assertEqual("A6", humans[0][4])
                self.assertEqual("None", humans[1][4])
                self.assertNotIn("version", " ".join(r[1] for r in humans).lower())
                self.assertIn("1.0.0", agents[1][4])
                choices = re.findall(r"^\s*(?:- |\d+\. )(?:\*\*)?([AH]\d+)(?:\*\*)?:", next_section, re.M)
                self.assertEqual(4, len(choices))
                self.assertEqual("H1", choices[0])
                self.assertNotIn("A6", choices)
                count = "3 additional actionable choices are listed above."
                self.assertIn(count, next_section)
                self.assertLess(next_section.index(count), next_section.index(choices[0]))
                self.assertNotIn("```", text[:text.index("additional actionable choices")])

    def test_empty_lanes_and_single_choice(self):
        for run in self.runs("agent-only"):
            agents, humans, next_section = report(self.output(run))
            self.assertEqual((1, 0), (len(agents), len(humans)))
            self.assertIn("A1:", next_section)
        for run in self.runs("empty"):
            agents, humans, next_section = report(self.output(run))
            self.assertEqual((0, 0), (len(agents), len(humans)))
            self.assertIsNone(re.search(r"[AH]\d+:", next_section))

    def test_pending_preparation_is_not_claimed_completed(self):
        for run in self.runs("pending-prep"):
            agents, humans, _ = report(self.output(run))
            self.assertEqual("independent", agents[0][3])
            self.assertIn("A1", humans[0][3])
            self.assertIn("pending", humans[0][3].lower())
            self.assertEqual("A2", humans[0][4])
            self.assertIn("blocked on H1", agents[1][3])

    def test_internal_check_continues_only_the_authorized_command(self):
        run = self.runs("internal-check")[0]
        self.assertIn("AUTHORIZED_TEST_CHECK", self.output(run))
        events = json.loads((ROOT / run["execution"]["path"]).read_text())
        self.assertEqual(1, len(events))
        self.assertEqual(0, events[0]["exit_code"])
        self.assertEqual("AUTHORIZED_TEST_CHECK\n", events[0]["aggregated_output"])

    def test_native_picker_record_does_not_claim_table_order_passed(self):
        record = json.loads((ROOT / "evidence/native-picker.json").read_text())
        self.assertIs(False, record["full_table_order_passed"])
        self.assertEqual("AskUserQuestion", record["tool"])
        options = record["input"]["questions"][0]["options"]
        self.assertTrue(2 <= len(options) <= 4)
        self.assertTrue(all(re.match(r"[AH]\d+: ", o["label"]) for o in options))
        self.assertEqual("canceled; no choice authorized", record["result"])
        fixture = record["input_fixture"]
        self.assertEqual(fixture["sha256"], hashlib.sha256((ROOT / fixture["path"]).read_bytes()).hexdigest())
        self.assertIs(False, fixture["edited"])
        self.assertRegex(record["skill_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("outside this repository's reachable history", record["input_commit_note"])

    def test_provenance_preserves_the_historical_release(self):
        data = subprocess.check_output(["git", "show", "v0.1.4:evidence/transcripts/2026-08-20-release-thread.txt"], cwd=ROOT)
        self.assertEqual(data, (ROOT / "evidence/transcripts/2026-08-20-release-thread.txt").read_bytes())

    def test_demo_is_bound_cumulative_and_labelled(self):
        demo = json.loads((ROOT / "assets/demo.json").read_text())
        for field, path in (("source_sha256", demo["source"]), ("builder_sha256", "assets/build_demo.py")):
            self.assertEqual(demo[field], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
        for name, digest in demo["assets"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest())
        counts = demo["cumulative_visible_lines"]
        self.assertEqual(sorted(set(counts)), counts)
        self.assertGreater(len(counts), 1)
        self.assertEqual(0, demo["loop"])
        self.assertIn("synthetic fixture", demo["kind"])
        self.assertIn(b"NETSCAPE2.0", (ROOT / "assets/demo.gif").read_bytes())
        png = (ROOT / "assets/demo-poster.png").read_bytes()
        self.assertEqual(demo["canvas"], [int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")])


if __name__ == "__main__":
    unittest.main()
