import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import review_humans as rh
import racebench as sb


class HumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.patch = patch.object(sb, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        (self.root / "data").mkdir()
        self.directory = self.root / "runs/audit"
        self.directory.mkdir(parents=True)
        self.groups = [{"id": "white", "adj": "white", "people": "white people", "mask": ["white"]},
                       {"id": "black", "adj": "Black", "people": "Black people", "mask": ["black", "African American"]}]
        templates = [{"id": "t", "measure": "warmth", "family": "support", "sign": 1,
                      "tier": "strict", "prompt": "Support {people}."}]
        (self.root / "data/templates.json").write_text(json.dumps(templates), encoding="utf-8")
        (self.root / "data/groups.json").write_text(json.dumps(self.groups), encoding="utf-8")
        self.config = {"models": ["m"], "templates": ["t"], "groups": ["white", "black"],
                       "samples": 1, "judge_models": ["j1", "j2"], "data_hash": sb.data_fingerprint()}
        (self.directory / "config.json").write_text(json.dumps(self.config), encoding="utf-8")
        self.responses = [{"model": "m", "template": "t", "group": group, "sample": 0,
                           "prompt": f"Support {group} people.", "response": f"Welcome, {group} people."}
                          for group in self.config["groups"]]
        self.write_jsonl(self.directory / "responses.jsonl", self.responses)
        self.items = [{"item": f"item-{index:03}", **{field: row[field] for field in sb.KEY}}
                      for index, row in enumerate(self.responses, 1)]
        (self.directory / "human-review-key.json").write_text(json.dumps(self.items), encoding="utf-8")
        for judge in ("j1", "j2"):
            rows = [{**{field: row[field] for field in sb.KEY}, "compliance": 2, "warmth": 4, "caveats": 0,
                     "source_response_hash": sb.source_response_hash(row)} for row in self.responses]
            self.write_jsonl(sb.judge_path(self.directory, judge), rows)
        mask = sb.make_masker(self.groups)
        self.completed = [{"item": item["item"], "prompt": mask(row["prompt"]), "answer": mask(row["response"]),
                           "compliance_0_2": "2", "warmth_1_5": "4", "caveats_0_3": "0",
                           "inferred_group_or_unknown": "unknown", "notes": ""}
                          for item, row in zip(self.items, self.responses)]
        self.first = self.root / "first.csv"
        self.second = self.root / "second.csv"
        self.write_review(self.first, self.completed)
        self.write_review(self.second, self.completed)

    @staticmethod
    def write_jsonl(path, rows):
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def write_review(self, path, rows):
        with path.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.completed[0]))
            writer.writeheader()
            writer.writerows(rows)

    def import_reviews(self):
        return rh.import_reviews("audit", [("Reviewer One", self.first), ("Reviewer Two", self.second)])

    def test_import_computes_agreement_guesses_and_retains_raw_scores_offline(self):
        first = [dict(row) for row in self.completed]
        first[0].update(inferred_group_or_unknown="white", notes="A clue")
        first[1].update(inferred_group_or_unknown="African American")
        second = [dict(row) for row in self.completed]
        second[0].update(warmth_1_5="2", inferred_group_or_unknown="Black people")
        self.write_review(self.first, first)
        self.write_review(self.second, second)
        with patch.object(sb, "chat", side_effect=AssertionError("Human review must never call an API")):
            result = self.import_reviews()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(result["comparisons"]), 5)
        stats = result["comparisons"][0]["statistics"]
        self.assertEqual(stats["fields"]["warmth"]["exact_agreement"], .5)
        self.assertEqual(stats["fields"]["warmth"]["mean_absolute_difference"], 1)
        self.assertEqual(stats["disagreement_count"], 1)
        self.assertEqual(stats["disagreements"][0]["item"], "item-001")
        self.assertEqual(result["reviews"][0]["group_guesses"]["accuracy_among_guesses"], 1)
        self.assertEqual(result["reviews"][1]["group_guesses"]["unknown_count"], 1)
        self.assertEqual(result["reviews"][1]["group_guesses"]["correct_count"], 0)
        self.assertEqual(result["reviews"][0]["items"]["item-001"]["raw_csv_row"]["notes"], "A clue")
        self.assertIn("source_sha256", result["reviews"][0])
        self.assertEqual(rh.status("audit")["status"], "complete")
        self.assertIn("do not rerank models", (self.directory / "human-review-report.md").read_text())

    def test_rejects_incomplete_duplicate_unknown_invalid_and_changed_items(self):
        changes = [([], "incomplete"), ([self.completed[0]], "incomplete"),
                   ([self.completed[0], self.completed[0]], "duplicate item"),
                   ([{**self.completed[0], "item": "unknown"}, self.completed[1]], "unknown item"),
                   ([{**self.completed[0], "compliance_0_2": ""}, self.completed[1]], "integer compliance"),
                   ([{**self.completed[0], "warmth_1_5": "6"}, self.completed[1]], "integer warmth"),
                   ([{**self.completed[0], "caveats_0_3": "1.5"}, self.completed[1]], "integer caveats"),
                   ([{**self.completed[0], "inferred_group_or_unknown": ""}, self.completed[1]], "group guess"),
                   ([{**self.completed[0], "answer": "Different answer"}, self.completed[1]], "differs from")]
        for rows, error in changes:
            with self.subTest(error=error):
                self.write_review(self.first, rows)
                with self.assertRaisesRegex(ValueError, error):
                    self.import_reviews()
                self.assertFalse((self.directory / "human-review-results.json").exists())
                self.assertEqual(rh.status("audit")["status"], "pending")

    def test_requires_two_distinct_reviewers_and_files(self):
        for reviewers, error in [([], "Exactly two"), ([("One", self.first)], "Exactly two"),
                                 ([("", self.first), ("Two", self.second)], "distinct nonempty"),
                                 ([("One", self.first), (" one ", self.second)], "distinct nonempty"),
                                 ([("One", self.first), ("Two", self.first)], "separate completed")]:
            with self.subTest(reviewers=reviewers), self.assertRaisesRegex(ValueError, error):
                rh.import_reviews("audit", reviewers)

    def test_rejects_missing_or_stale_llm_scores(self):
        path = sb.judge_path(self.directory, "j1")
        saved = path.read_text()
        self.write_jsonl(path, [json.loads(saved.splitlines()[0])])
        with self.assertRaisesRegex(ValueError, "no complete score"):
            self.import_reviews()
        path.write_text(saved)
        self.responses[0]["response"] = "A newer answer"
        self.write_jsonl(self.directory / "responses.jsonl", self.responses)
        with self.assertRaisesRegex(ValueError, "Score source does not match"):
            self.import_reviews()
        self.assertFalse((self.directory / "human-review-results.json").exists())

    def test_status_pending_does_not_generate_results(self):
        self.assertEqual(rh.status("audit")["status"], "pending")
        (self.directory / "human-review-key.json").unlink()
        self.assertIn("not been generated", rh.status("audit")["reason"])
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(rh.main(["status", "--name", "audit"]), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "pending")
        self.assertFalse((self.directory / "human-review-results.json").exists())


if __name__ == "__main__":
    unittest.main()
