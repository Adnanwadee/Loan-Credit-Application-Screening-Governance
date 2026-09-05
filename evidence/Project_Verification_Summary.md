# Project Verification Summary

## Mentor Acceptance Matrix

| Mentor Requirement | Status | Repository Evidence |
| --- | --- | --- |
| Structured loan application intake | PASS | `data/applications_60.json` contains structured applicant, employment, demographic-audit, and financial fields. |
| AI-assisted loan screening pipeline | PASS | `src/screening.py` implements the structured screening workflow. |
| watsonx.ai foundation model used | PASS | The project uses `meta-llama/llama-3-3-70b-instruct` through the watsonx.ai client. |
| Recommendation output supports Approve / Refer / Decline | PASS | Prompt contract and stored decision logs use these recommendation values. |
| Confidence score returned | PASS | Canonical stored decisions include model-reported confidence. |
| Plain-language justification returned | PASS | Canonical accepted decisions include application-specific justification. |
| Exact structured JSON output schema defined before model output handling | PASS | `prompts/screening_v1.txt` defines `applicant_id`, `recommendation`, `confidence`, `key_factor_fields`, and `justification`. |
| Prompt tested on at least 10 applications | PASS | The governed screening workflow was evaluated across the complete 60-application dataset. |
| Decline recommendation must include specific application evidence | PASS | The prompt requires application-specific evidence, and stored accepted Decline records contain grounded justifications. |
| Separate explainability layer | PASS | `src/explainability.py` creates deterministic evidence-bound explanation records separate from the provider justification. |
| Explainability for all three decision types | PASS | Stored Approve, Refer, and Decline records contain structured explanation evidence. |
| Structured decision log | PASS | `outputs/baseline_decisions.jsonl` and `outputs/mitigated_decisions.jsonl` each contain 60 evaluation records. |
| Every application processed during evaluation logged | PASS | Both evaluation variants contain 60 decision-log records. |
| Human review for every Decline | PASS | `src/review.py` routes every valid Decline with `DECLINE_REQUIRES_REVIEW`. |
| Human review for Approve below 0.75 confidence | PASS | `src/review.py` routes low-confidence Approve decisions with `LOW_CONFIDENCE_APPROVE`. |
| Human review path available | PASS | Review queues preserve the application, AI recommendation, confidence, justification, explanation, factors, reason, and review status. |
| Full fairness dataset contains at least 30 applications | PASS | The final dataset contains 60 synthetic applications. |
| Balanced gender coverage | PASS | 30 Female / 30 Male. |
| Balanced nationality coverage | PASS | 30 Kuwaiti / 30 Expat. |
| Balanced age-group coverage | PASS | 20 Under 30 / 20 Age 30-50 / 20 Over 50. |
| Approval, referral, and decline rates by gender | PASS | Documented in `reports/Bias_and_Fairness_Analysis.md` and stored fairness metrics. |
| Approval, referral, and decline rates by age group | PASS | Documented in `reports/Bias_and_Fairness_Analysis.md` and stored fairness metrics. |
| Approval, referral, and decline rates by nationality | PASS | Documented in `reports/Bias_and_Fairness_Analysis.md` and stored fairness metrics. |
| Meaningful disparity investigation | PASS | Group composition and controlled similar-profile diagnostics are documented. |
| At least one fairness finding | PASS | Material aggregate approval-rate disparities were identified. |
| Investigate whether disparity may be explained by financial profiles | PASS | `outputs/fairness_investigation.json` compares relevant financial-profile composition across protected groups. |
| Investigate possible protected/proxy sensitivity | PASS WITH DOCUMENTED LIMITATION | Controlled similar-profile pairs were analyzed; no specific proxy relationship was causally established. |
| At least one mitigation attempted | PASS | Mitigated model-visible context removes gender, age, and nationality. |
| Re-run after mitigation | PASS | Mitigated results cover all 60 applications. |
| Mitigation documented before and after | PASS | `outputs/mitigation_assessment.json` and `outputs/baseline_vs_mitigated_comparison.json` document the comparison. |
| Mitigation result documented accurately | PASS | Final effect is `MIXED`; the project does not claim bias elimination. |
| Responsible-AI summary covering historical bias | PASS | `reports/Responsible_AI_Bias_Summary.md`. |
| Responsible-AI summary covering representation bias | PASS | `reports/Responsible_AI_Bias_Summary.md`. |
| Responsible-AI summary covering measurement/proxy bias | PASS | `reports/Responsible_AI_Bias_Summary.md`. |
| Financial-services example for each bias type | PASS | Included in `reports/Responsible_AI_Bias_Summary.md`. |
| Understand demographic parity | PASS | Outcome-rate comparison and its limitations are documented in the fairness and governance reports. |
| Understand equalized odds | PASS WITH DOCUMENTED LIMITATION | Equalized odds is described but not computed because repayment/default ground truth is unavailable. |
| Understand explainability vs interpretability | PASS | `reports/AI_Governance_Report.md` explains the distinction and foundation-model limitations. |
| Understand adverse-action concept | PASS WITH DOCUMENTED LIMITATION | The project documents the need for specific reasons and human review but does not claim a legally compliant notice generator. |
| Register/track the AI application in watsonx.governance | PASS | `evidence/Watsonx_Governance_Evidence.md` records the tracked AI Use Case and Prompt Template. |
| Governed prompt/model identity documented | PASS | Foundation model, publisher, Prompt Template, Approach, and version are recorded. |
| Factsheet / governance record contains intended-use context | PASS | Intended use and non-production boundaries are documented in the watsonx.governance record and repository evidence. |
| Factsheet / governance record contains model/prompt context | PASS | Model identity and governed prompt information are documented. |
| Factsheet / governance record contains fairness findings | PASS | Aggregate disparity and mixed mitigation findings are documented. |
| Factsheet / governance record contains limitations | PASS | Major data, fairness, explainability, confidence, DBR, and deployment limitations are documented. |
| Factsheet / governance record contains human-oversight expectations | PASS | Decline and low-confidence Approve review requirements are documented. |
| Basic input/output logging for future monitoring | PASS | Decision logs preserve inputs, outputs, validation, provenance, and review-routing fields for later batch comparison. |
| Governance Report included | PASS | `reports/AI_Governance_Report.md`. |
| Governance Report Section 1: Model Description | PASS | Model, inputs, outputs, derived features, validation, retry, logging, and provenance are documented. |
| Governance Report Section 2: Intended Use and Out-of-Scope Use | PASS | Intended and prohibited uses are explicitly documented. |
| Governance Report Section 3: Fairness Analysis | PASS | Protected-group outcome distributions and methodology are included. |
| Governance Report Section 4: Bias Finding | PASS | Material disparity, likely contributors, mitigation, and causal limitations are included. |
| Governance Report Section 5: Explainability Approach | PASS | Provider justification, deterministic explanation, and limitations are documented. |
| Governance Report Section 6: Human Oversight Design | PASS | Mentor-required and additional project review conditions are documented. |
| Governance Report Section 7: Known Limitations | PASS | Data, fairness, explainability, policy, monitoring, and deployment limitations are documented. |
| Governance Report Section 8: Recommendations | PASS | Required conditions before real-world deployment are documented. |

