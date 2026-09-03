"""Deterministic evidence binding for active governed screening.

The model proposes a screening recommendation and model-declared key factor
field names. This module binds exact observed values, conservative impact
labels, and canonical reviewer-facing factor relevance from the decision
context. It does not infer hidden model reasoning or restrict recommendations.
"""

MANDATORY_DIRECTIONAL_FIELDS = (
    "previous_defaults",
    "monthly_cash_surplus_before_new_loan",
)

ALLOWED_CONTEXTUAL_FIELDS = (
    "employment_status",
    "employer_type",
    "years_employed",
    "monthly_net_salary_kwd",
    "monthly_expenses_kwd",
    "existing_debt_monthly_kwd",
    "loan_amount_requested_kwd",
    "loan_purpose",
    "credit_score",
    "existing_debt_service_ratio",
    "expense_to_income_ratio",
    "requested_loan_to_annual_income",
)

PROTECTED_FIELDS = {"applicant_id", "age", "gender", "nationality"}

ALLOWED_KEY_FACTOR_FIELDS = MANDATORY_DIRECTIONAL_FIELDS + ALLOWED_CONTEXTUAL_FIELDS

FACTOR_KEYS = ("field", "observed_value", "impact", "reason")


def _require_context_field(decision_context, field):
    if field not in decision_context:
        raise KeyError(f"Missing decision context field: {field}")
    return decision_context[field]


def impact_for_field(decision_context, field):
    value = _require_context_field(decision_context, field)

    if field == "previous_defaults":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("previous_defaults must be numeric.")
        return "positive" if value == 0 else "negative"

    if field == "monthly_cash_surplus_before_new_loan":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("monthly_cash_surplus_before_new_loan must be numeric.")
        if value > 0:
            return "positive"
        if value < 0:
            return "negative"
        return "contextual"

    if field in ALLOWED_CONTEXTUAL_FIELDS:
        return "contextual"

    if field in PROTECTED_FIELDS:
        raise ValueError(f"Protected field cannot be bound as evidence: {field}")
    raise ValueError(f"Unsupported evidence field: {field}")


def canonical_reason(decision_context, field):
    impact = impact_for_field(decision_context, field)

    if field == "previous_defaults":
        if impact == "positive":
            return "No recorded prior-default adverse signal is present."
        return "Recorded previous defaults are adverse credit-history evidence, but they do not create an automatic deterministic outcome."

    if field == "monthly_cash_surplus_before_new_loan":
        if impact == "positive":
            return "Current supplied salary, expenses, and existing debt leave positive pre-loan monthly cash surplus; new-loan repayment is not projected because installment terms are unavailable."
        if impact == "negative":
            return "Current supplied salary, expenses, and existing debt leave negative pre-loan monthly cash surplus; this is adverse financial-capacity evidence without implying a regulatory threshold."
        return "Current supplied salary, expenses, and existing debt leave zero pre-loan monthly cash surplus; this is contextual evidence without a deterministic threshold."

    return "This supplied application field is usable contextual screening evidence. The model may consider it without treating it as a hard policy threshold."


def build_evidence_factor(decision_context, field):
    """Build one canonical factor using exact direct lookup for observed_value."""

    return {
        "field": field,
        "observed_value": _require_context_field(decision_context, field),
        "impact": impact_for_field(decision_context, field),
        "reason": canonical_reason(decision_context, field),
    }


def validate_selected_contextual_fields(selected_fields):
    return validate_selected_contextual_fields_for_allowed(selected_fields, ALLOWED_CONTEXTUAL_FIELDS)


def validate_key_factor_fields(key_factor_fields):
    return validate_key_factor_fields_for_allowed(key_factor_fields, ALLOWED_KEY_FACTOR_FIELDS)


def allowed_contextual_fields_for_context(decision_context):
    return [
        field
        for field in ALLOWED_CONTEXTUAL_FIELDS
        if field in decision_context and decision_context[field] is not None
    ]


def allowed_key_factor_fields_for_context(decision_context):
    return [
        field
        for field in ALLOWED_KEY_FACTOR_FIELDS
        if field in decision_context and decision_context[field] is not None
    ]


