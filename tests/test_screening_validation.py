import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evidence import build_final_screening_result, build_screening_control
from screening import build_decision_context, build_messages
from validation import validate_final_screening_result, validate_provider_output


class ScreeningValidationTests(unittest.TestCase):
    def test_provider_response_binds_to_final_schema(self):
        application = json.loads((ROOT / "data" / "applications_60.json").read_text(encoding="utf-8"))[0]
        context = build_decision_context(application)
        response = json.dumps({
            "applicant_id": "A001",
            "recommendation": "Approve",
            "confidence": 0.9,
            "justification": "The supplied credit score is 740, monthly cash surplus before the new loan is 700 KWD, and employment status is full-time employed.",
            "key_factor_fields": ["credit_score", "monthly_cash_surplus_before_new_loan", "employment_status"],
        })
        control = build_screening_control(context)
        provider_validation = validate_provider_output(response, "A001", context, control)
        self.assertTrue(provider_validation["valid"], provider_validation["errors"])
        final_result = build_final_screening_result(provider_validation["parsed"], context)
        final_validation = validate_final_screening_result(final_result, "A001", context)
        self.assertTrue(final_validation["valid"], final_validation["errors"])
        self.assertEqual(final_result["recommendation"], "Approve")
        self.assertEqual(len(final_result["decision_factors"]), 3)

    def test_messages_include_context_and_control(self):
        application = json.loads((ROOT / "data" / "applications_60.json").read_text(encoding="utf-8"))[0]
        context = build_decision_context(application)
        messages = build_messages("System prompt", context)
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertIn("Decision context JSON", messages[1]["content"])
        self.assertIn("Screening control JSON", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