## Final Evaluation Summary

### Baseline Evaluation

- Applications: 60
- Accepted recommendations: 60
- Approve: 21
- Refer: 18
- Decline: 21
- Technical failures: 0
- Human-review queue: 39
- Controlled retry used: 4 applications

### Mitigated Evaluation

- Applications: 60
- Accepted recommendations: 60
- Approve: 22
- Refer: 27
- Decline: 11
- Technical failures: 0
- Human-review queue: 38
- Controlled retry used: 6 applications

## Final Fairness Summary

Baseline material approval-rate gaps include:

- Gender: 16.67 pp
- Nationality: 30.00 pp
- Under 30 vs Age 30-50: 20.00 pp
- Under 30 vs Over 50: 25.00 pp

The mitigation removed gender, age, and nationality from the model-visible context.

The observed fairness effect was:

> **MIXED**

The project does not claim that bias was eliminated.

It also does not claim that causal discrimination was proven.

Equalized odds was not computed because credible repayment/default ground truth is unavailable.

## Additional Engineering Controls

The implementation includes several controls beyond the minimum acceptance criteria:

- controlled retry for invalid provider output,
- structured response validation,
- protected-field exclusion from decision-factor explanations,
- deterministic evidence binding,
- separation of model justification from the explainability record,
- structured model and prompt provenance,
- reviewer acceptance and override workflow,
- controlled similar-profile pair diagnostics,
- SHA-256 submission manifest,
- behavior-focused local regression tests,
- environment-variable handling for watsonx.ai credentials,
- separation between submitted stored evidence and future `runtime_outputs/`.

## Final Project Position

The project satisfies the required controlled-development objectives for:

- AI-assisted screening,
- structured logging,
- explainability,
- fairness analysis,
- mitigation assessment,
- human oversight,
- watsonx.governance documentation.

The project remains a development-stage educational prototype.

It is not presented as a production-ready lending approval system, a legally compliant underwriting engine, or evidence of fairness for a real applicant population.
