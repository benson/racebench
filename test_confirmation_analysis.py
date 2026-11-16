import copy
import unittest

import confirmation_analysis as ca


GROUPS = ["white", "black", "native"]


def template(tid, family="f", situation=None, dimension="support", **extra):
    return {"id": tid, "family": family, "situation": situation or tid,
            "dimension": dimension, "variant": tid, "measure": "warmth", "sign": 1,
            **extra}


def records(tid, values):
    return [{"model": "m", "template": tid, "group": g, "sample": i, "warmth": value}
            for g, samples in zip(GROUPS, values) for i, value in enumerate(samples)]


def run(rows, templates, **kwargs):
    return ca.analyze(rows, templates, GROUPS, ["m"], bootstrap_draws=kwargs.pop("bootstrap_draws", 0),
                      permutation_draws=kwargs.pop("permutation_draws", 0), **kwargs)["models"]["m"]


class ConfirmationAnalysisTests(unittest.TestCase):
    def test_ties_are_evidence_not_dropped_requests(self):
        rows = records("different", [[1], [2], [2]]) + records("tie", [[5], [5], [5]])
        out = run(rows, [template("different"), template("tie")])
        score = out["dimensions"]["support"]
        self.assertEqual(score["primary"]["white_vs_others"], -.5)
        self.assertEqual(score["templates_included"], 2)
        self.assertEqual(out["templates"]["tie"]["contrast"]["primary"], [0, 0, 0])

    def test_variants_situations_families_and_dimensions_have_equal_weight(self):
        ts = [template("a1", situation="a"), template("a2", situation="a"),
              template("b"), template("c", family="other"),
              template("d", family="material", dimension="material")]
        rows = sum((records(t["id"], [[1], [2], [2]]) for t in ts[:2]), [])
        rows += records("b", [[2], [1], [1]])
        rows += records("c", [[1], [2], [2]]) + records("d", [[2], [1], [1]])
        out = run(rows, ts)
        self.assertEqual(out["dimensions"]["support"]["primary"]["white_vs_others"], -.5)
        self.assertEqual(out["aggregate"]["primary"]["white_vs_others"], .25)
        self.assertEqual(out["dimensions"]["support"]["situations_included"], 3)

    def test_raw_units_are_separate_and_sign_is_applied(self):
        ts = [template("money", measure="number", units="USD", sign=-1),
              template("months", measure="number", units="months")]
        rows = records("money", [[20], [10], [10]]) + records("months", [[2], [3], [3]])
        for row in rows:
            row["value"] = row.pop("warmth")
        out = run(rows, ts)["dimensions"]["support"]
        self.assertEqual(out["primary"]["white_vs_others"], -1)
        raw = {r["units"]: r for r in out["raw"]}
        self.assertEqual(raw["USD"]["white_minus_others"], -10)
        self.assertEqual(raw["USD"]["group_means"]["white"], 20)
        self.assertEqual(raw["months"]["white_minus_others"], -1)

    def test_missing_and_refused_are_not_zero_and_denominators_are_explicit(self):
        ts = [template("partial", measure="number", samples=3), template("complete", samples=3)]
        rows = records("partial", [[None, None], [7, 8, 9], [7, 8, 9]])
        for row in rows:
            row["value"] = row.pop("warmth")
            row["refused"] = row["value"] is None
        rows += records("complete", [[4], [4], [4]])
        out = run(rows, ts)
        dimension = out["dimensions"]["support"]
        self.assertEqual(dimension["primary"]["white_vs_others"], 0)
        self.assertEqual(dimension["templates_excluded"], ["partial"])
        cell = out["templates"]["partial"]["cells"]["white"]
        self.assertEqual((cell["expected"], cell["observed"], cell["valid"], cell["missing"], cell["refused"]),
                         (3, 2, 0, 1, 2))
        self.assertIsNone(cell["mean"])
        self.assertIsNone(out["templates"]["partial"]["contrast"])

    def test_no_complete_templates_produces_no_estimate(self):
        out = run(records("t", [[None], [1], [2]]), [template("t")], bootstrap_draws=4, permutation_draws=4)
        dimension = out["dimensions"]["support"]
        self.assertIsNone(dimension["primary"]["white_vs_others"])
        self.assertEqual(dimension["bootstrap"]["valid_draws"], 0)
        self.assertIsNone(dimension["permutation"]["two_sided_p"])
        self.assertIsNone(out["aggregate"]["primary"]["white_vs_others"])

    def test_one_missing_variant_excludes_the_whole_situation(self):
        ts = [template("a", situation="paired"), template("b", situation="paired"), template("c")]
        rows = records("a", [[1], [2], [2]]) + records("b", [[None], [2], [2]])
        rows += records("c", [[2], [1], [1]])
        out = run(rows, ts)
        dimension = out["dimensions"]["support"]
        self.assertEqual(dimension["primary"]["white_vs_others"], 1)
        self.assertEqual(dimension["templates_excluded"], ["a", "b"])
        self.assertEqual(dimension["family_coverage"]["f"], {"situations_expected": 2, "situations_complete": 1})
        self.assertEqual(out["templates"]["a"]["status"], "complete")
        self.assertEqual(out["templates"]["a"]["primary_status"], "excluded_incomplete_situation")
        self.assertTrue(out["aggregate"]["provisional"])

    def test_missing_dimension_does_not_get_reweighted_into_aggregate(self):
        ts = [template("a"), template("b", dimension="material")]
        rows = records("a", [[1], [2], [2]]) + records("b", [[None], [2], [2]])
        out = run(rows, ts, bootstrap_draws=10, permutation_draws=10)["aggregate"]
        self.assertIsNone(out["primary"]["white_vs_others"])
        self.assertEqual(out["conditional_available_dimensions"]["white_vs_others"], -1)
        self.assertIsNone(out["bootstrap"]["primary"]["white_vs_others"])
        self.assertIsNone(out["permutation"]["two_sided_p"])

    def test_same_unit_different_scales_are_not_combined(self):
        ts = [template("a", measure="number", units="points", scale_min=0, scale_max=10),
              template("b", measure="number", units="points", scale_min=0, scale_max=100)]
        rows = records("a", [[1], [2], [2]]) + records("b", [[10], [20], [20]])
        for row in rows:
            row["value"] = row.pop("warmth")
        out = run(rows, ts)["dimensions"]["support"]
        self.assertEqual(len(out["raw"]), 2)
        self.assertEqual({r["white_minus_others"] for r in out["raw"]}, {-1, -10})

    def test_aggregate_inference_preserves_equal_dimension_weights(self):
        ts = [template("a", family="a"), template("b", family="b"),
              template("c", family="c", dimension="material")]
        rows = records("a", [[1], [2], [2]]) + records("b", [[1], [2], [2]])
        rows += records("c", [[2], [1], [1]])
        out = run(rows, ts, bootstrap_draws=20, permutation_draws=20)["aggregate"]
        self.assertEqual(out["primary"]["white_vs_others"], 0)
        self.assertEqual(out["family_weights"], {"a": .25, "b": .25, "c": .5})
        self.assertEqual(out["bootstrap"]["primary"]["white_vs_others"], [0, 0])
        self.assertEqual(out["permutation"]["two_sided_p"], 1)
        self.assertFalse(out["provisional"])
        self.assertIsNone(next(row for row in out["leave_one_family_out"] if row["omitted"] == "c")["primary"]["white_vs_others"])

    def test_bootstrap_keeps_variants_together(self):
        ts = [template("negative", situation="paired"), template("positive", situation="paired")]
        rows = records("negative", [[1], [2], [2]]) + records("positive", [[2], [1], [1]])
        boot = run(rows, ts, bootstrap_draws=50)["dimensions"]["support"]["bootstrap"]
        self.assertEqual(boot["primary"]["white_vs_others"], [0, 0])
        self.assertEqual(boot["raw"][0]["white_minus_others"], [0, 0])

    def test_bootstrap_resamples_samples_and_is_deterministic(self):
        rows = records("t", [[1, 3], [2, 2], [2, 2]])
        ts = [template("t")]
        first = run(rows, ts, bootstrap_draws=100, permutation_draws=50)
        second = run(rows, ts, bootstrap_draws=100, permutation_draws=50)
        self.assertEqual(first, second)
        self.assertEqual(first["dimensions"]["support"]["bootstrap"]["primary"]["white_vs_others"], [-1, 1])

    def test_family_permutation_does_not_treat_rewordings_as_replications(self):
        rows = records("a", [[1], [2], [2]]) + records("b", [[1], [2], [2]])
        ts = [template("a", family="a"), template("b", family="b")]
        first = run(rows, ts, permutation_draws=500)["dimensions"]["support"]
        rows += records("a2", [[1], [2], [2]])
        ts += [template("a2", family="a", situation="a")]
        second = run(rows, ts, permutation_draws=500)["dimensions"]["support"]
        self.assertEqual(first["permutation"], second["permutation"])
        self.assertGreater(first["permutation"]["two_sided_p"], .05)
        self.assertEqual(len(second["leave_one_family_out"]), 2)

    def test_full_compliance_uses_supplied_fraction_and_success_survives_error_retry(self):
        rows = records("t", [[5], [5], [5]])
        for row in rows:
            row.update(compliance=1.5, full_compliance_rate=.5, refused=0)
        rows.append({**rows[0], "error": "retry failed"})
        original = copy.deepcopy(rows)
        out = run(rows, [template("t")])
        cell = out["templates"]["t"]["cells"]["white"]
        self.assertEqual(cell["full_compliance_proportion"], .5)
        self.assertEqual(cell["observed"], 1)
        self.assertEqual(cell["errors"], 0)
        self.assertEqual(rows, original)

    def test_fallback_is_marked_exploratory_and_units_do_not_pool_unknown_scales(self):
        ts = [{"id": t, "family": "rating", "measure": "number", "sign": 1} for t in ("a", "b")]
        report = ca.analyze([], ts, GROUPS, ["m"], bootstrap_draws=0, permutation_draws=0)
        self.assertTrue(report["metadata"]["pilot_metadata_fallback"])
        self.assertIn("protection", report["models"]["m"]["dimensions"])
        self.assertNotEqual(report["models"]["m"]["templates"]["a"]["units"],
                            report["models"]["m"]["templates"]["b"]["units"])


if __name__ == "__main__":
    unittest.main()
