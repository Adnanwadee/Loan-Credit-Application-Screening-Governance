import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from screening import screen_application


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def chat(self, messages):
        self.calls += 1
        return self.responses.pop(0)


class ScreeningRetryTests(unittest.TestCase):
    def test_invalid_first_response_retries_once(self):
        application = json.loads((ROOT / "data" / "applications_60.json").read_text(encoding="utf-8"))[0]
        valid = json.dumps({
            "applicant_id": "A001",
            "recommendation": "Approve",
            "confidence": 0.9,
            "justification": "The supplied credit score is 740, monthly cash surplus before the new loan is 700 KWD, and employment status is full-time employed.",
            "key_factor_fields": ["credit_score", "monthly_cash_surplus_before_new_loan", "employment_status"],
        })
        client = FakeClient(["not json", valid])
        result = screen_application(application, client, prompt_text="Return JSON.")
        self.assertEqual(client.calls, 2)
        self.assertEqual(result["status"], "VALID")
        self.assertTrue(result["retry_used"])
        self.assertFalse(result["initial_schema_valid"])

    def test_provider_exception_returns_technical_failure(self):
        def failing_client(messages):
            raise RuntimeError("offline")

        application = json.loads((ROOT / "data" / "applications_60.json").read_text(encoding="utf-8"))[0]
        result = screen_application(application, failing_client, prompt_text="Return JSON.")
        self.assertEqual(result["status"], "TECHNICAL_FAILURE")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["provider_error"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
