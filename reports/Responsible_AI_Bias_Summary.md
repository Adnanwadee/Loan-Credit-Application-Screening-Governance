# Responsible AI Bias Summary

AI-assisted lending is a high-impact use case because screening outcomes can materially affect a person's access to credit and financial opportunities. For this reason, a lending AI system should not be evaluated only on whether it produces plausible recommendations. It must also be examined for bias, explainability, auditability, and appropriate human oversight.

## Historical Bias

Historical bias occurs when historical data or past decision patterns already contain unfair or discriminatory treatment and an AI system reproduces those patterns.

**Financial-services example:** if a lender historically rejected applicants from certain neighborhoods more often for reasons unrelated to their actual financial risk, a model trained on those past decisions may learn and reproduce the same pattern.

The main risk is that historical data can encode previous human or institutional bias rather than objective creditworthiness.

## Representation Bias

Representation bias occurs when some applicant groups are underrepresented in the data used to evaluate or validate an AI system.

**Financial-services example:** if an evaluation dataset contains mostly full-time salaried applicants and very few self-employed applicants, overall results may appear acceptable while the system's behavior for self-employed applicants remains insufficiently tested.

In this project, the synthetic evaluation dataset was intentionally balanced across gender, nationality, and age groups to support group comparison. However, a balanced synthetic dataset is not the same as a representative real-world lending population.

## Measurement and Proxy Bias

Measurement bias occurs when a feature does not accurately measure the concept it is intended to represent. Proxy bias occurs when a seemingly neutral feature is correlated with a protected attribute and indirectly carries related information.

**Financial-services example:** variables such as years employed, employer type, or residential stability may correlate with a protected characteristic in a particular dataset. Removing the protected attribute itself therefore does not automatically guarantee that all related information has been removed.

In this project, possible proxy risk was investigated by comparing financial-profile composition across protected groups and by using controlled similar-profile pairs. The available evidence was not sufficient to establish that any specific neutral feature functions as a protected-attribute proxy.

## Project Relevance

These three bias types affect different parts of the AI lifecycle:

- historical bias concerns patterns inherited from prior decisions or data,
- representation bias concerns who is sufficiently represented in evaluation,
- measurement/proxy bias concerns how features may encode sensitive information indirectly.

The project therefore treats fairness analysis as an investigation process rather than a single pass/fail number. Observed group disparities are measured, possible contributors are investigated, a mitigation is tested, and the limitations of the evidence are documented.

The final project does not claim that fairness has been proven or that bias has been eliminated. Instead, it demonstrates how a lending AI system can be evaluated and governed more responsibly.
