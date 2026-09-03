# Mentor Acceptance Matrix

| Requirement | Status | Evidence |
| --- | --- | --- |
| Screening recommendations only | PASS | Outputs are recommendations, not final lending decisions. |
| Recommendation enum | PASS | Stored outputs use Approve, Refer, and Decline. |
| Model-reported confidence | PASS | Decision logs include confidence values. |
| Uncalibrated confidence limitation | PASS | Reports and explanations state confidence is not a probability. |
| Plain-language justification | PASS | Each stored decision includes a justification. |
| Explainability separated from hidden reasoning | PASS | Explanations are deterministic post-hoc records. |
| Decision JSONL logging | PASS | Baseline and mitigated JSONL decision logs are included. |
| Human review for Refer | PASS | Refer recommendations are routed to review. |
| Human review for Decline | PASS | Decline recommendations are routed to review. |
| Human review for low-confidence Approve | PASS | Approve below 0.75 routes to review. |
| Human review for technical failure | PASS | Routing code covers technical failures. |
| Gender fairness analysis | PASS | Gender rates and gaps are recomputed. |
| Age fairness analysis | PASS | Age-group rates and gaps are recomputed. |
| Nationality fairness analysis | PASS | Nationality rates and gaps are recomputed. |
| Mitigation attempt | PASS | Mitigated context removes direct protected attributes. |
| Controlled before-vs-after comparison | PASS | Comparison artifact is included. |
| Counterfactual diagnostic pairs | PASS | Nine controlled pairs are referenced. |
| Synthetic dataset limitation | PASS WITH DOCUMENTED LIMITATION | Dataset is synthetic and small. |
| Population representativeness | PASS WITH DOCUMENTED LIMITATION | No population representativeness claim is made. |
| Equalized-odds analysis | PASS WITH DOCUMENTED LIMITATION | Not computable without repayment/default ground truth. |
| No causal discrimination claim | PASS | Reports describe gaps as diagnostics. |
| No production deployment claim | PASS | Governance evidence is development lifecycle only. |
| watsonx.governance evidence | PASS | Factsheet/AI use case facts are documented. |
| Foundation-model asset semantics | PASS | Prompt Template references the watsonx.ai foundation model. |
| No standalone custom model claim | PASS | Governance evidence states no trained custom model exists. |
| Stored output preservation | PASS | Submitted outputs are copied from canonical stored evidence. |
| Provider replay avoidance | PASS | Submission build performs zero provider replay. |
| Secret hygiene | PASS | Only `.env.example` placeholders are included. |
| Reproducible local tests | PASS | Behavior-focused unittest suite is included. |
| Review queue evidence | PASS | Review queues contain 39 baseline and 38 mitigated records. |
| Baseline outcome distribution | PASS | {'Approve': 21, 'Refer': 18, 'Decline': 21, 'TECHNICAL_FAILURE': 0} |
| Mitigated outcome distribution | PASS | {'Approve': 22, 'Refer': 27, 'Decline': 11, 'TECHNICAL_FAILURE': 0} |
| A004 stored mitigated status | PASS | A004 remains a valid mitigated Refer recommendation in stored public evidence. |

# Additional Engineering Controls

- SHA-256 manifest is included as `SHA256SUMS.txt`.
- Live evaluation examples write to `runtime_outputs/` so submitted outputs are not overwritten.
- Packaging excludes raw full-run files, local credentials, virtual environments, caches, and repository workflow documents.
