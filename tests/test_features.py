import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features import compute_derived_features


class FeatureComputationTests(unittest.TestCase):
    def test_derived_features_are_arithmetic_only(self):
        result = compute_derived_features({
            "monthly_net_salary_kwd": 1000,
            "monthly_expenses_kwd": 250,
            "existing_debt_monthly_kwd": 150,
            "loan_amount_requested_kwd": 6000,
        })
        self.assertEqual(result["monthly_cash_surplus_before_new_loan"], 600)
        self.assertEqual(result["existing_debt_service_ratio"], 0.15)
        self.assertEqual(result["expense_to_income_ratio"], 0.25)
        self.assertEqual(result["requested_loan_to_annual_income"], 0.5)

    def test_zero_salary_keeps_denominator_ratios_uncomputed(self):
        result = compute_derived_features({
            "monthly_net_salary_kwd": 0,
            "monthly_expenses_kwd": 50,
            "existing_debt_monthly_kwd": 25,
            "loan_amount_requested_kwd": 1000,
        })
        self.assertIsNone(result["existing_debt_service_ratio"])
        self.assertIsNone(result["expense_to_income_ratio"])
        self.assertIsNone(result["requested_loan_to_annual_income"])
        self.assertEqual(result["monthly_cash_surplus_before_new_loan"], -75)


if __name__ == "__main__":
    unittest.main()
