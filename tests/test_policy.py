import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from policy import evaluate_lab_policy


class LabPolicyTests(unittest.TestCase):
    def test_policy_sanity_fixtures(self):
        cases = json.loads((ROOT / "data" / "policy_sanity_cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["case_id"]):
                result = evaluate_lab_policy(case)
                self.assertTrue(result["computable"])
                self.assertAlmostEqual(result["lab_dbr_ratio"], case["expected_lab_dbr_ratio"])
                self.assertEqual(result["lab_policy_cap"], case["lab_policy_cap"])
                self.assertEqual(result["result"], case["expected_boundary_result"])
                self.assertIn("not current CBK regulation", result["policy_context"])

    def test_missing_installment_is_not_inferred(self):
        result = evaluate_lab_policy({
            "nationality": "Kuwaiti",
            "monthly_net_salary_kwd": 1000,
            "existing_debt_monthly_kwd": 200,
            "loan_amount_requested_kwd": 5000,
        })
        self.assertFalse(result["computable"])
        self.assertEqual(result["result"], "not_computable")
        self.assertIn("does not estimate", result["not_computable_reason"])


if __name__ == "__main__":
    unittest.main()
