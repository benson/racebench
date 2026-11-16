import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import confirmation as c


class ConfirmationRunnerTests(unittest.TestCase):
    def test_explicit_allocation_and_unit_answers(self):
        for text, expected in (("I would allocate $100.", 100), ("I would give 50 credits.", 50),
                               ("Score: 8 out of 10", 8), ("5 penalty points", 5)):
            self.assertEqual(c.sb.parse_number(text), expected)

    def test_budget_rejects_invalid_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            for cap in (0, -1, math.nan, math.inf):
                with self.assertRaises(ValueError):
                    c.Budget(Path(tmp), cap, {})

    def test_study_lock_covers_two_budget_users(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with c.study_lock(directory):
                with self.assertRaises(ValueError):
                    with c.study_lock(directory):
                        self.fail("Second collector acquired the same study")
            self.assertFalse((directory / ".confirmation.lock").exists())

    def test_budget_reserves_retries_and_persists_spending(self):
        pricing = {"m": {"prompt": "0", "completion": "0.01", "request": "0.01"}}
        payload = {"model": "m", "messages": [], "max_tokens": 10}
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            calls = []
            def original(*args):
                calls.append(args)
                return {"usage": {"cost": .10}, "attempts": 2}
            first = c.Budget(directory, .8, pricing)
            self.assertNotIn("error", first.wrap(original)(payload, 1))
            self.assertAlmostEqual(first.accounted, .21)
            resumed = c.Budget(directory, .7, pricing)
            self.assertTrue(resumed.wrap(original)(payload, 1)["budget_stopped"])
            self.assertEqual(len(calls), 1)

    def test_interrupted_reservation_remains_charged(self):
        pricing = {"m": {"prompt": "0", "completion": "0.01"}}
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            budget = c.Budget(directory, .9, pricing)
            with self.assertRaises(RuntimeError):
                budget.wrap(lambda *a: (_ for _ in ()).throw(RuntimeError()))(
                    {"model": "m", "messages": [], "max_tokens": 10}, 1)
            resumed = c.Budget(directory, .9, pricing)
            self.assertAlmostEqual(sum(resumed.active.values()), .5)
            self.assertTrue(resumed.wrap(lambda *a: self.fail("Sent request"))(
                {"model": "m", "messages": [], "max_tokens": 10}, 1)["budget_stopped"])

    def test_verify_detects_changed_frozen_copy(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(c, "ROOT", Path(tmp)):
            directory = Path(tmp) / "studies" / "example"
            directory.mkdir(parents=True)
            source = Path(tmp) / "source.py"
            source.write_text("original")
            snapshot = directory / "templates.json"
            snapshot.write_text("[]")
            (directory / "manifest.json").write_text(json.dumps({
                "hashes": {"source.py": c.sha(source)},
                "snapshot_hashes": {"templates.json": c.sha(snapshot)}}))
            c.verify("example")
            snapshot.write_text("[1]")
            with self.assertRaisesRegex(ValueError, "snapshots"):
                c.verify("example")

    def test_unbound_existing_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "config.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "provenance"):
                c.bind_run(directory, {"name": "example"})

    def test_fresh_prompt_structure(self):
        situations = c.validate_templates(c.read(c.TEMPLATES))
        self.assertEqual(len(situations), 24)


if __name__ == "__main__":
    unittest.main()
