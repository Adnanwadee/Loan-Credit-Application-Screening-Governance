# Watsonx Governance Evidence

This document summarizes the watsonx.governance evidence created for the loan/credit screening project.

The governance scope is the development lifecycle only.

It does not claim production deployment, regulatory approval, automated IBM fairness validation, or production monitoring.

## Governance Registration

| Field | Recorded Value |
| --- | --- |
| Region | Frankfurt |
| Inventory | Default Inventory |
| AI Use Case | Governed Loan/Credit Application Screening |
| Risk | High |
| Status | Development in progress |
| Development Workspace | Loan Credit Governance - Project 3 |
| Prompt Template | Loan Credit Screening - Final Governed Prompt |
| Task | Classification |
| Foundation Model | llama-3-3-70b-instruct |
| Publisher | Meta |
| Approach | Governed Loan Screening - Final V1/V2 |
| Version | 0.0.1 |
| Version Type | Experimental |
| Lifecycle Scope | Development |

## Governed Asset

This project uses an IBM-provided foundation model rather than a separately trained custom model.

The governed application asset is therefore the tracked Prompt Template associated with the watsonx.ai foundation model.

The tracked Prompt Template references:

`llama-3-3-70b-instruct`

No separately trained custom model asset exists in this project.

## AI Use Case and Factsheet Record

The watsonx.governance AI Use Case, tracked Prompt Template, and associated Factsheet record were populated to document the development-stage governance context of the application.

The governance information covers the main areas required for this project:

- intended use,
- project purpose,
- model and prompt identity,
- development lifecycle,
- synthetic evaluation context,
- fairness findings,
- mitigation approach,
- known limitations,
- human oversight expectations,
- non-production status.

The governance record is maintained in watsonx.governance.

The repository contains a textual summary of the governed configuration rather than claiming that a standalone exported Factsheet document is included.
Conceptually, this governance record serves a similar documentation purpose to a model card by recording the system's intended use, model and prompt identity, evaluation context, known limitations, fairness findings, and required human oversight.

## Intended Use Recorded for Governance

The system is intended for controlled AI-assisted screening of synthetic loan/credit applications.

The governed application produces non-final screening recommendations:

- Approve
- Refer
- Decline

The system is intended to support human decision-making rather than act as an autonomous lender.

## Prompt and Model Context

The governed prompt requires a structured JSON response containing:

- applicant identifier,
- screening recommendation,
- model-reported confidence,
- one to three key factor fields,
- application-specific plain-language justification.

The prompt also defines explicit boundaries.

The model must not:

- act as a final lending authority,
- invent loan terms,
- invent installment amounts,
- invent repayment outcomes,
- invent lender policy,
- invent current regulation,
- use protected attributes as screening reasons.

The model-reported confidence is documented as uncalibrated.

## Evaluation Data Context

The project uses 60 synthetic applications.

The evaluation dataset is balanced across:

- gender,
- age group,
- nationality.

The dataset is used for controlled development evaluation and fairness diagnostics.

It is not presented as representative of an actual production lending population.

The assignment-provided Expected Lean values for A001-A008 are retained as reference material only and are not treated as ground-truth credit labels.

## Fairness Findings

The baseline evaluation identified material aggregate approval-rate disparities across protected groups.

The strongest baseline disparity was:

- Kuwaiti approval rate: 50.00%
- Expat approval rate: 20.00%
- absolute gap: 30.00 percentage points

Material gender and age-group approval gaps were also observed.

The project does not interpret these disparities as proof of causal discrimination.

A structural mitigation removed:

- gender,
- age,
- nationality

from the model-visible decision context while preserving them for audit and fairness measurement.

The observed fairness effect was classified as:

> **MIXED**

Some approval-rate gaps improved, some worsened, and one remained unchanged.

The mitigation therefore removed direct protected-attribute exposure but did not demonstrate that bias had been eliminated.

## Human Oversight

The mentor-required review conditions are:

- Decline recommendations,
- Approve recommendations with confidence below 0.75.

The implementation additionally routes:

- Refer recommendations,
- technical/model-output failures.

These additional routes are project safeguards.

The AI recommendation remains advisory and is not treated as an autonomous final lending decision.

## Known Governance Limitations

The governance record and supporting reports document several limitations, including:

- synthetic evaluation data,
- small sample size,
- lack of population representativeness,
- no real repayment/default ground truth,
- inability to compute equalized odds,
- uncalibrated model confidence,
- post-hoc explanation limitations,
- inability to compute projected post-loan DBR without proposed installment information,
- assignment-specific policy assumptions,
- unresolved aggregate disparities,
- no proven proxy attribution,
- mixed mitigation results,
- no production deployment,
- no production fairness monitor,
- no independent lender/legal/model-risk validation.

## Lifecycle

The AI Use Case remains in the development lifecycle.

The project does not claim:

- validation approval,
- operational approval,
- production promotion,
- production deployment.

This is consistent with the project's intended status as a controlled development prototype.

## Monitoring Readiness

The project implements structured JSON Lines decision logging.

The decision log preserves information such as:

- application snapshot,
- protected audit attributes,
- model recommendation,
- model-reported confidence,
- justification,
- structured explainability,
- derived financial features,
- validation status,
- retry status,
- technical-failure status,
- human-review routing,
- model ID,
- prompt version,
- prompt SHA-256,
- screening version.

This provides traceable historical input/output evidence that could support later monitoring of:

- recommendation distributions,
- confidence distributions,
- input-distribution changes,
- technical-failure rates,
- retry behavior,
- protected-group outcome distributions.

This is development-stage monitoring readiness.

The project does not claim that an operational watsonx/OpenScale production drift or fairness monitor has been deployed.

## Governance Scope Boundary

The governance evidence does not claim:

- production readiness,
- regulatory compliance,
- legal approval,
- lender-policy approval,
- IBM automated fairness certification,
- IBM production monitoring,
- production deployment.

The purpose of the watsonx.governance integration is to demonstrate:

- AI Use Case tracking,
- governed Prompt Template tracking,
- lifecycle documentation,
- Factsheet-style governance documentation,
- fairness finding documentation,
- limitation documentation,
- human-oversight documentation,
- auditability of the AI-assisted screening workflow.
