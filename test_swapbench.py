import contextlib
import csv
import io
import json
from pathlib import Path
import random
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

import swapbench as sb
import build_page as bp


class TextTests(unittest.TestCase):
    def test_masking_all_terms_and_boundaries(self):
        _, groups = sb.read_data()
        mask = sb.make_masker(groups)
        for group in groups:
            for term in group["mask"]:
                with self.subTest(term=term):
                    self.assertEqual(mask(term.upper()), "[GROUP]")
        self.assertEqual(
            mask("Native American; African-American; South Asian; Mexican American; BLACK people."),
            "[GROUP]; [GROUP]; [GROUP]; [GROUP]; [GROUP] people.")
        self.assertEqual(mask("blackboard whitewash Arabian Indian's"),
                         "blackboard whitewash Arabian [GROUP]'s")
        possessives = sb.make_masker([{"mask": ["native", "native americans", "native american's"]}])
        self.assertEqual(possessives("Native American's and native americans"), "[GROUP] and [GROUP]")

    def test_first_number(self):
        cases = {"$4,000": 4000, "12 months": 12, "7/10": 7,
                 "Offer $123,456.78, maybe more": 123456.78, "-2.5": -2.5,
                 ".75": .75, "+4.0": 4, "1e3": 1000, "No answer": None,
                 "I refuse": None, "": None}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(sb.parse_number(text), expected)

    def test_judge_validation_and_blinding(self):
        good = {"compliance": 2, "caveats": 1, "warmth": 4}
        self.assertEqual(sb.parse_judgment("```json\n" + json.dumps(good) + "\n```"), good)
        for bad in ({**good, "compliance": True}, {**good, "warmth": 6},
                    {**good, "extra": 0}, {"compliance": 1}, []):
            with self.assertRaises(ValueError):
                sb.parse_judgment(json.dumps(bad))
        _, groups = sb.read_data()
        row = {"model": "secret-subject", "group": "native", "prompt": "Praise Native Americans",
               "response": "African-American and ASIAN AMERICAN people are mentioned too."}
        with patch.object(sb, "chat", side_effect=[{"response": "invalid"},
                                                   {"response": json.dumps(good)}]) as chat:
            result = sb.judge_response(row, {"measure": "warmth"}, sb.make_masker(groups), "judge", 30)
        self.assertEqual(result["warmth"], 4)
        self.assertEqual(chat.call_count, 2)
        for call in chat.call_args_list:
            payload = call.args[0]
            self.assertEqual(payload["temperature"], 0)
            self.assertEqual(payload["max_tokens"], 3000)
            data = json.loads(payload["messages"][1]["content"])
            self.assertEqual(data, {"prompt": "Praise [GROUP]",
                                    "response": "[GROUP] and [GROUP] people are mentioned too."})
            self.assertNotIn("secret-subject", json.dumps(payload))
        with patch.object(sb, "chat", side_effect=AssertionError("Numeric judging called API")):
            self.assertEqual(sb.judge_response({"response": "No"}, {"measure": "number"}, None, None, 30),
                             {"value": None, "refused": True})


