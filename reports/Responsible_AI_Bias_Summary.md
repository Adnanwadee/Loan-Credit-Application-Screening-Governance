# Responsible AI Bias Summary

## The Three Types of Bias in Financial-Services AI

**Historical bias** occurs when training or prompting data reflects past
discriminatory lending decisions, so the model reproduces them even when
they were wrong. Example: if a bank historically declined more applicants
from certain postcodes or employer categories due to past redlining-style
practices, a model trained or prompted on that pattern will keep declining
similar applicants today, regardless of their actual current creditworthiness.

**Representation bias** occurs when some applicant groups are
under-sampled in the evaluation or reference data, so the system's
behavior for that group is effectively untested. Example: if an
evaluation dataset contains mostly full-time salaried applicants and very
few self-employed or gig-economy applicants, the model's reliability for
self-employed applicants is unknown — errors there simply won't surface
in aggregate metrics because that group is a small share of the test set.

**Measurement / proxy bias** occurs when a feature that looks neutral is
actually correlated with a protected attribute, so it silently carries
the same signal even if the protected attribute itself is removed.
Example: "years at current address" or "years employed" can proxy for
age; "employer type" (e.g., government vs. private sector) can
correlate with nationality in a market like Kuwait's, where public-sector
employment skews toward Kuwaiti nationals.

## Fairness Metrics

Demographic parity asks whether outcome rates are similar across groups.
Equalized odds asks whether error rates are similar across groups
*conditional on actual outcomes* (true creditworthiness), which requires
ground-truth repayment/default labels. This project computes demographic
outcome-rate diagnostics only; equalized odds is documented as not
computable because no real repayment/default ground truth exists for the
synthetic dataset.

## Interpretability vs. Explainability

Interpretability describes how understandable the model or rules are
internally. Explainability describes how the system communicates a
decision after the fact. This project uses deterministic post-hoc
explanations that bind selected evidence fields to stored applicant
values, and explicitly separates those explanations from the model's
hidden reasoning — the explanation is not a guaranteed faithful account
of why the model produced its output.
