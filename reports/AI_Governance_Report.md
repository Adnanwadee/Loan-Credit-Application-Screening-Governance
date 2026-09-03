# AI Governance Report

## 1. Model Description

The application is a governed loan/credit screening workflow using the watsonx.ai-provided `llama-3-3-70b-instruct` foundation model through a tracked Prompt Template. The local system validates JSON outputs and binds public evidence factors deterministically.

## 2. Intended Use and Out-of-Scope Use

Intended use is preliminary screening support for synthetic loan/credit applications. Out-of-scope uses include autonomous lending approval, regulatory eligibility determination, repayment/default prediction, production deployment, or use on real customers without further validation.

## 3. Fairness Analysis

Fairness analysis recomputes gender, age-group, and nationality outcome rates from stored decision logs. Baseline outcomes were `{'Approve': 21, 'Refer': 18, 'Decline': 21, 'TECHNICAL_FAILURE': 0}` and mitigated outcomes were `{'Approve': 22, 'Refer': 27, 'Decline': 11, 'TECHNICAL_FAILURE': 0}`.

## 4. Bias Finding

Approval-rate gaps above 10 percentage points are documented as investigation triggers. The project does not claim causal discrimination because the evidence is observational over a synthetic dataset and lacks repayment/default ground truth.

## 5. Explainability Approach

Explanations are constrained post-hoc records that bind selected evidence factors to recorded values. They are separate from hidden model reasoning and include explicit limitations around uncalibrated confidence and unavailable repayment ground truth.

## 6. Human Oversight Design

Human review is required for `Refer`, `Decline`, `Approve` below confidence 0.75, and technical/model-output failure. Review queues are stored as JSONL evidence and contain no reviewer action contamination.

## 7. Known Limitations

The dataset is synthetic, small, and not representative of a real applicant population. It has no real repayment/default outcomes, so equalized odds and default-prediction validation are not computable. LAB_POLICY fixtures are assignment policy simulations, not verified current CBK regulation.

## 8. Recommendations

Before any production consideration, use real governance-approved data, define lender policy with legal review, calibrate confidence or remove reliance on confidence, collect outcome labels for model validation, perform operational monitoring, and complete formal approval in watsonx.governance.
