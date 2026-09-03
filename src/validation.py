"""Validation for the active provider and final screening contracts."""

import json
import re

from evidence import (
    ALLOWED_CONTEXTUAL_FIELDS,
    ALLOWED_KEY_FACTOR_FIELDS,
    FACTOR_KEYS,
    PROTECTED_FIELDS,
    allowed_key_factor_fields_for_context,
    build_evidence_factor,
    impact_for_field,
    validate_key_factor_fields_for_allowed,
)


PROVIDER_KEYS = (
    "applicant_id",
    "recommendation",
    "confidence",
    "key_factor_fields",
    "justification",
)
FINAL_KEYS = (
    "applicant_id",
    "recommendation",
    "confidence",
    "justification",
    "decision_factors",
)
RECOMMENDATIONS = {"Approve", "Refer", "Decline"}
IMPACTS = {"positive", "negative", "contextual"}

_DIGIT = re.compile(r"\d")
_PROTECTED_WORDS = re.compile(r"\b(gender|age|nationality|female|male|kuwaiti|expat)\b", re.IGNORECASE)
_EVIDENCE_TERM = re.compile(
    r"\b("
    r"employment_status|employment\s+status|employment|employer_type|employer\s+type|employer|years_employed|years\s+employed|tenure|"
    r"monthly_net_salary_kwd|monthly\s+net\s+salary|monthly\s+salary|monthly_expenses_kwd|monthly\s+expenses|"
    r"existing_debt_monthly_kwd|existing\s+monthly\s+debt|debt|loan_amount_requested_kwd|requested\s+loan\s+amount|loan\s+amount|"
    r"loan_purpose|loan\s+purpose|credit_score|credit\s+score|credit\s+evidence|"
    r"existing_debt_service_ratio|existing\s+debt\s+service\s+ratio|debt\s+service\s+ratio|"
    r"expense_to_income_ratio|expense[-\s]+to[-\s]+income\s+ratio|requested_loan_to_annual_income|"
    r"requested\s+loan\s+to\s+annual\s+income\s+ratio|previous\s+defaults?|prior[-\s]+defaults?|cash\s+surplus|cash\s+flow|income|expenses|salary"
    r")\b",
    re.IGNORECASE,
)
_UNSUPPORTED_PATTERNS = (
    (
        "unsupported_threshold_or_regulatory_claim",
        re.compile(
            r"\b(?:approval|decline|credit|lender|bank|regulatory|legal)?\s*threshold\b"
            r"|\b(regulatory|regulation|CBK|central\s+bank|law|legal\s+limit|LAB_POLICY|projected\s+DBR|post[-\s]+loan\s+DBR)\b"
            r"|\b(loan\s+term|interest\s+rate|profit\s+rate|installment)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "autonomous_final_decision_claim",
        re.compile(
            r"\b(final|legally\s+final|autonomous|automatic)\s+(?:approval|rejection|decline|decision)\b"
            r"|\bloan\s+(?:is|must\s+be|will\s+be)\s+(?:approved|rejected|declined)\b"
            r"|\bapplicant\s+(?:is|must\s+be|will\s+be)\s+(?:approved|rejected|declined)\b",
            re.IGNORECASE,
        ),
    ),
)
_REPAYMENT_CAPACITY_TERMS = re.compile(
    r"\b(?:ability|capacity)\s+to\s+(?:repay|afford|service)\b"
    r"|\brepayment\s+capacity\b",
    re.IGNORECASE,
)
_RISK_OR_UNCERTAINTY_TERMS = re.compile(
    r"\b("
    r"raises?\s+concerns?|concerns?\s+about|uncertainty|uncertain|"
    r"may|might|could|potential|risk|strain|borderline|"
    r"further\s+(?:review|assessment)|assess|ensure|impact|warrants?\s+referral"
    r")\b",
    re.IGNORECASE,
)
_AFFIRMATIVE_REPAYMENT_CAPACITY = re.compile(
    r"\b(?:has|shows|demonstrates|indicates|suggests)\s+(?:a\s+)?"
    r"(?:(?:positive|strong|good|sufficient|adequate)\s+)?"
    r"(?:ability|capacity)\s+to\s+(?:repay|afford|service)\b"
    r"|\b(?:positive|strong|good|sufficient|adequate)\s+"
    r"(?:ability|capacity)\s+to\s+(?:repay|afford|service)\b"
    r"|\b(?:has|shows|demonstrates|indicates|suggests)\s+repayment\s+capacity\b",
    re.IGNORECASE,
)
_DEFINITIVE_REPAYMENT_OR_DEFAULT = re.compile(
    r"\b(?:can|cannot|can't|will|would|is\s+able\s+to|is\s+unable\s+to|"
    r"will\s+be\s+able\s+to|will\s+not\s+be\s+able\s+to)\s+"
    r"(?:repay|afford|service)\s+(?:the\s+)?(?:new\s+)?loan\b"
    r"|\brepayment\s+(?:will|would|is|appears|seems)\s+"
    r"(?:be\s+)?(?:reliable|unreliable|likely|unlikely|probable|improbable|successful|unsuccessful)\b"
    r"|\b(?:repayment|default)\s+(?:probability|guarantee|outcome)\b"
    r"|\bprobability\s+of\s+(?:default|repayment)\b"
    r"|\b(?:will|would)\s+(?:repay|default)\b",
    re.IGNORECASE,
)
_PROJECTED_LOAN_TERMS_OR_AFFORDABILITY = re.compile(
    r"\b(?:projected|post[-\s]+loan|new[-\s]+loan)\s+"
    r"(?:affordability|repayment|dbr|debt[-\s]+burden)\b"
    r"|\b(?:loan|application)\s+(?:is|appears|seems)\s+"
    r"(?:affordable|unaffordable)\b",
    re.IGNORECASE,
)
_CASH_OR_INCOME_PAYMENT_SUFFICIENCY = re.compile(
    r"\b(?:has|shows|demonstrates|indicates|suggests)\s+"
    r"(?:sufficient|insufficient|adequate|inadequate|enough|comfortable)\s+"
    r"(?:income|cash|surplus|funds?|cash\s+flow|affordability)\s+"
    r"(?:to|for)\s+(?:repay|repayment|afford|service|meet|manage|handle|cover)\b"
    r"|"
    r"\b(?:sufficient|insufficient|adequate|inadequate|enough|comfortable)\s+"
    r"(?:income|cash|surplus|funds?|cash\s+flow|affordability)\s+"
    r"(?:to|for)\s+(?:repay|repayment|afford|service|meet|manage|handle|cover)\b"
    r"|\b(?:income|cash|surplus|funds?|cash\s+flow|monthly\s+cash\s+surplus)\b"
    r"[^.!?]{0,80}\b(?:sufficient|insufficient|adequate|inadequate|enough|comfortable)\b"
    r"[^.!?]{0,80}\b(?:repay|afford|service|meet|manage|handle|cover|"
    r"payments?|obligations?|installments?)\b"
    r"|\b(?:may\s+not\s+be|not\s+be|is\s+not|is|appears|seems)\s+"
    r"(?:sufficient|insufficient|adequate|inadequate|enough|comfortable)\s+"
    r"(?:to|for)\s+(?:cover|handle|meet|manage|service)\s+"
    r"(?:the\s+)?(?:new\s+|additional\s+)?(?:loan\s+)?"
    r"(?:payments?|obligations?|installments?)\b",
    re.IGNORECASE,
)
_HUMAN_REVIEW_ROUTING_LANGUAGE = re.compile(
    r"\b(?:no\s+)?(?:human|manual)\s+(?:assessment|review)\b[^.!?]{0,80}\b"
    r"(?:required|not\s+required|needed|not\s+needed|necessary|not\s+necessary|"
    r"unnecessary|optional|appropriate|not\s+appropriate|inappropriate|"
    r"should\s+happen|should\s+not\s+happen|may\s+be\s+skipped|can\s+be\s+skipped|"
    r"skipped|bypassed|skip|bypass)\b"
    r"|\b(?:required|not\s+required|needed|not\s+needed|necessary|not\s+necessary|"
    r"unnecessary|optional|appropriate|not\s+appropriate|inappropriate|"
    r"should\s+happen|should\s+not\s+happen|may\s+be\s+skipped|can\s+be\s+skipped|"
    r"skipped|bypassed|skip|bypass)\b[^.!?]{0,80}\b"
    r"(?:human|manual)\s+(?:assessment|review)\b",
    re.IGNORECASE,
)
_PROTECTED_REASONING = re.compile(
    r"\b(?:because|due\s+to|based\s+on|given|as)\s+(?:the\s+)?(?:gender|age|nationality|female|male|kuwaiti|expat)\b"
    r"|\b(?:gender|age|nationality|female|male|kuwaiti|expat)\b[^.!?]{0,80}\b(?:risk|creditworthy|approve|decline|refer|safer|riskier)\b",
    re.IGNORECASE,
)


def _error(code, message):
    return {"code": code, "message": message}


def _parse_json(raw_output):
    if not isinstance(raw_output, str):
        return None, [_error("not_string", "Model output must be a string.")]
    stripped = raw_output.strip()
    if stripped.startswith("```"):
        return None, [
            _error("invalid_json", "Model output is not exact parseable JSON: markdown/code fence prefix."),
            _error("markdown_code_fence", "Model output uses a markdown/code fence instead of raw JSON."),
        ]
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return None, [_error("invalid_json", f"Model output is not exact parseable JSON: {exc.msg}")]
    return parsed, []


def _key_errors(parsed, required_keys):
    errors = []
    actual = set(parsed.keys())
    required = set(required_keys)
    for key in sorted(required - actual):
        errors.append(_error("missing_top_level_key", f"Missing top-level key: {key}"))
    for key in sorted(actual - required):
        errors.append(_error("unexpected_top_level_key", f"Unexpected top-level key: {key}"))
    return errors


def _confidence_errors(confidence):
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return [_error("invalid_confidence_type", "confidence must be a non-boolean JSON number.")]
    if confidence < 0.0 or confidence > 1.0:
        return [_error("confidence_out_of_range", "confidence must be between 0.0 and 1.0.")]
    return []


def _sentence_count(text):
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def _normalized_text(text):
    return re.sub(r"\s+", " ", text.lower().replace("–", "-").replace("—", "-")).strip()


def _sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _available_numeric_values(decision_context):
    values = []
    for value in decision_context.values():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            values.append(float(value))
            if abs(value) <= 10:
                values.append(float(value) * 100.0)
    return values


def _numeric_claims(justification):
    claims = []
    numeric_pattern = re.compile(
        r"(?<![A-Za-z])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
    )
    for match in numeric_pattern.finditer(justification):
        raw = match.group(0)
        is_percent = raw.endswith("%")
        normalized = raw.rstrip("%").replace(",", "")
        try:
            value = float(normalized)
        except ValueError:
            continue
        claims.append({"raw": raw, "value": value, "is_percent": is_percent})
    return claims


def _numeric_claim_is_grounded(claim, available):
    candidate_values = [claim["value"]]
    if claim["is_percent"]:
        candidate_values.append(claim["value"] / 100.0)
    for candidate in candidate_values:
        for value in available:
            tolerance = max(0.01, abs(value) * 0.001)
            if abs(candidate - value) <= tolerance:
                return True
    return False


def _numeric_claim_errors(justification, decision_context):
    if decision_context is None:
        return []
    claims = _numeric_claims(justification)
    if not claims:
        return []
    available = _available_numeric_values(decision_context)
    errors = []
    for claim in claims:
        if not _numeric_claim_is_grounded(claim, available):
            errors.append(_error("unsupported_numeric_claim", f"numeric claim is not grounded in supplied or derived evidence: {claim['raw']}"))
    return errors


def _unsupported_affordability_errors(justification):
    """Reject unsupported repayment conclusions without blocking risk language.

    The prompt forbids invented affordability, repayment, installment, and
    default-probability conclusions. It still allows grounded screening-risk
    uncertainty, including concern about whether more debt is appropriate.
    """

    for sentence in _sentences(justification):
        normalized = _normalized_text(sentence)
        if _PROJECTED_LOAN_TERMS_OR_AFFORDABILITY.search(normalized):
            return [_error("unsupported_affordability_claim", "justification contains an unsupported semantic claim.")]
        if _DEFINITIVE_REPAYMENT_OR_DEFAULT.search(normalized):
            return [_error("unsupported_affordability_claim", "justification contains an unsupported semantic claim.")]
        if _CASH_OR_INCOME_PAYMENT_SUFFICIENCY.search(normalized) and not _RISK_OR_UNCERTAINTY_TERMS.search(normalized):
            return [_error("unsupported_affordability_claim", "justification contains an unsupported semantic claim.")]
        if _AFFIRMATIVE_REPAYMENT_CAPACITY.search(normalized):
            return [_error("unsupported_affordability_claim", "justification contains an unsupported semantic claim.")]
        if _REPAYMENT_CAPACITY_TERMS.search(normalized) and not _RISK_OR_UNCERTAINTY_TERMS.search(normalized):
            return [_error("unsupported_affordability_claim", "justification contains an unsupported semantic claim.")]
    return []


def _previous_default_semantics(normalized):
    no_default_patterns = (
        r"\bno\s+(?:recorded\s+)?(?:previous|prior)[-\s]+defaults?\b",
        r"\bno\s+history\s+of\s+(?:previous\s+|prior\s+)?defaults?\b",
        r"\babsence\s+of\s+(?:previous|prior)[-\s]+defaults?\b",
        r"\bwithout\s+(?:any\s+)?(?:recorded\s+)?(?:previous|prior)[-\s]+defaults?\b",
        r"\bzero\s+(?:previous|prior)[-\s]+defaults?\b",
        r"\bno\s+recorded\s+prior[-\s]+default\s+adverse\s+signal\b",
    )
    present_default_patterns = (
        r"\bhas\s+(?:a\s+)?(?:history\s+of\s+)?(?:(?:\d+|one|two|several|multiple)\s+)?(?:previous|prior)[-\s]+defaults?\b",
        r"\b(?:record|application)\s+(?:shows|has|contains)\s+(?:(?:\d+|one|two|several|multiple)\s+)?(?:previous|prior)[-\s]+defaults?\b",
        r"\bhistory\s+of\s+(?!no\s)(?:(?:\d+|one|two|several|multiple)\s+)?(?:previous\s+|prior\s+)?defaults?\b",
        r"\b(?:previous|prior)[-\s]+defaults?\s+(?:are\s+)?present\b",
        r"\b(?:previous|prior)[-\s]+default\s+(?:is\s+)?recorded\b",
        r"\brecorded\s+prior[-\s]+default\s+adverse\s+signal\b",
    )
    no_default = any(re.search(pattern, normalized) for pattern in no_default_patterns)
    present_default = any(re.search(pattern, normalized) for pattern in present_default_patterns)
    if no_default:
        present_default = False
    return {"no_default": no_default, "present_default": present_default}


def _mandatory_evidence_contradiction_errors(justification, decision_context):
    errors = []
    normalized = _normalized_text(justification)

    previous_defaults_impact = impact_for_field(decision_context, "previous_defaults")
    previous_default_semantics = _previous_default_semantics(normalized)
    if previous_defaults_impact == "negative" and previous_default_semantics["no_default"]:
        errors.append(_error("mandatory_evidence_contradiction", "justification contradicts previous-default evidence."))
    if previous_defaults_impact == "positive" and previous_default_semantics["present_default"]:
        errors.append(_error("mandatory_evidence_contradiction", "justification contradicts previous-default evidence."))

    cash_impact = impact_for_field(decision_context, "monthly_cash_surplus_before_new_loan")
    has_positive_cash = "positive pre-loan cash position" in normalized
    has_negative_cash = "negative pre-loan cash position" in normalized
    if cash_impact == "positive" and has_negative_cash:
        errors.append(_error("mandatory_evidence_contradiction", "justification contradicts cash-position evidence."))
    if cash_impact == "negative" and has_positive_cash:
        errors.append(_error("mandatory_evidence_contradiction", "justification contradicts cash-position evidence."))
    if cash_impact == "contextual" and (has_positive_cash or has_negative_cash):
        errors.append(_error("mandatory_evidence_contradiction", "justification contradicts neutral cash-position evidence."))

    return errors


def _negative_mandatory_acknowledgement_errors(justification, decision_context):
    errors = []
    normalized = _normalized_text(justification)

    previous_defaults_impact = impact_for_field(decision_context, "previous_defaults")
    has_prior_default_adverse_signal = re.search(
        r"\brecorded\s+prior[-\s]+default\s+adverse\s+signal\b",
        normalized,
    )
    if previous_defaults_impact == "negative" and not has_prior_default_adverse_signal:
        errors.append(
            _error(
                "missing_negative_mandatory_evidence_acknowledgement",
                "justification must acknowledge negative previous-default evidence.",
            )
        )

    cash_impact = impact_for_field(decision_context, "monthly_cash_surplus_before_new_loan")
    has_negative_cash_position = "negative pre-loan cash position" in normalized
    if cash_impact == "negative" and not has_negative_cash_position:
        errors.append(
            _error(
                "missing_negative_mandatory_evidence_acknowledgement",
                "justification must acknowledge negative pre-loan cash-position evidence.",
            )
        )

    return errors


def justification_errors(justification, decision_context=None):
    errors = []
    if not isinstance(justification, str) or not justification.strip():
        return [_error("empty_justification", "justification must be a non-empty string.")]
    if len(justification) > 900:
        errors.append(_error("justification_too_long", "justification must be concise enough for review."))
    if _PROTECTED_WORDS.search(justification):
        errors.append(_error("protected_attribute_in_justification", "justification must not use protected attributes or values as screening reasons."))
    if _PROTECTED_REASONING.search(justification):
        errors.append(_error("protected_attribute_reasoning", "justification contains protected-attribute reasoning."))
    if _HUMAN_REVIEW_ROUTING_LANGUAGE.search(justification):
        errors.append(_error("human_review_routing_language", "justification must not describe human-review routing necessity."))
    errors.extend(_unsupported_affordability_errors(justification))
    for code, pattern in _UNSUPPORTED_PATTERNS:
        if pattern.search(justification):
            errors.append(_error(code, "justification contains an unsupported semantic claim."))
    if decision_context is not None:
        errors.extend(_mandatory_evidence_contradiction_errors(justification, decision_context))
        errors.extend(_numeric_claim_errors(justification, decision_context))
    return errors


def _basic_screening_errors(parsed, expected_applicant_id, decision_context=None):
    errors = []
    applicant_id = parsed.get("applicant_id")
    if not isinstance(applicant_id, str) or not applicant_id:
        errors.append(_error("invalid_applicant_id", "applicant_id must be a non-empty string."))
    elif applicant_id != expected_applicant_id:
        errors.append(_error("applicant_id_mismatch", "applicant_id does not match supplied applicant."))

    recommendation = parsed.get("recommendation")
    if recommendation not in RECOMMENDATIONS:
        errors.append(_error("invalid_recommendation", "recommendation must be Approve, Refer, or Decline."))
    elif recommendation == "Decline" and decision_context is not None:
        justification = parsed.get("justification")
        if not isinstance(justification, str) or not _EVIDENCE_TERM.search(justification):
            errors.append(_error("decline_requires_concrete_evidence", "Decline justification must cite concrete supplied application evidence."))

    errors.extend(_confidence_errors(parsed.get("confidence")))
    errors.extend(justification_errors(parsed.get("justification"), decision_context))
    return errors


def validate_recommendation_support(recommendation, decision_context):
    return []


def validate_provider_output(raw_output, expected_applicant_id, decision_context, screening_control=None):
    """Validate the lean model-facing provider response."""

    parsed, errors = _parse_json(raw_output)
    if errors:
        return {"valid": False, "parsed": parsed, "errors": errors}
    if not isinstance(parsed, dict):
        return {"valid": False, "parsed": parsed, "errors": [_error("root_not_object", "Root value must be a JSON object.")]}

    errors = []
    errors.extend(_key_errors(parsed, PROVIDER_KEYS))
    errors.extend(_basic_screening_errors(parsed, expected_applicant_id, decision_context))
    allowed_key_factor_fields = tuple(
        (screening_control or {}).get("allowed_key_factor_fields")
        or allowed_key_factor_fields_for_context(decision_context)
    )
    errors.extend(
        validate_key_factor_fields_for_allowed(
            parsed.get("key_factor_fields"),
            allowed_key_factor_fields,
        )
    )

    return {"valid": not errors, "parsed": parsed, "errors": errors}


def validate_model_output(raw_output, expected_applicant_id, decision_context, screening_control=None):
    """Compatibility wrapper for provider response validation."""
    return validate_provider_output(raw_output, expected_applicant_id, decision_context, screening_control)


def validate_final_screening_result(result, expected_applicant_id, decision_context):
    """Validate the final project schema after deterministic evidence binding."""

    errors = []
    if not isinstance(result, dict):
        return {"valid": False, "parsed": result, "errors": [_error("root_not_object", "Final result must be an object.")]}

    errors.extend(_key_errors(result, FINAL_KEYS))
    errors.extend(_basic_screening_errors(result, expected_applicant_id, decision_context))
    if result.get("recommendation") in RECOMMENDATIONS:
        errors.extend(validate_recommendation_support(result.get("recommendation"), decision_context))

    factors = result.get("decision_factors")
    if not isinstance(factors, list):
        errors.append(_error("invalid_decision_factors", "decision_factors must be a list."))
        return {"valid": not errors, "parsed": result, "errors": errors}

    if len(factors) < 1:
        errors.append(_error("too_few_factors", "decision_factors must contain at least 1 item."))
    if len(factors) > 3:
        errors.append(_error("too_many_factors", "decision_factors must contain at most 3 items."))

    seen = set()
    for index, factor in enumerate(factors):
        location = f"decision_factors[{index}]"
        if not isinstance(factor, dict):
            errors.append(_error("factor_not_object", f"{location} must be an object."))
            continue

        factor_keys = set(factor.keys())
        for key in sorted(set(FACTOR_KEYS) - factor_keys):
            errors.append(_error("missing_factor_key", f"{location} missing key: {key}"))
        for key in sorted(factor_keys - set(FACTOR_KEYS)):
            errors.append(_error("unexpected_factor_key", f"{location} unexpected key: {key}"))

        field = factor.get("field")
        if field in PROTECTED_FIELDS:
            errors.append(_error("protected_factor_field", f"{location} uses protected field: {field}"))
        elif field not in ALLOWED_KEY_FACTOR_FIELDS:
            errors.append(_error("invalid_factor_field", f"{location} field is not allowed: {field}"))
        elif field not in decision_context:
            errors.append(_error("field_not_in_context", f"{location} field is absent from decision context: {field}"))

        if field in seen:
            errors.append(_error("duplicate_factor_field", f"{location} duplicates field: {field}"))
        elif isinstance(field, str):
            seen.add(field)

        if factor.get("impact") not in IMPACTS:
            errors.append(_error("invalid_impact", f"{location} impact must be positive, negative, or contextual."))

        if field in decision_context and field in ALLOWED_KEY_FACTOR_FIELDS:
            expected = build_evidence_factor(decision_context, field)
            if factor.get("observed_value") != expected["observed_value"]:
                errors.append(_error("observed_value_mismatch", f"{location} observed_value does not match context."))
            if factor.get("impact") != expected["impact"]:
                errors.append(_error("semantic_impact_mismatch", f"{location} impact does not match deterministic evidence binding."))
            if factor.get("reason") != expected["reason"]:
                errors.append(_error("canonical_reason_mismatch", f"{location} reason does not match deterministic evidence binding."))

    return {"valid": not errors, "parsed": result, "errors": errors}
