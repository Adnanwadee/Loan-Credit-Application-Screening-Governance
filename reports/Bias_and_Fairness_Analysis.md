# Bias and Fairness Analysis

## Objective

Evaluate whether stored screening recommendations show material approval-rate disparities across gender, age group, or nationality, and assess whether removing direct protected attributes from the model-visible context changed those diagnostics.

## Evaluation Dataset

The evaluation dataset contains 60 synthetic applications: 30 Female and 30 Male applicants, 30 Kuwaiti and 30 Expat applicants, and 20 applicants in each age group. The 12 gender/nationality/age-group intersection cells each contain five records.

## Methodology

The analysis uses stored decision logs, not new model calls. It recomputes outcome counts, group rates, approval-rate gaps, controlled similar-profile pair diagnostics, and before-vs-after mitigation changes. Approval-rate gaps greater than 10 percentage points are investigation triggers only.

## Baseline Outcome Distribution

Baseline outcomes: `{'Approve': 21, 'Refer': 18, 'Decline': 21, 'TECHNICAL_FAILURE': 0}` across 60 applications.

## Fairness Analysis by Gender

- gender: Female 26.67% vs Male 43.33%; absolute gap 16.67pp, triggered.

## Fairness Analysis by Age Group

- age_group: Under 30 20.00% vs Age 30-50 40.00%; absolute gap 20.00pp, triggered.
- age_group: Under 30 20.00% vs Over 50 45.00%; absolute gap 25.00pp, triggered.
- age_group: Age 30-50 40.00% vs Over 50 45.00%; absolute gap 5.00pp, not triggered.

## Fairness Analysis by Nationality

- nationality: Kuwaiti 50.00% vs Expat 20.00%; absolute gap 30.00pp, triggered.

## Investigation of Observed Disparities

The baseline gender, nationality, and selected age approval gaps exceed the investigation threshold. This is a descriptive fairness finding and does not establish intent, causality, illegal discrimination, or protected-attribute use by the model.

## Controlled Similar-Profile Diagnostic

The controlled-pair reference contains three gender pairs, three nationality pairs, and three age pairs. Pair identifiers are `CF_G1` through `CF_G3`, `CF_N1` through `CF_N3`, and `CF_A1` through `CF_A3`. These pairs support diagnostic inspection of paired output variation, not causal claims.

## Mitigation Attempt

The mitigation removed direct protected attributes from the model-visible context while preserving protected attributes in the audit record for fairness measurement and accountability.

## Before-vs-After Results

Mitigated outcomes: `{'Approve': 22, 'Refer': 27, 'Decline': 11, 'TECHNICAL_FAILURE': 0}` across 60 applications. The mitigation assessment result is `MIXED`.

## Fairness Finding

Material aggregate approval disparities require investigation in both stored runs. Mitigation validated structural protected-field removal but did not eliminate every aggregate approval-rate disparity.

## Regulatory Context: DBR Caps Not Computed on This Dataset

The CBK Debt Burden Ratio caps (40% expat / 50% Kuwaiti) are implemented
in `src/policy.py` as `LAB_POLICY`, but this calculation requires a
`proposed_monthly_installment_kwd` field that is **not present** in
`data/applications_60.json`. As a result, the LAB_POLICY DBR check has
not been run against the 60-application evaluation set, and the
nationality approval-rate gap reported below cannot yet be attributed to,
or ruled out from, legitimate DBR-cap differences. This is a known
limitation, not a finding: the question of whether the 30pp nationality
gap is explained by the regulatory cap difference remains open pending a
run with installment data populated.

## Composition Analysis Findings (from `outputs/fairness_investigation.json`)

For each triggered disparity, a composition analysis compared group
means on financial features. Key observations:

- **Nationality (30pp gap):** Kuwaiti applicants have a higher mean
  requested loan amount (16,700 vs 11,900 KWD), higher mean salary
  (1,493 vs 1,218 KWD), and higher mean credit score (689 vs 659) than
  Expat applicants in this dataset. These are legitimate compositional
  differences that plausibly contribute to the gap, but the analysis
  labels this only "insufficient evidence to classify as proxy" — it
  does not rule out disproportionate weighting of nationality itself.
- **Gender (16.67pp gap):** Male applicants have a higher mean requested
  loan amount and higher mean existing debt than Female applicants; other
  numeric features are close (credit score delta of ~1 point).
- **Age (20–25pp gaps):** Under-30 applicants have substantially shorter
  employment history (2.6 vs 8.75–18.2 years) and lower income than
  older groups — the largest compositional deltas of any grouping,
  consistent with a legitimate underwriting explanation.

All findings are classified `INSUFFICIENT_EVIDENCE_TO_CLASSIFY_AS_PROXY`:
the composition differences are real and directionally plausible, but
the dataset does not support a definitive proxy-vs-legitimate
determination without controlled-pair outcome analysis (see below) and,
for nationality specifically, without the DBR calculation described above.

## Limitations

The dataset is synthetic, small, and not population-representative. It lacks real repayment/default labels, so equalized odds cannot be computed. Observed aggregate gaps and paired variations are descriptive diagnostics rather than causal discrimination findings.

## Conclusion

The project demonstrates evidence-derived fairness measurement and governance documentation. It should be treated as a controlled educational validation exercise, not as a production-ready lending approval system.
