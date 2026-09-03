"""Deterministic explainability for governed screening results.

Explanations are constrained post-hoc summaries of model-declared key evidence
fields after deterministic value binding. They do not expose hidden model
reasoning and do not add lending thresholds, regulatory claims, or credit-score
categories.
"""

EXPLANATION_SCHEMA_VERSION = "explanation_v1"
EXPLANATION_KEYS = ("schema_version", "applicant_id", "recommendation", "summary", "factors", "limitations")
EXPLANATION_FACTOR_KEYS = ("field", "observed_value", "impact", "explanation")
ALLOWED_IMPACTS = {"positive", "negative", "contextual", "neutral"}

LIMITATIONS = (
    "This is a constrained post-hoc explanation of recorded screening evidence, not hidden model reasoning.",
    "Model-reported confidence is not a calibrated probability of repayment or correctness.",
    "No current CBK, lender-policy, repayment, or regulatory eligibility conclusion is inferred.",
    "LAB_POLICY is not evaluated when proposed_monthly_installment_kwd is absent.",
)


def _require_mapping(value, name):
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping.")
    return value


def _explanation_for_factor(factor):
    field = factor.get("field")
    impact = factor.get("impact")
    observed = factor.get("observed_value")

    if field == "previous_defaults":
        if impact == "positive":
            return f"Previous defaults: {observed}. This indicates no recorded prior-default adverse signal in the supplied application."
        if impact == "negative":
            return f"Previous defaults: {observed}. Recorded prior defaults are adverse credit-history evidence for a reviewer to consider."

    if field == "monthly_cash_surplus_before_new_loan":
        if impact == "positive":
            return f"Pre-loan monthly cash surplus: KWD {observed}. Supplied income, expenses, and existing debt leave cash available before any new loan installment."
        if impact == "negative":
            return f"Pre-loan monthly cash surplus: KWD {observed}. Supplied expenses and existing debt exceed supplied income before considering any new loan installment."
        return f"Pre-loan monthly cash surplus: KWD {observed}. Supplied income is fully consumed by expenses and existing debt before any new loan installment."

    if field == "credit_score":
        return f"Credit score: {observed}. The project treats this as higher-is-better ordinal credit evidence without assuming a FICO/CINET scale or legal cutoff."

    if field in {"existing_debt_service_ratio", "expense_to_income_ratio", "requested_loan_to_annual_income"}:
        return f"{field}: {observed}. This is a derived arithmetic relationship from supplied values, not a projected DBR or regulatory eligibility result."

    labels = {
        "employment_status": "Employment status",
        "employer_type": "Employer type",
        "years_employed": "Years employed",
        "monthly_net_salary_kwd": "Monthly net salary",
        "monthly_expenses_kwd": "Monthly expenses",
        "existing_debt_monthly_kwd": "Existing monthly debt",
        "loan_amount_requested_kwd": "Requested loan amount",
        "loan_purpose": "Loan purpose",
    }
    return f"{labels.get(field, field)}: {observed}. This supplied field provides application-specific context for human review of the screening recommendation."


def build_explanation(screening_result, decision_context=None):
    """Build a structured explanation from one final screening result."""

    result = _require_mapping(screening_result, "screening_result")
    factors = result.get("decision_factors")
    if not isinstance(factors, list) or not factors:
        raise ValueError("screening_result.decision_factors must be a non-empty list.")

    explanation_factors = []
    for factor in factors:
        factor = _require_mapping(factor, "decision factor")
        for key in ("field", "observed_value", "impact"):
            if key not in factor:
                raise ValueError(f"decision factor missing required key: {key}")
        if factor["impact"] not in ALLOWED_IMPACTS:
            raise ValueError(f"unsupported factor impact: {factor['impact']}")
        if decision_context is not None and factor["field"] in decision_context and factor["observed_value"] != decision_context[factor["field"]]:
            raise ValueError(f"decision factor observed_value is stale for field: {factor['field']}")
        explanation_factors.append(
            {
                "field": factor["field"],
                "observed_value": factor["observed_value"],
                "impact": factor["impact"],
                "explanation": _explanation_for_factor(factor),
            }
        )

    recommendation = result.get("recommendation")
    applicant_id = result.get("applicant_id")
    return {
        "schema_version": EXPLANATION_SCHEMA_VERSION,
        "applicant_id": applicant_id,
        "recommendation": recommendation,
        "summary": (
            f"Applicant {applicant_id} received a screening recommendation of {recommendation}. "
            "The factors below bind the model-declared key evidence fields to recorded application values."
        ),
        "factors": explanation_factors,
        "limitations": list(LIMITATIONS),
    }


