import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fairness_analysis import COUNTERFACTUAL_PAIRS


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class FairnessAnalysisTests(unittest.TestCase):
    def test_approval_gap_rule_is_applied_only_to_approve(self):
        metrics = read_json("outputs/baseline_fairness_metrics.json")
        for gap in metrics["approval_rate_gaps"]:
            self.assertEqual(gap["outcome"], "Approve")
            self.assertEqual(gap["investigation_triggered"], gap["absolute_gap_pp"] > 10.0)
        for gap in metrics["descriptive_non_approval_gaps"]:
            self.assertFalse(gap["investigation_triggered"])

    def test_mitigated_ten_point_gap_is_not_triggered(self):
        metrics = read_json("outputs/mitigated_fairness_metrics.json")
        target = next(
            gap for gap in metrics["approval_rate_gaps"]
            if gap["grouping"] == "age_group" and gap["left_group"] == "Under 30" and gap["right_group"] == "Age 30-50"
        )
        self.assertEqual(target["absolute_gap_pp"], 10.0)
        self.assertFalse(target["investigation_triggered"])

    def test_public_counterfactual_pair_ids_are_consistent(self):
        expected = {
            "gender": ("CF_G1", "CF_G2", "CF_G3"),
            "nationality": ("CF_N1", "CF_N2", "CF_N3"),
            "age": ("CF_A1", "CF_A2", "CF_A3"),
        }
        actual = {dimension: tuple(pair[0] for pair in pairs) for dimension, pairs in COUNTERFACTUAL_PAIRS.items()}
        self.assertEqual(actual, expected)
        comparison = read_json("outputs/baseline_vs_mitigated_comparison.json")
        pair_ids = {
            pair["pair_id"]
            for block in ("baseline_counterfactual_analysis", "mitigated_counterfactual_analysis")
            for pair in comparison[block]["pairs"]
        }
        self.assertEqual(pair_ids, set().union(*[set(values) for values in expected.values()]))

    def test_mitigation_uses_public_trigger_transition_name(self):
        mitigation = read_json("outputs/mitigation_assessment.json")
        self.assertIn("approval_gap_trigger_transitions", mitigation)
        self.assertNotIn("d008_trigger_transition", mitigation)
        self.assertEqual(mitigation["observed_fairness_effect"], "MIXED")


if __name__ == "__main__":
    unittest.main()