def validate_selected_contextual_fields_for_allowed(selected_fields, allowed_contextual_fields):
    errors = []
    if not isinstance(selected_fields, list):
        return [{"code": "invalid_selected_contextual_fields", "message": "selected_contextual_fields must be a list."}]

    allowed = tuple(allowed_contextual_fields)
    if len(selected_fields) > 3:
        errors.append({"code": "too_many_selected_contextual_fields", "message": "selected_contextual_fields may contain at most 3 fields."})

    seen = set()
    for index, field in enumerate(selected_fields):
        location = f"selected_contextual_fields[{index}]"
        if not isinstance(field, str):
            errors.append({"code": "invalid_selected_contextual_field", "message": f"{location} must be a string field name."})
            continue
        if field in seen:
            errors.append({"code": "duplicate_contextual_field", "message": f"{location} duplicates field: {field}"})
        seen.add(field)
        if field in PROTECTED_FIELDS or field in MANDATORY_DIRECTIONAL_FIELDS:
            errors.append({"code": "invalid_selected_contextual_field", "message": f"{location} is not allowed as contextual evidence: {field}"})
        elif field not in allowed:
            errors.append({"code": "invalid_selected_contextual_field", "message": f"{location} is not in screening_control.allowed_contextual_fields: {field}"})
    return errors


def validate_key_factor_fields_for_allowed(key_factor_fields, allowed_key_factor_fields):
    errors = []
    if not isinstance(key_factor_fields, list):
        return [{"code": "invalid_key_factor_fields", "message": "key_factor_fields must be a list."}]

    allowed = tuple(allowed_key_factor_fields)
    if len(key_factor_fields) < 1:
        errors.append({"code": "too_few_key_factor_fields", "message": "key_factor_fields must contain at least 1 field."})
    if len(key_factor_fields) > 3:
        errors.append({"code": "too_many_key_factor_fields", "message": "key_factor_fields may contain at most 3 fields."})

    seen = set()
    for index, field in enumerate(key_factor_fields):
        location = f"key_factor_fields[{index}]"
        if not isinstance(field, str):
            errors.append({"code": "invalid_key_factor_field", "message": f"{location} must be a string field name."})
            continue
        if field in seen:
            errors.append({"code": "duplicate_key_factor_field", "message": f"{location} duplicates field: {field}"})
        seen.add(field)
        if field in PROTECTED_FIELDS:
            errors.append({"code": "protected_key_factor_field", "message": f"{location} is protected or non-evidentiary: {field}"})
        elif field not in allowed:
            errors.append({"code": "invalid_key_factor_field", "message": f"{location} is not in screening_control.allowed_key_factor_fields: {field}"})
    return errors


def bind_decision_factors(decision_context, key_factor_fields):
    """Bind final project-schema factors exactly from model-declared fields."""

    errors = validate_key_factor_fields_for_allowed(
        key_factor_fields,
        allowed_key_factor_fields_for_context(decision_context),
    )
    if errors:
        raise ValueError(errors[0]["code"])

    return [build_evidence_factor(decision_context, field) for field in key_factor_fields]


def negative_supported_factor_count(decision_context):
    """Diagnostic count retained for evidence summaries, not routing."""

    count = 0
    if impact_for_field(decision_context, "previous_defaults") == "negative":
        count += 1
    if impact_for_field(decision_context, "monthly_cash_surplus_before_new_loan") == "negative":
        count += 1
    return count


def allowed_recommendations_for_context(decision_context):
    """Return the active screening recommendation enum.

    The foundation model may return any valid screening recommendation when
    the output is structurally valid and evidence-grounded.
    """

    return ("Approve", "Refer", "Decline")


def build_screening_control(decision_context):
    return {
        "mandatory_directional_evidence": {
            "previous_defaults_impact": impact_for_field(decision_context, "previous_defaults"),
            "monthly_cash_surplus_before_new_loan_impact": impact_for_field(decision_context, "monthly_cash_surplus_before_new_loan"),
        },
        "allowed_key_factor_fields": allowed_key_factor_fields_for_context(decision_context),
        "allowed_contextual_fields": allowed_contextual_fields_for_context(decision_context),
        "allowed_recommendations": list(allowed_recommendations_for_context(decision_context)),
        "recommendation_rule": "MODEL_MAY_SELECT_APPROVE_REFER_OR_DECLINE_WHEN_GROUNDED_IN_SUPPLIED_EVIDENCE",
    }


def build_final_screening_result(provider_response, decision_context):
    key_factor_fields = provider_response.get("key_factor_fields")
    if key_factor_fields is None:
        key_factor_fields = provider_response.get("selected_contextual_fields", [])
    factors = bind_decision_factors(decision_context, key_factor_fields)
    return {
        "applicant_id": provider_response.get("applicant_id"),
        "recommendation": provider_response.get("recommendation"),
        "confidence": provider_response.get("confidence"),
        "justification": provider_response.get("justification"),
        "decision_factors": factors,
    }
