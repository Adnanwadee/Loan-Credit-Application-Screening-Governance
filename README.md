# Loan/Credit Application Screening Tool with Governance

## Overview

This project implements an AI-assisted loan/credit application screening workflow with evidence logging, human review routing, fairness analysis, mitigation assessment, and watsonx.governance documentation. The system produces screening recommendations only: `Approve`, `Refer`, or `Decline`.

## Architecture

The local Python pipeline validates applicant records, builds deterministic arithmetic features, sends a constrained decision context to a watsonx.ai foundation model during live evaluation, validates the model response, binds evidence factors deterministically, logs each decision, routes mandatory human review, and computes fairness diagnostics from stored outputs.

## Application Input

The evaluation dataset contains 60 synthetic applications in `data/applications_60.json`. Each record includes applicant identity, demographics retained for audit, employment context, income, expenses, existing debt, requested loan amount, loan purpose, credit score, and previous defaults.

## Model Output

The model-facing contract accepts a JSON recommendation, model-reported confidence, plain-language justification, and declared key factor fields. Confidence is model-reported and uncalibrated; it is not a repayment probability or correctness estimate.

## Explainability

The project uses deterministic post-hoc explanation records with schema `explanation_v1`. Explanations bind declared factors to recorded applicant values and separate public explanation from hidden model reasoning.

## Human Review

Human review is required for every `Refer`, every `Decline`, every `Approve` below confidence 0.75, and technical/model-output failures. The stored baseline review queue contains 39 records; the mitigated review queue contains 38 records.

## Fairness Analysis

Fairness analysis recomputes outcome rates by gender, age group, and nationality. Approval-rate gaps greater than 10 percentage points are treated as investigation triggers, not proof of discrimination. Equalized odds is documented as not computable because repayment/default ground truth is unavailable.

## Mitigation

The mitigation removes direct protected attributes from the model-visible decision context while retaining those attributes for audit and fairness measurement. The observed assessment is `MIXED` because some approval gaps improved and others worsened or newly crossed the investigation threshold.

## watsonx.governance

Governance evidence is summarized in `evidence/Watsonx_Governance_Evidence.md`. The governed application asset is the tracked Prompt Template referencing the watsonx.ai-provided `llama-3-3-70b-instruct` foundation model; no separately trained custom model asset exists to register.

## Evaluation Results

Baseline outcomes: {'Approve': 21, 'Refer': 18, 'Decline': 21, 'TECHNICAL_FAILURE': 0}. Mitigated outcomes: {'Approve': 22, 'Refer': 27, 'Decline': 11, 'TECHNICAL_FAILURE': 0}. Stored evaluation artifacts are in `outputs/` and are not overwritten by the live-run examples below.

## Project Structure

- `data/`: synthetic evaluation records and controlled-pair reference data.
- `prompts/`: governed screening prompt.
- `src/`: screening, validation, review, logging, explainability, and fairness modules.
- `scripts/`: live evaluation runner.
- `outputs/`: stored baseline and mitigated evidence outputs.
- `reports/`: submission reports.
- `evidence/`: governance evidence index and verification summary.
- `tests/`: behavior-focused local regression tests.

## Setup

Tested with Python 3.11.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Populate `.env` with a valid watsonx.ai project configuration only when running a live evaluation.

## Run Local Tests

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

## Run a Live Evaluation

```powershell
.\.venv\Scripts\python.exe -B scripts\run_screening_evaluation.py --variant baseline --output-dir runtime_outputs\baseline
.\.venv\Scripts\python.exe -B scripts\run_screening_evaluation.py --variant mitigated --output-dir runtime_outputs\mitigated
```

The live commands write to `runtime_outputs/` so the submitted `outputs/` evidence remains unchanged.

## Known Limitations

The dataset is synthetic and small. It is not population-representative, has no real repayment/default ground truth, and cannot support causal discrimination conclusions or equalized-odds analysis. LAB_POLICY fixtures are assignment policy simulations only and are not represented as current CBK regulation or lender underwriting policy.

## Reports and Evidence

Read `reports/Bias_and_Fairness_Analysis.md`, `reports/AI_Governance_Report.md`, `reports/Responsible_AI_Bias_Summary.md`, `evidence/Evidence_Index.md`, and `evidence/Project_Verification_Summary.md` for the written submission package.
