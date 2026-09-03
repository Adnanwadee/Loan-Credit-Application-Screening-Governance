import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from watsonx_client import CHAT_PARAMETERS, EXPECTED_MODEL_ID, load_effective_config


class ConfigurationAndDocumentationTests(unittest.TestCase):
    def test_readme_uses_runtime_output_examples(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Tested with Python 3.11", readme)
        self.assertIn("runtime_outputs", readme)
        self.assertIn("Run a Live Evaluation", readme)

    def test_governance_report_has_required_sections(self):
        text = (ROOT / "reports" / "AI_Governance_Report.md").read_text(encoding="utf-8")
        headings = [line.strip() for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, [
            "## 1. Model Description",
            "## 2. Intended Use and Out-of-Scope Use",
            "## 3. Fairness Analysis",
            "## 4. Bias Finding",
            "## 5. Explainability Approach",
            "## 6. Human Oversight Design",
            "## 7. Known Limitations",
            "## 8. Recommendations",
        ])

    def test_evidence_index_paths_exist(self):
        text = (ROOT / "evidence" / "Evidence_Index.md").read_text(encoding="utf-8")
        for category in (
            "Screening System",
            "Decision Logs",
            "Human Review",
            "Explainability",
            "Fairness Analysis",
            "Mitigation",
            "Governance",
            "Written Deliverables",
            "Validation",
        ):
            self.assertIn(f"## {category}", text)

    def test_environment_template_has_placeholders(self):
        template = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("WATSONX_APIKEY=replace-with-your-api-key", template)
        self.assertIn(f"WATSONX_MODEL_ID={EXPECTED_MODEL_ID}", template)
        self.assertIn("replace-with-your-project-id", template)

    def test_model_settings_are_fixed(self):
        self.assertEqual(CHAT_PARAMETERS["temperature"], 0)
        self.assertEqual(CHAT_PARAMETERS["top_p"], 1)
        self.assertEqual(CHAT_PARAMETERS["max_completion_tokens"], 512)
        config = load_effective_config(ROOT)
        self.assertIn("api_key_present", config)
        self.assertNotIn("api_key", config)

    def test_validation_summary_records_no_replay(self):
        summary = json.loads((ROOT / "outputs" / "evaluation_validation_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["phase_status"], "PASS")
        self.assertEqual(summary["new_provider_calls"], 0)
        self.assertFalse(summary["provider_replay"])
        self.assertFalse(summary["a004_mitigated_status"]["technical_failure"])


if __name__ == "__main__":
    unittest.main()