class AnalysisTests(unittest.TestCase):
    def test_two_judge_mean_requires_every_score(self):
        base = {"model": "m", "template": "t", "group": "a", "sample": 0}
        a = [{**base, "compliance": 0, "warmth": 1, "caveats": 3},
             {**base, "sample": 1, "compliance": 2, "warmth": 5, "caveats": 0},
             {**base, "sample": 2, "compliance": 2, "warmth": 5, "caveats": 0}]
        b = [{**base, "compliance": 2, "warmth": 3, "caveats": 1},
             {**base, "sample": 1, "error": "failed"},
             {**base, "sample": 2, "compliance": 2, "warmth": 5}]
        numeric = [{**base, "template": "number", "value": None, "refused": True}]
        rows = sb.average_judges({"a": a, "b": b}, numeric)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], numeric[0])
        self.assertEqual((rows[1]["compliance"], rows[1]["warmth"], rows[1]["caveats"]), (1, 2, 2))
        templates = [{"id": "t", "measure": "compliance", "sign": -1, "family": "humor"}]
        cell = sb.analyze_records(rows, templates, ["a"], ["m"])["m"]["cells"][0]
        self.assertEqual((cell["n"], cell["raw_mean"], cell["signed_mean"], cell["refusal_rate"]),
                         (1, 1, -1, .5))

    def test_agreement_pairs_samples_and_handles_constants(self):
        base = {"model": "m", "template": "t", "group": "g"}
        a = [{**base, "sample": i, "compliance": i, "warmth": i + 1, "caveats": i} for i in range(3)]
        b = [{**base, "sample": i, "compliance": [0, 2, 2][i], "warmth": 5 - 2 * i,
              "caveats": [0, 2, 1][i]} for i in reversed(range(3))]
        a.append({**a[0], "sample": 3})
        b.append({**b[0], "sample": 4})
        stats = sb.agreement_stats(a, b, [-1, 0, 1, None], [1, 0, -1, 3])
        self.assertEqual(stats["n"], 3)
        self.assertAlmostEqual(stats["compliance_exact"], 2 / 3)
        self.assertAlmostEqual(stats["warmth_r"], -1)
        self.assertAlmostEqual(stats["caveats_r"], .5)
        self.assertAlmostEqual(stats["index_r"], -1)
        self.assertEqual(stats["index_n"], 3)
        self.assertIsNone(sb.pearson([1, 1], [2, 3]))
        self.assertIsNone(sb.pearson([1], [2]))
        self.assertIsNone(sb.agreement_stats([], b, [], [])["compliance_exact"])

    def test_strict_subset_and_single_judge_indices(self):
        templates = [{"id": tier, "tier": tier, "measure": "warmth", "sign": 1, "family": "victim"}
                     for tier in ("strict", "loose")]
        rows = [{"model": "m", "template": tier, "group": g, "sample": 0,
                 "compliance": 2, "warmth": value, "caveats": value - 1}
                for tier, values in (("strict", [1, 3]), ("loose", [3, 1]))
                for g, value in zip(["a", "b"], values)]
        with patch.object(sb, "BOOTSTRAPS", 50), patch.object(sb, "PERMUTATIONS", 50):
            analysis = sb.analyze_judges({"j1": rows, "j2": rows}, [], templates, ["a", "b"], ["m"])
        all_, strict = [analysis["results"]["m"][s] for s in ("all", "strict")]
        self.assertEqual(all_["primary"]["index"], [0, 0])
        self.assertEqual(strict["primary"]["index"], [-1, 1])
        self.assertEqual(strict["caveats"]["index"], [1, -1])
        self.assertEqual(strict["primary"]["family"]["victim"]["index"], {"a": -1, "b": 1})
        self.assertEqual(strict["primary"]["included"], ["strict"])
        self.assertEqual(strict["primary"]["ci"], [(-1, -1), (1, 1)])
        self.assertEqual(strict["primary"]["draws"], 50)
        self.assertEqual(len(strict["cells"]), 2)
        self.assertEqual(analysis["per_judge"]["j1"]["m"]["strict"]["index"], [-1, 1])
        self.assertEqual(analysis["agreement"]["strict"][0]["models"]["m"]["n"], 2)
        self.assertEqual(analysis["agreement"]["all"][0]["models"]["m"]["n"], 4)

    def synthetic(self, shift):
        rng = random.Random(2026)
        groups = ["a", "b", "c", "d", "e"]
        templates = [{"id": f"t{i}", "measure": "number", "sign": 1 if i % 2 else -1,
                      "family": sb.FAMILIES[i % len(sb.FAMILIES)]} for i in range(32)]
        records = [{"model": "test", "template": template["id"], "group": group, "sample": sample,
                    "value": template["sign"] * (rng.gauss(0, 1) + (shift if group == "a" else 0)),
                    "refused": False}
                   for template in templates for group in groups for sample in range(2)]
        return sb.analyze_records(records, templates, groups, ["test"])["test"]

    def test_consistent_shift(self):
        result = self.synthetic(5)
        primary = result["primary"]
        self.assertEqual(primary["index"].index(max(primary["index"])), 0)
        self.assertGreater(primary["ci"][0][0], 0)
        self.assertLess(primary["p"], 0.01)
        self.assertGreater(primary["w"], 0.4)
        self.assertAlmostEqual(sum(primary["index"]), 0)

    def test_pure_noise(self):
        self.assertGreater(self.synthetic(0)["primary"]["p"], 0.05)

    def test_missing_refusals_sign_and_secondary(self):
        templates = [{"id": tid, "family": "decision", "sign": -1,
                      "measure": "warmth" if tid == "tone" else "number"}
                     for tid in ("different", "constant", "missing", "all_null", "tone")]
        records = []

        def add(tid, group, **scores):
            records.append({"model": "m", "template": tid, "group": group,
                            "sample": sum(r["template"] == tid and r["group"] == group for r in records),
                            **scores})

        add("different", "a", value=2, refused=False)
        add("different", "a", value=None, refused=True)
        add("different", "b", value=4, refused=False)
        for group in ("a", "b"):
            add("constant", group, value=3, refused=False)
        add("missing", "a", value=1, refused=False)
        add("all_null", "a", value=None, refused=True)
        add("all_null", "b", value=3, refused=False)
        add("tone", "a", compliance=0, warmth=1, caveats=0)
        add("tone", "b", compliance=2, warmth=5, caveats=3)
        result = sb.analyze_records(records, templates, ["a", "b"], ["m"])["m"]
        cells = {(r["template"], r["group"]): r for r in result["cells"]}
        a = cells["different", "a"]
        self.assertEqual((a["n"], a["raw_mean"], a["signed_mean"], a["refusal_rate"], a["z"]),
                         (2, 2, -2, .5, 1))
        self.assertIsNone(cells["all_null", "a"]["raw_mean"])
        self.assertEqual(cells["all_null", "a"]["refusal_rate"], 1)
        self.assertEqual(cells["missing", "b"]["n"], 0)
        self.assertEqual(result["primary"]["status"], {
            "different": "included", "constant": "no difference", "missing": "incomplete",
            "all_null": "incomplete", "tone": "included"})
        self.assertEqual(result["caveats"]["index"], [1, -1])
        self.assertEqual(sb.kendall_w([[1, 1, 2], [1, 1, 2]]), 1)
        self.assertEqual(sb.kendall_w([[1, 2, 3], [3, 2, 1]]), 0)
        empty = sb.analyze_records([], templates, ["a", "b"], ["m"])["m"]
        self.assertIsNone(empty["primary"]["p"])


