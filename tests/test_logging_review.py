import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(relative_path):
    return [json.loads(line) for line in (ROOT / relative_path).read_text(encoding="utf-8").splitlines() if line]


class LoggingAndReviewTests(unittest.TestCase):
    def test_decision_logs_have_expected_counts_and_schema(self):
        expected = {
            "outputs/baseline_decisions.jsonl": {"Approve": 21, "Refer": 18, "Decline": 21},
            "outputs/mitigated_decisions.jsonl": {"Approve": 22, "Refer": 27, "Decline": 11},
        }
        for path, counts in expected.items():
            records = read_jsonl(path)
            with self.subTest(path=path):
                self.assertEqual(len(records), 60)
                self.assertTrue(all(record["schema_version"] == "decision_log_v1" for record in records))
                actual = Counter(record["monitoring"]["output_recommendation"] for record in records)
                self.assertEqual(dict(actual), counts)
                self.assertTrue(all(record["record_class"] == "REAL_EVIDENCE" for record in records))

    def test_review_queue_membership_matches_routing(self):
        for variant in ("baseline", "mitigated"):
            decisions = read_jsonl(f"outputs/{variant}_decisions.jsonl")
            queue = read_jsonl(f"outputs/{variant}_review_queue.jsonl")
            expected_ids = {
                record["identity"]["applicant_id"]
                for record in decisions
                if record["routing"]["review_required"]
            }
            queue_ids = {record["applicant_id"] for record in queue}
            self.assertEqual(queue_ids, expected_ids)
            self.assertTrue(all(record["review_status"] == "PENDING" for record in queue))

    def test_decision_factors_do_not_use_protected_fields(self):
        protected = {"age", "gender", "nationality"}
        for path in ("outputs/baseline_decisions.jsonl", "outputs/mitigated_decisions.jsonl"):
            for record in read_jsonl(path):
                fields = {factor["field"] for factor in record["screening"]["decision_factors"]}
                self.assertFalse(fields & protected)


if __name__ == "__main__":
    unittest.main()
