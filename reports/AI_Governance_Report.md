# AI Governance Report

## 1. Model Description

This project implements an AI-assisted loan and credit application screening workflow using the watsonx.ai-provided `llama-3-3-70b-instruct` foundation model.

The system accepts structured loan-application information including:

- applicant identifier,
- employment status,
- employer type,
- years employed,
- monthly net salary,
- monthly expenses,
- existing monthly debt,
- requested loan amount,
- loan purpose,
- credit score,
- previous defaults.

The application dataset also contains gender, age, and nationality for audit and fairness analysis.

The local pipeline calculates deterministic financial indicators from supplied values, including:

- existing debt-service ratio,
- expense-to-income ratio,
- monthly cash surplus before the new loan,
- requested-loan-to-annual-income ratio.

The foundation model receives a constrained decision context and returns a structured JSON response containing:

- `applicant_id`
- `recommendation`
- `confidence`
- `key_factor_fields`
- `justification`

The allowed recommendation values are:

- Approve
- Refer
- Decline

The recommendation is produced by the foundation model.

The deterministic Python layer does not replace the model recommendation with a hidden rules-based underwriting decision.

After model inference, the local governance pipeline:

1. validates the provider response against the structured output contract,
2. checks that key-factor fields are permitted and grounded in available evidence,
3. converts accepted key factors into deterministic evidence bindings,
4. generates a separate structured explanation record,
5. writes the decision to a JSON Lines audit log,
6. applies human-review routing,
7. preserves model and prompt provenance,
8. computes fairness diagnostics from stored evaluation records.

One controlled retry is available when the first provider response fails the governed output contract. If an acceptable output still cannot be produced, the application becomes a technical/model-output failure and is routed for human review rather than receiving a fabricated recommendation.

The model-reported confidence value is uncalibrated.

It must not be interpreted as:

- probability of repayment,
- probability of default,
- probability that the recommendation is correct,
- a lender-approved credit-risk score.

The assignment-provided Expected Lean values for A001-A008 are retained only as behavioral references and are not treated as model inputs or ground-truth creditworthiness labels.

## 2. Intended Use and Out-of-Scope Use

### Intended Use

The intended use is preliminary AI-assisted screening of structured synthetic loan/credit applications in a controlled development environment.

The system is intended to:

- provide a non-final screening recommendation,
- provide a plain-language model justification,
- identify application-specific financial factors,
- produce a separate evidence-bound explanation,
- support a human reviewer,
- create auditable decision records,
- support fairness analysis,
- demonstrate responsible-AI governance practices.

The AI component is a decision-support tool.

It is not a final lending authority.

### Out-of-Scope Use

The system is not intended for:

- autonomous final loan approval,
- autonomous final loan rejection,
- replacing a qualified loan officer,
- legally binding credit decisions,
- regulatory eligibility determination,
- repayment/default prediction,
- production use with real applicants without further validation,
- treating model confidence as a calibrated risk probability,
- using the synthetic fairness results as evidence that a real population would be treated fairly.

The project also does not claim legal or regulatory compliance.

Any real lending use would require formal lender-policy, legal, regulatory, operational, security, and model-risk review.

## 3. Fairness Analysis

Fairness was evaluated using a synthetic dataset of 60 applications.

The protected-group distribution is:

- Gender: 30 Female / 30 Male
- Nationality: 30 Kuwaiti / 30 Expat
- Age:
  - 20 Under 30
  - 20 Age 30-50
  - 20 Over 50

The dataset contains 12 gender × nationality × age-group intersection cells, with five records in each cell.

The dataset is deliberately balanced for diagnostic comparison.

It is not representative of a production lending population.

Two stored evaluation variants were analyzed.

### Baseline

Gender, age, and nationality were available in the model-visible decision context.

The governed prompt instructed the model not to use protected attributes as screening reasons.

### Mitigated

Gender, age, and nationality were removed from the model-visible decision context.

They remained available separately for audit and fairness measurement.

The baseline and mitigated evaluations used the same 60-application dataset, foundation model, governed prompt, response contract, and recorded inference configuration.

The intended structural difference was removal of direct protected-attribute exposure in the mitigated variant.

An approval-rate gap greater than 10 percentage points was used as a project-level investigation trigger.

This is not a legal or regulatory threshold.

### Overall Outcomes

| Variant | Approve | Refer | Decline | Technical Failure |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 21 (35.00%) | 18 (30.00%) | 21 (35.00%) | 0 |
| Mitigated | 22 (36.67%) | 27 (45.00%) | 11 (18.33%) | 0 |

### Gender Outcomes

| Variant | Female Approve | Female Refer | Female Decline | Male Approve | Male Refer | Male Decline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 26.67% | 40.00% | 33.33% | 43.33% | 20.00% | 36.67% |
| Mitigated | 26.67% | 56.67% | 16.67% | 46.67% | 33.33% | 20.00% |

