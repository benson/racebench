import unittest

from example_analysis import permutation_spread, analyze_examples


class ExampleAnalysisTests(unittest.TestCase):
    def test_known_exact_null_distribution(self):
        # Six assignments of [0, 0, 1, 1] to two groups of two;
        # only the two separated assignments have spread one.
        result = permutation_spread([[[0, 0], [1, 1]]], draws=12_000, seed=19)
        self.assertAlmostEqual(result["p"], 1 / 3, delta=.02)
        self.assertEqual(result["spread"], 1)

    def test_model_offsets_do_not_create_group_effects(self):
        a = permutation_spread([[[0, 1], [1, 2]], [[2], [4, 5]]], draws=1000)
        b = permutation_spread([[[100, 101], [101, 102]], [[-18], [-16, -15]]], draws=1000)
        self.assertAlmostEqual(a["spread"], b["spread"])
        self.assertEqual(a["exceedances"], b["exceedances"])

    def test_equal_model_weight_despite_unequal_sample_counts(self):
        result = permutation_spread([[[0], [2, 2, 2]], [[10, 10, 10], [10]]], draws=5)
        self.assertEqual(result["means"], [5, 6])
        self.assertEqual(result["counts"], [[1, 3], [3, 1]])

    def test_ties_and_invalid_input(self):
        self.assertEqual(permutation_spread([[[5, 5], [5, 5]]], draws=10)["p"], 1)
        for blocks in ([], [[[1], []]], [[[float("nan")], [1]]]):
            with self.assertRaises(ValueError):
                permutation_spread(blocks, draws=10)

    def test_missing_model_is_excluded_and_full_prompt_family_is_used(self):
        data = {"run": "fixture", "models": ["a", "b"], "samples": 2,
                "groups": [{"id": "x"}, {"id": "y"}], "examples": ["t"],
                "templates": [{"id": "t", "measure": "number"}] + [{"id": str(i)} for i in range(39)],
                "cells": {"a": {"t": {"x": {"raw": 0, "valid": 2}, "y": {"raw": 1, "valid": 2}}},
                          "b": {"t": {"x": {"raw": None, "valid": 0}, "y": {"raw": 10, "valid": 2}}}}}
        records = [{"model": m, "template": "t", "group": g, "sample": s, "value": v}
                   for m, g, v in [("a", "x", 0), ("a", "y", 1), ("b", "y", 10)] for s in range(2)]
        out = analyze_examples(data, records, draws=100)["results"]["t"]
        self.assertEqual(out["models"], ["a"])
        self.assertEqual(out["adjusted_p"], min(1, out["p"] * 40))
        data["cells"]["a"]["t"]["x"]["raw"] = 99
        with self.assertRaises(ValueError):
            analyze_examples(data, records, draws=10)


if __name__ == "__main__":
    unittest.main()