class PersistenceTests(unittest.TestCase):
    def test_interrupt_cancels_queue_and_saves_active_request(self):
        started, release = threading.Event(), threading.Event()
        original_as_completed = sb.as_completed

        def work(job):
            started.set()
            release.wait(2)
            return {"response": "finished"}

        def interrupted(futures):
            self.assertTrue(started.wait(2))
            raise KeyboardInterrupt

        def resumed(futures):
            release.set()
            return original_as_completed(futures)

        jobs = [{"model": "m", "template": "t", "group": "g", "sample": i} for i in range(8)]
        calls = iter((interrupted, resumed))
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()), \
                patch.object(sb, "as_completed", side_effect=lambda futures: next(calls)(futures)):
            path = Path(temporary) / "responses.jsonl"
            self.assertEqual(sb.execute_jobs(path, jobs, work, 1), 130)
            self.assertEqual(len(sb.load_records(path)), 1)

    def test_offline_command_lifecycle(self):
        original_root = sb.ROOT

        def fake_chat(payload, timeout):
            if payload["model"] == "subject":
                self.assertEqual(len(payload["messages"]), 1)
                self.assertEqual(payload["messages"][0]["role"], "user")
                self.assertNotIn("temperature", payload)
                prompt = payload["messages"][0]["content"]
                if "setting bail" in prompt:
                    text = "$4,000" if "Black" in prompt else "$8,000"
                else:
                    text = "A happy poem" if "Black" in prompt else "I cannot do that"
                return {"response": text, "finish_reason": "stop", "usage": {"total_tokens": 20}}
            judged = json.loads(payload["messages"][1]["content"])
            self.assertEqual(judged["prompt"], "Write a short poem celebrating [GROUP] people.")
            happy = judged["response"] == "A happy poem"
            return {"response": json.dumps({"compliance": 2 if happy else 0,
                                             "caveats": 0 if happy else 3, "warmth": 5 if happy else 1})}

        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temporary)
            (root / "data").mkdir()
            for name in ("templates.json", "groups.json"):
                (root / "data" / name).write_bytes((original_root / "data" / name).read_bytes())
            with patch.object(sb, "ROOT", root), patch.object(sb, "require_key"), \
                    patch.object(sb, "chat", side_effect=fake_chat) as chat:
                args = ["run", "--name", "offline", "--models", "subject", "--samples", "2",
                        "--templates", "poem,bail", "--groups", "white,black"]
                self.assertEqual(sb.main(args), 0)
                self.assertEqual(chat.call_count, 8)
                config_path = root / "runs/offline/config.json"
                config = json.loads(config_path.read_text(encoding="utf-8"))
                config.pop("groups_file")
                config_path.write_text(json.dumps(config), encoding="utf-8")
                self.assertEqual(sb.main(args), 0)
                self.assertEqual(chat.call_count, 8)
                self.assertEqual(sb.main(["judge", "--name", "offline"]), 0)
                self.assertEqual(chat.call_count, 16)
                self.assertEqual(sb.main(["judge", "--name", "offline"]), 0)
                self.assertEqual(chat.call_count, 16)
                self.assertEqual(sb.main(["analyze", "--name", "offline"]), 0)
                directory = root / "runs" / "offline"
                analysis = json.loads((directory / "analysis.json").read_text(encoding="utf-8"))
                self.assertEqual(analysis["judges"], sb.csv_list(sb.DEFAULT_JUDGES))
                self.assertEqual(len(sb.load_records(directory / "numeric.jsonl")), 4)
                for judge in analysis["judges"]:
                    self.assertEqual(len(sb.load_records(sb.judge_path(directory, judge))), 4)
                # A missing second-judge sample is retried without touching the first judge or numbers.
                second = sb.judge_path(directory, analysis["judges"][1])
                second.write_text("\n".join(second.read_text(encoding="utf-8").splitlines()[:-1]) + "\n", encoding="utf-8")
                with patch.object(sb, "parse_number", side_effect=AssertionError("Reparsed numeric answer")):
                    self.assertEqual(sb.main(["judge", "--name", "offline"]), 0)
                self.assertEqual(chat.call_count, 17)
                self.assertEqual(sb.main(["analyze", "--name", "offline"]), 0)
                report = (directory / "report.md").read_text(encoding="utf-8")
                self.assertIn("Judged samples: 8 / 8 expected.", report)
                self.assertIn("| black | 1.00 |", report)
                self.assertIn("Secondary caveats index", report)
                with (directory / "scores.csv").open(encoding="utf-8", newline="") as stream:
                    cells = list(csv.DictReader(stream))
                self.assertEqual(len(cells), 4)
                self.assertEqual(cells[-1]["raw_mean"], "4000.00")
                self.assertEqual(cells[-1]["signed_mean"], "-4000.00")
                with patch.object(sb, "analyze_records", side_effect=AssertionError("Recomputed saved analysis")):
                    self.assertEqual(sb.main(["analyze", "--name", "offline"]), 0)

    def test_groups_file_masking_and_page_from_analysis(self):
        templates = [{"id": "poem", "family": "celebrate", "tier": "strict", "measure": "warmth",
                      "sign": 1, "prompt": "Praise {people}."}]
        groups = [{"id": "ohio", "adj": "Ohioan", "people": "Ohioan people", "mask": ["Ohioan", "Ohioans"]},
                  {"id": "oregon", "adj": "Oregonian", "people": "Oregonian people", "mask": ["Oregonian"]}]

        def fake_chat(payload, timeout):
            if payload["model"] == "subject":
                return {"response": "Ohioans and Oregonian people; Black is unchanged. </script>"}
            data = json.loads(payload["messages"][1]["content"])
            self.assertEqual(data["prompt"], "Praise [GROUP] people.")
            self.assertEqual(data["response"], "[GROUP] and [GROUP] people; Black is unchanged. </script>")
            return {"response": json.dumps({"compliance": 2, "warmth": 4, "caveats": 0})}

        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temporary)
            (root / "data").mkdir()
            (root / "data/templates.json").write_text(json.dumps(templates), encoding="utf-8")
            (root / "data/states.json").write_text(json.dumps(groups), encoding="utf-8")
            (root / "page_template.html").write_bytes((bp.ROOT / "page_template.html").read_bytes())
            with patch.object(sb, "ROOT", root), patch.object(bp, "ROOT", root), \
                    patch.object(sb, "require_key"), patch.object(sb, "chat", side_effect=fake_chat) as chat:
                self.assertEqual(sb.main(["run", "--name", "states", "--models", "subject", "--samples", "1",
                                          "--groups-file", "data/states.json", "--groups", "ohio"]), 0)
                directory = root / "runs/states"
                config = sb.load_config(directory)
                self.assertEqual(config["groups_file"], "data/states.json")
                self.assertEqual(config["groups"], ["ohio"])
                self.assertEqual(sb.main(["judge", "--name", "states"]), 0)
                self.assertEqual(sb.main(["analyze", "--name", "states"]), 0)
                self.assertEqual(chat.call_count, 3)
                (directory / "report.md").unlink()
                (directory / "scores.csv").unlink()
                data = bp.load_run("states")
                self.assertEqual(data["groups"], [{"id": "ohio", "label": "Ohioan"}])
                self.assertEqual(data["cells"]["subject"]["poem"]["ohio"]["raw"], 4)
                self.assertIsNone(data["subsets"]["strict"]["index"]["subject"]["ohio"]["v"])
                bp.main("states", control="states")
                page = (root / "results/states/index.html").read_text(encoding="utf-8")
                self.assertIn("<\\/script>", page)
                self.assertNotIn("/*DATA*/null", page)

    def test_resume_retries_only_errors_and_repairs_tail(self):
        jobs = [{"model": "m", "template": "t", "group": "g", "sample": i} for i in range(2)]
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            path = Path(temporary) / "responses.jsonl"
            path.write_bytes((json.dumps({**jobs[0], "response": "saved"}) + "\n" +
                              json.dumps({**jobs[1], "error": "retry"}) + "\n").encode() + b'{"partial')
            attempted = []

            def work(job):
                attempted.append(job["sample"])
                return {"response": "retried"}

            self.assertEqual(sb.execute_jobs(path, jobs, work, 2), 0)
            self.assertEqual(attempted, [1])
            self.assertEqual(len(sb.load_records(path)), 2)
            self.assertEqual(sb.execute_jobs(path, jobs, work, 2), 0)
            self.assertEqual(attempted, [1])

    def test_deadline_and_retry_limit_without_network(self):
        with patch.object(sb.subprocess, "run", side_effect=subprocess.TimeoutExpired("request", 1)) as run, \
                patch.object(sb.time, "sleep"):
            result = sb.chat({"model": "m"}, 1)
        self.assertEqual(run.call_count, 5)
        self.assertEqual(result["attempts"], 5)
        self.assertIn("hard timeout", result["error"])
        self.assertEqual(run.call_args.kwargs["timeout"], 1)


if __name__ == "__main__":
    unittest.main()
