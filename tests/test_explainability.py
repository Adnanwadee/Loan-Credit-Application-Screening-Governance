import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from explainability import validate_explanation


def read_first_decision(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8").splitlines()[0])


class ExplainabilityTests(unittest.TestCase):
    def test_stored_explanation_schema_is_valid(self):
        record = read_first_decision("outputs/baseline_decisions.jsonl")
        screening = dict(record["screening"], applicant_id=record["identity"]["applicant_id"])
        errors = validate_explanation(record["explainability"], screening)
        self.assertEqual(errors, [])
        self.assertEqual(record["explainability"]["schema_version"], "explanation_v1")
        self.assertIn("not hidden model reasoning", record["explainability"]["limitations"][0])

    def test_explanation_factors_match_screening_factors(self):
        record = read_first_decision("outputs/mitigated_decisions.jsonl")
        explanation_fields = [factor["field"] for factor in record["explainability"]["factors"]]
        screening_fields = [factor["field"] for factor in record["screening"]["decision_factors"]]
        self.assertEqual(explanation_fields, screening_fields)


if __name__ == "__main__":
    unittest.main()