Approval-rate gap:

- Baseline: 16.67 pp
- Mitigated: 20.00 pp

### Nationality Outcomes

| Variant | Kuwaiti Approve | Kuwaiti Refer | Kuwaiti Decline | Expat Approve | Expat Refer | Expat Decline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 50.00% | 26.67% | 23.33% | 20.00% | 33.33% | 46.67% |
| Mitigated | 50.00% | 30.00% | 20.00% | 23.33% | 60.00% | 16.67% |

Approval-rate gap:

- Baseline: 30.00 pp
- Mitigated: 26.67 pp

### Age-Group Outcomes

Baseline approval rates:

- Under 30: 20.00%
- Age 30-50: 40.00%
- Over 50: 45.00%

Mitigated approval rates:

- Under 30: 25.00%
- Age 30-50: 35.00%
- Over 50: 50.00%

Material approval-rate gaps remain after mitigation.

Equalized odds was not calculated because the dataset does not contain real repayment/default or true-creditworthiness ground truth.

The complete outcome distributions and investigation methodology are documented in `reports/Bias_and_Fairness_Analysis.md`.

## 4. Bias Finding

The final fairness classification is:

> **MATERIAL AGGREGATE DISPARITY REQUIRES INVESTIGATION**

The strongest baseline disparity was observed by nationality:

- Kuwaiti approval rate: 50.00%
- Expat approval rate: 20.00%
- Absolute gap: 30.00 percentage points

Material disparities were also observed by gender and age group.

These results do not establish causal discrimination.

The investigation identified several possible contributors.

First, the synthetic groups differ in legitimate financial characteristics.

For example:

- nationality groups differ in average income and credit score,
- age groups differ materially in employment tenure and income,
- gender groups differ somewhat in debt and requested-loan composition.

These differences may contribute to the observed outcome distributions.

Second, gender, age, and nationality were directly available to the model in the baseline decision context.

Even though the prompt instructed the model not to use them as screening reasons, direct protected-attribute availability was treated as a governance risk.

The project therefore implemented a mitigation that removed gender, age, and nationality from the model-visible context while preserving those fields for fairness audit purposes.

The effect was mixed:

| Approval Gap | Baseline | Mitigated | Effect |
| --- | ---: | ---: | --- |
| Gender | 16.67 pp | 20.00 pp | Worsened |
| Nationality | 30.00 pp | 26.67 pp | Improved slightly |
| Under 30 vs Age 30-50 | 20.00 pp | 10.00 pp | Improved |
| Under 30 vs Over 50 | 25.00 pp | 25.00 pp | Unchanged |
| Age 30-50 vs Over 50 | 5.00 pp | 15.00 pp | Worsened |

The mitigation removed direct protected-attribute exposure but did not consistently reduce all observed disparities.

The project therefore does not claim that bias was eliminated.

Controlled similar-profile pair diagnostics were also performed.

The baseline contained one recommendation change across nine pairs.

The mitigated evaluation contained two recommendation changes across nine pairs.

The protected attributes under test were absent from the mitigated model-visible context for those mitigated comparisons, and the paired records also use different applicant IDs.

Therefore, these paired variations are treated as supplementary diagnostic evidence rather than causal proof of protected-attribute influence.

The available evidence was also insufficient to establish that any specific neutral feature functions as a protected-attribute proxy.

## 5. Explainability Approach

The system distinguishes between model justification and the separate explainability layer.

### Foundation-Model Justification

The foundation model returns a plain-language `justification` with each accepted recommendation.

The governed prompt requires the justification to use application-specific evidence rather than generic wording.

For Decline recommendations, the justification is expected to refer to concrete supplied or derived information such as:

- previous defaults,
- existing debt,
- current cash surplus,
- credit score,
- employment stability,
- requested loan relative to available income information.

The model is prohibited from inventing:

- loan terms,
- installments,
- interest or profit rates,
- repayment probabilities,
- unverified regulatory thresholds.

### Evidence-Bound Explainability Layer

The model also returns one to three `key_factor_fields`.

A separate deterministic component binds those factor names to actual recorded application or derived values.

The resulting explanation includes:

- factor name,
- observed value,
- impact classification,
- human-readable explanation,
- explicit limitations.

Protected fields are not accepted as decision factors in the explanation layer.

This provides a stronger audit trail because the public explanation is tied to recorded evidence rather than free-form model reasoning alone.

### Explainability Limitations

The foundation model itself is not interpretable in the way a simple decision tree or transparent ruleset would be.

The model justification is a post-hoc explanation and is not treated as a guaranteed reconstruction of the model's hidden internal reasoning.