def build_technical_failure_explanation(applicant_id, validation_errors):
    return {
        "schema_version": EXPLANATION_SCHEMA_VERSION,
        "applicant_id": applicant_id,
        "recommendation": None,
        "summary": (
            f"Applicant {applicant_id} has no accepted AI screening recommendation because the model output failed validation. "
            "The explanation is limited to the recorded technical failure evidence."
        ),
        "factors": [
            {
                "field": "validation_status",
                "observed_value": "TECHNICAL_FAILURE",
                "impact": "neutral",
                "explanation": "The model output did not pass the governed output contract, so no recommendation was fabricated.",
            }
        ],
        "limitations": list(LIMITATIONS),
        "validation_errors": list(validation_errors),
    }


def validate_explanation(explanation, screening_result):
    errors = []
    if not isinstance(explanation, dict):
        return [{"code": "explanation_not_object", "message": "Explanation must be an object."}]

    keys = set(explanation.keys())
    allowed_keys = set(EXPLANATION_KEYS) | {"validation_errors"}
    for key in EXPLANATION_KEYS:
        if key not in keys:
            errors.append({"code": "missing_explanation_key", "message": f"Missing explanation key: {key}"})
    for key in sorted(keys - allowed_keys):
        errors.append({"code": "unexpected_explanation_key", "message": f"Unexpected explanation key: {key}"})

    if explanation.get("schema_version") != EXPLANATION_SCHEMA_VERSION:
        errors.append({"code": "invalid_explanation_schema_version", "message": "Unexpected explanation schema version."})
    if explanation.get("applicant_id") != screening_result.get("applicant_id"):
        errors.append({"code": "explanation_applicant_mismatch", "message": "Explanation applicant_id does not match screening result."})
    if explanation.get("recommendation") != screening_result.get("recommendation"):
        errors.append({"code": "explanation_recommendation_mismatch", "message": "Explanation recommendation does not match screening result."})

    source_factors = screening_result.get("decision_factors", [])
    explanation_factors = explanation.get("factors")
    if not isinstance(explanation_factors, list):
        errors.append({"code": "invalid_explanation_factors", "message": "Explanation factors must be a list."})
        return errors
    if screening_result.get("final_status") != "TECHNICAL_FAILURE" and len(explanation_factors) != len(source_factors):
        errors.append({"code": "factor_count_mismatch", "message": "Explanation factor count must match decision factors."})

    for index, factor in enumerate(explanation_factors):
        if not isinstance(factor, dict):
            errors.append({"code": "explanation_factor_not_object", "message": f"factors[{index}] must be an object."})
            continue
        if set(factor.keys()) != set(EXPLANATION_FACTOR_KEYS):
            errors.append({"code": "invalid_explanation_factor_keys", "message": f"factors[{index}] has invalid keys."})
        if index < len(source_factors):
            source = source_factors[index]
            for key in ("field", "observed_value", "impact"):
                if factor.get(key) != source.get(key):
                    errors.append({"code": "factor_provenance_mismatch", "message": f"factors[{index}].{key} does not match decision factor."})
        if not isinstance(factor.get("explanation"), str) or not factor["explanation"].strip():
            errors.append({"code": "empty_factor_explanation", "message": f"factors[{index}].explanation must be non-empty."})

    if not isinstance(explanation.get("limitations"), list) or not explanation.get("limitations"):
        errors.append({"code": "missing_explanation_limitations", "message": "Explanation limitations must be present."})
    return errors
