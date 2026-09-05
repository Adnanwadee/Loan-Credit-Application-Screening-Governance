# Evidence Index

This index identifies the primary implementation, evaluation, fairness, review, explainability, and governance evidence included in the repository.

## Screening System

- `src/screening.py`  
  Main screening workflow, decision-context construction, provider invocation, validation flow, and controlled retry handling.

- `src/validation.py`  
  Structured provider-response validation, protected-reasoning controls, and final-result validation.

- `src/evidence.py`  
  Deterministic evidence binding and allowed key-factor handling.

- `src/features.py`  
  Deterministic financial-feature derivation.

- `src/watsonx_client.py`  
  watsonx.ai client configuration and foundation-model connection.

- `prompts/screening_v1.txt`  
  Governed screening prompt, recommendation boundaries, protected-attribute restrictions, and exact JSON output contract.

## Evaluation Dataset

- `data/applications_60.json`  
  Final 60-application synthetic evaluation dataset.

- `data/evaluation_reference.csv`  
  Assignment Expected Lean references and controlled similar-profile pair definitions.

- `data/policy_sanity_cases.json`  
  Assignment-specific `LAB_POLICY` sanity cases separate from the main 60-application evaluation.

## Decision Logging

- `outputs/baseline_decisions.jsonl`  
  Baseline decision log containing 60 stored evaluation records.

- `outputs/mitigated_decisions.jsonl`  
  Mitigated decision log containing 60 stored evaluation records.

- `src/logging_layer.py`  
  Append-only JSON Lines logging, schema versioning, model/prompt provenance, monitoring fields, and protected audit-data separation.

## Human Review

- `outputs/baseline_review_queue.jsonl`  
  Baseline review queue containing 39 records.

- `outputs/mitigated_review_queue.jsonl`  
  Mitigated review queue containing 38 records.

- `src/review.py`  
  Human-review routing, review-record validation, reviewer acceptance, and reviewer override logic.

## Explainability

- Decision-log `screening.justification`  
  Foundation-model plain-language justification.

- Decision-log `explainability` block  
  Separate deterministic evidence-bound explanation using schema `explanation_v1`.

- `src/explainability.py`  
  Explanation generation, evidence binding, explanation limitations, and technical-failure explanation support.

- `outputs/sample_application_review.json`  
  A001-A008 reference comparison between assignment Expected Lean and stored screening outcomes.

## Fairness Analysis

- `outputs/baseline_fairness_metrics.json`  
  Baseline protected-group counts, rates, approval gaps, intersectional metrics, and investigation triggers.

- `outputs/mitigated_fairness_metrics.json`  
  Mitigated protected-group counts, rates, approval gaps, intersectional metrics, and investigation triggers.

- `outputs/fairness_investigation.json`  
  Group financial-profile composition analysis and fairness-investigation evidence.

- `outputs/baseline_vs_mitigated_comparison.json`  
  Baseline-versus-mitigated comparison and controlled similar-profile pair diagnostics.

- `reports/Bias_and_Fairness_Analysis.md`  
  Human-readable fairness report containing methodology, protected-group outcome distributions, disparity investigation, controlled-pair analysis, mitigation, and limitations.

## Mitigation

- `outputs/mitigation_assessment.json`  
  Final structural-mitigation assessment, approval-gap transitions, proxy-status assessment, and `MIXED` fairness-effect classification.

- `outputs/baseline_vs_mitigated_comparison.json`  
  Stored before-versus-after evaluation comparison.

## Governance

- `evidence/Watsonx_Governance_Evidence.md`  
  watsonx.governance AI Use Case, tracked Prompt Template, governed model/prompt identity, lifecycle, fairness context, limitations, monitoring readiness, and oversight evidence.

- `reports/AI_Governance_Report.md`  
  Final governance report containing the eight mentor-required sections.

## Responsible AI

- `reports/Responsible_AI_Bias_Summary.md`  
  Responsible-AI summary covering historical bias, representation bias, measurement/proxy bias, and financial-services examples.

## Validation and Verification

- `outputs/evaluation_validation_summary.json`  
  Final stored evaluation summary containing dataset balance, outcome counts, retry counts, review-queue counts, fairness status, model/prompt configuration, and stored-evidence provenance.

- `evidence/Project_Verification_Summary.md`  
  Mentor requirement-to-evidence verification matrix.

- `tests/`  
  Behavior-focused regression tests covering configuration, screening validation, retry behavior, explainability, fairness analysis, feature derivation, logging, review routing, and policy handling.

- `SHA256SUMS.txt`  
  SHA-256 manifest for repository submission files.

## Primary Written Deliverables

The primary human-readable submission documents are:

1. `reports/Responsible_AI_Bias_Summary.md`
2. `reports/Bias_and_Fairness_Analysis.md`
3. `reports/AI_Governance_Report.md`
4. `evidence/Watsonx_Governance_Evidence.md`
5. `evidence/Project_Verification_Summary.md`

The remaining implementation and output files provide supporting technical and audit evidence for those written deliverables.