The deterministic explanation layer improves traceability and evidence grounding, but it does not make the foundation model internally interpretable.

The system also does not expose hidden chain-of-thought.

## 6. Human Oversight Design

Human review is a structural governance control in the project.

The mentor-required review conditions are:

- every Decline recommendation,
- every Approve recommendation with confidence below 0.75.

The implementation adds two additional safeguards:

- every Refer recommendation,
- every technical/model-output failure.

Therefore:

- Decline is never treated as an autonomous final rejection,
- Refer is always escalated,
- low-confidence Approve is not treated as final,
- invalid model output never receives a fabricated recommendation.

The baseline review queue contains 39 records.

The mitigated review queue contains 38 records.

A review-queue record contains:

- full application snapshot,
- AI recommendation,
- model-reported confidence,
- plain-language justification,
- structured explanation,
- decision factors,
- review reason,
- review status.

The local review workflow supports:

- reviewer acceptance,
- reviewer override.

This design preserves human accountability and gives the reviewer enough evidence to challenge or override the model recommendation.

The AI recommendation therefore remains advisory within the project architecture.
Where an unfavorable credit decision would trigger adverse-action notice obligations under applicable law, a production system would require a legally reviewed applicant-facing notice that provides specific reasons for the decision. This prototype does not implement or claim to generate a legally compliant adverse-action notice; it only demonstrates the underlying requirement for specific, evidence-grounded reasons and accountable human review.

## 7. Known Limitations

The system has several important limitations.

1. **Synthetic evaluation data**  
   The evaluation contains only 60 synthetic applications.

2. **No population representativeness**  
   The dataset is intentionally balanced for diagnostic fairness comparison and does not represent a real lending population.

3. **Expected Lean is not ground truth**  
   Assignment-provided Expected Lean values for A001-A008 are behavioral references only.

4. **No real repayment/default outcomes**  
   The project cannot validate actual credit performance or default prediction.

5. **Equalized odds is unavailable**  
   Error-rate fairness cannot be calculated without credible ground-truth credit outcomes.

6. **Uncalibrated confidence**  
   Model-reported confidence is not a calibrated repayment, default, or correctness probability.

7. **Post-hoc explanation limitation**  
   A plausible explanation is not guaranteed to reflect the foundation model's internal reasoning.

8. **Projected post-loan DBR is unavailable**  
   The evaluation dataset does not contain proposed installment, term, or interest/profit-rate information.

9. **Assignment-specific DBR policy assumption**  
   The nationality-specific DBR values supplied in the project specification are retained only as `LAB_POLICY` and are not presented as independently verified current regulation.

10. **Aggregate disparity does not establish causality**  
    Group outcome differences are fairness diagnostics, not proof of discrimination.

11. **Controlled-pair analysis is not causal proof**  
    Similar-profile pairs use different applicant IDs and are interpreted as diagnostic sensitivity checks.

12. **Proxy bias is not proven**  
    No specific neutral feature was established as a protected-attribute proxy.

13. **Mitigation produced mixed results**  
    Removing direct protected attributes did not consistently reduce all observed approval-rate gaps.

14. **Foundation-model variability remains**  
    Different outputs can still occur even when direct protected attributes are not exposed.

15. **No production fairness validation**  
    The project does not include an IBM production fairness monitor or independent production model-risk validation.

16. **No production deployment**  
    The governed asset remains in the development lifecycle.

17. **No legal or regulatory approval**  
    The project has not been validated as compliant with real lender policy or applicable law.

## 8. Recommendations

Before the system could be considered for real lending use, the following conditions should be satisfied:

1. Replace the synthetic evaluation dataset with governance-approved and representative real applicant data.
2. Collect reliable repayment/default outcomes.
3. Define lender-approved underwriting and eligibility policy.
4. Perform formal legal and regulatory review for the intended jurisdiction.
5. Reassess the role of protected attributes and possible proxy variables.
6. Perform fairness testing using representative production-like data.
7. Use ground-truth-dependent fairness metrics when valid outcome labels become available.
8. Calibrate model confidence or remove decision reliance on uncalibrated confidence.
9. Perform independent model-risk and responsible-AI validation.
10. Establish operational input/output monitoring.
11. Monitor changes in applicant distributions and model behavior over time.
12. Repeat fairness evaluation after model or prompt changes.
13. Maintain human-review, override, and escalation procedures.
14. Establish an applicant review or appeal mechanism where required.
15. Maintain model, prompt, Factsheet, and governance lifecycle versioning.
16. Perform security, privacy, and access-control review for real customer information.
17. Obtain formal governance approval before any production deployment.

The current system should therefore be treated as a governed development prototype that demonstrates responsible loan-screening architecture, not as a production-ready lending decision system.
