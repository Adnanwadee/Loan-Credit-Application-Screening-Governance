# Responsible AI Bias Summary

Financial-services AI can inherit historical bias when past lending data reflects unequal access to credit, representation bias when applicant groups are under-sampled or simplified, and measurement/proxy bias when variables such as employment stability, location, income volatility, or credit-file thickness stand in for structural differences rather than individual repayment behavior.

Demographic parity asks whether outcome rates are similar across groups. Equalized odds asks whether error rates are similar across groups conditional on real outcomes, which requires ground-truth labels such as repayment/default. This project can compute demographic outcome-rate diagnostics but cannot compute equalized odds because it has no real repayment/default ground truth.

Interpretability describes how understandable the model or rules are internally. Explainability describes how the system communicates a decision or recommendation to users and reviewers. This project uses deterministic post-hoc explanations that bind selected evidence fields to stored applicant values and explicitly separates those explanations from hidden model reasoning.

Human oversight is implemented through mandatory review routing for uncertain, adverse, or failed outputs. Auditability is implemented through JSONL decision logs, review queues, prompt hashes, model identifiers, and reproducible fairness metrics. In a real lending context, adverse-action concepts would require legally reviewed, accurate, applicant-facing reasons; this project provides screening explanations only.

Model cards and AI Factsheets document intended use, limitations, data, metrics, governance ownership, and deployment status. The watsonx.governance evidence in this package records the governed Prompt Template and development lifecycle status without claiming production approval or automated IBM fairness monitoring.
