"""Assert on the picker-ending contract and on the runs that exercised it."""

import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "what-next" / "SKILL.md"
LABEL = re.compile(r"^[AH]\d+: ")
HUMAN_SCENARIOS = ("human-and-agent", "single-human")


def section(text, heading):
    """The body of one heading, up to the next heading of equal or higher rank."""
    level = len(heading) - len(heading.lstrip("#"))
    start = text.index("\n" + heading + "\n") + len(heading) + 2
    rest = text[start:]
    stop = re.search(r"^#{1,%d} " % level, rest, re.M)
    if stop is None:
        return " ".join(rest.split())
    return " ".join(rest[: stop.start()].split())


def skill_hashes():
    """Every sha256 SKILL.md has had, by content, so rebased commits still match."""
    commits = subprocess.check_output(
        ["git", "log", "--format=%H", "--", "skills/what-next/SKILL.md"],
        cwd=ROOT,
        text=True,
    ).split()
    hashes = set()
    for commit in commits:
        data = subprocess.check_output(
            ["git", "show", commit + ":skills/what-next/SKILL.md"], cwd=ROOT
        )
        hashes.add(hashlib.sha256(data).hexdigest())
    return hashes


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


class TestSkillText(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text()

    def test_next_requires_the_call_to_be_the_last_thing(self):
        body = section(self.text, "### Next")
        self.assertIn("`Next` is a structured-choice call", body)
        self.assertIn("the last thing in the response", body)
        self.assertIn("nothing after it", body)

    def test_next_carves_not_now_out_of_the_id_rule(self):
        body = section(self.text, "### Next")
        self.assertIn("`Not now`", body)
        self.assertIn("needs neither an ID nor an action", body)

    def test_host_adapters_name_each_tool_and_the_padding(self):
        body = section(self.text, "## Host adapters")
        for token in ("`AskUserQuestion`", "`request_user_input`", "`Not now`"):
            with self.subTest(token=token):
                self.assertIn(token, body)
        self.assertIn("Never add it to a plain list", body)

    def test_host_adapters_keep_the_plain_list_fallback(self):
        body = section(self.text, "## Host adapters")
        self.assertIn("noninteractive", body)
        self.assertIn("exposes no structured-choice tool", body)
        self.assertIn("the human lane is `None` and only one actionable choice", body)

    def test_turn_boundary_ends_an_explicit_determination_on_the_call(self):
        body = section(self.text, "## Turn boundary")
        self.assertIn("stopping means ending the way `Next` describes", body)
        self.assertIn("while independent authorized work remains", body)


class TestRecordedRuns(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "evidence/picker-ending.json").read_text())
        self.runs = self.record["runs"]

    def phase(self, phase, scenario=None, product=None):
        found = []
        for run in self.runs:
            if run["phase"] != phase:
                continue
            if scenario is not None and run["scenario"] != scenario:
                continue
            if product is not None and run["client"]["product"] != product:
                continue
            found.append(run)
        return found

    def call(self, run):
        return json.loads((ROOT / run["tool_input"]["path"]).read_text())

    def labels(self, run):
        return [o["label"] for o in self.call(run)["questions"][0]["options"]]

    def test_every_run_binds_its_files(self):
        self.assertEqual(len(self.runs), len({r["id"] for r in self.runs}))
        for run in self.runs:
            with self.subTest(run=run["id"]):
                self.assertEqual(run["input"]["sha256"], digest(run["input"]["path"]))
                self.assertEqual(run["output"]["sha256"], digest(run["output"]["path"]))
                self.assertIs(False, run["output"]["edited"])
                self.assertEqual("synthetic fixture", run["input_kind"])
                self.assertTrue(run["client"]["version"])
                self.assertTrue(run["finding"])
                if run["tool"] is not None:
                    self.assertEqual(
                        run["tool_input"]["sha256"], digest(run["tool_input"]["path"])
                    )

    def test_runs_cover_every_scenario_host_and_phase(self):
        for phase in ("base", "edited"):
            for scenario in ("human-and-agent", "single-human", "agent-only"):
                with self.subTest(phase=phase, scenario=scenario):
                    claude = self.phase(phase, scenario, "Claude Code")
                    codex = self.phase(phase, scenario, "Codex CLI")
                    self.assertEqual(4, len(claude))
                    self.assertEqual(1, len(codex))

    def test_runs_bind_to_the_skill_text_they_exercised(self):
        known = skill_hashes()
        base = subprocess.check_output(
            ["git", "show", self.record["base_commit"] + ":skills/what-next/SKILL.md"],
            cwd=ROOT,
        )
        base_hash = hashlib.sha256(base).hexdigest()
        edited = {r["skill_sha256"] for r in self.phase("edited")}
        self.assertEqual({base_hash}, {r["skill_sha256"] for r in self.phase("base")})
        self.assertEqual(1, len(edited))
        self.assertNotIn(base_hash, edited)
        self.assertTrue(edited <= known)

    def test_recorded_calls_have_the_fixed_shape(self):
        calls = [r for r in self.runs if r["tool"] is not None]
        self.assertTrue(calls)
        for run in calls:
            with self.subTest(run=run["id"]):
                self.assertEqual("AskUserQuestion", run["tool"])
                self.assertIsInstance(run["full_table_order_passed"], bool)
                questions = self.call(run)["questions"]
                self.assertEqual(1, len(questions))
                self.assertEqual("Next", questions[0]["header"])
                self.assertIs(False, questions[0]["multiSelect"])
                options = questions[0]["options"]
                self.assertTrue(2 <= len(options) <= 4)
                for option in options:
                    self.assertTrue(option["description"].strip())
                    if option["label"] != "Not now":
                        self.assertRegex(option["label"], LABEL)

    def test_not_now_is_the_last_option_and_pads_the_single_choice(self):
        for run in self.runs:
            if run["tool"] is None:
                continue
            labels = self.labels(run)
            if "Not now" not in labels:
                continue
            with self.subTest(run=run["id"]):
                self.assertEqual("Not now", labels[-1])
                self.assertEqual(1, labels.count("Not now"))
        for run in self.phase("edited", "single-human", "Claude Code"):
            with self.subTest(run=run["id"]):
                self.assertEqual(2, len(self.labels(run)))

    def test_plain_lists_never_carry_not_now(self):
        for run in self.runs:
            if run["tool"] is not None:
                continue
            with self.subTest(run=run["id"]):
                text = (ROOT / run["output"]["path"]).read_text()
                self.assertNotIn("Not now", text)

    def test_each_finding_names_the_labels_of_its_call(self):
        for run in self.runs:
            if run["tool"] is None:
                continue
            with self.subTest(run=run["id"]):
                for label in self.labels(run):
                    self.assertIn(label, run["finding"])

    def test_table_order_flag_agrees_with_the_output_text(self):
        for run in self.runs:
            if run["tool"] is None:
                continue
            with self.subTest(run=run["id"]):
                text = (ROOT / run["output"]["path"]).read_text().lower()
                both = "agent lane" in text and "human lane" in text
                self.assertIs(both, run["full_table_order_passed"])

    def test_no_run_states_a_zero_additional_count(self):
        pattern = re.compile(r"(\d+) additional actionable choices are listed above")
        for run in self.runs:
            with self.subTest(run=run["id"]):
                text = (ROOT / run["output"]["path"]).read_text()
                for count in pattern.findall(text):
                    self.assertGreater(int(count), 0)

    def test_readme_counts_match_the_recorded_runs(self):
        readme = " ".join((ROOT / "README.md").read_text().split())
        before = 0
        after = 0
        ordered = 0
        for scenario in HUMAN_SCENARIOS:
            for run in self.phase("base", scenario, "Claude Code"):
                if run["tool"] is not None:
                    before += 1
            for run in self.phase("edited", scenario, "Claude Code"):
                if run["tool"] is not None:
                    after += 1
                    if run["full_table_order_passed"]:
                        ordered += 1
        self.assertIn(f"({after} of 8, against {before} of 8 before)", readme)
        self.assertIn(f"preceded the call in {ordered} of those 8 runs", readme)

    def test_agent_only_control_never_calls(self):
        for run in self.phase("base", "agent-only") + self.phase(
            "edited", "agent-only"
        ):
            with self.subTest(run=run["id"]):
                self.assertIsNone(run["tool"])

    def test_base_skill_never_made_the_call_for_a_single_human_choice(self):
        for run in self.phase("base", "single-human", "Claude Code"):
            with self.subTest(run=run["id"]):
                self.assertIsNone(run["tool"])

    def test_edited_skill_ends_a_human_lane_on_the_call(self):
        for scenario in HUMAN_SCENARIOS:
            for run in self.phase("edited", scenario, "Claude Code"):
                with self.subTest(run=run["id"]):
                    self.assertEqual("AskUserQuestion", run["tool"])

    def test_single_human_call_carries_the_human_choice_and_the_padding(self):
        for run in self.phase("edited", "single-human", "Claude Code"):
            with self.subTest(run=run["id"]):
                labels = self.labels(run)
                self.assertRegex(labels[0], r"^H1: ")
                self.assertIn("Not now", labels)

    def test_human_and_agent_call_carries_both_choices(self):
        for run in self.phase("edited", "human-and-agent", "Claude Code"):
            with self.subTest(run=run["id"]):
                labels = self.labels(run)
                ids = {label.split(":")[0] for label in labels if label != "Not now"}
                self.assertEqual({"A1", "H1"}, ids)

    def test_plain_list_runs_end_on_id_labelled_choices(self):
        pattern = re.compile(
            r"^\s*(?:[-*] |\d+\. )?(?:\*\*|`)?([AH]\d+)(?:\*\*|`)?:", re.M
        )
        for run in self.runs:
            if run["tool"] is not None:
                continue
            with self.subTest(run=run["id"]):
                text = (ROOT / run["output"]["path"]).read_text()
                tail = text[text.rindex("Next") :]
                self.assertTrue(pattern.search(tail))


if __name__ == "__main__":
    unittest.main()
