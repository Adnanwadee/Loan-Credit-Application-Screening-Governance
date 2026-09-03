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

## Limitations

The dataset is synthetic, small, and not population-representative. It lacks real repayment/default labels, so equalized odds cannot be computed. Observed aggregate gaps and paired variations are descriptive diagnostics rather than causal discrimination findings.

## Conclusion

The project demonstrates evidence-derived fairness measurement and governance documentation. It should be treated as a controlled educational validation exercise, not as a production-ready lending approval system.
