"""Screening runner: provider response validation, deterministic binding, one retry."""

import copy
import json
from pathlib import Path

from evidence import build_final_screening_result, build_screening_control
from features import compute_derived_features
from validation import validate_final_screening_result, validate_provider_output


ORIGINAL_APPLICATION_FIELDS = (
    "applicant_id",
    "age",
    "gender",
    "nationality",
    "employment_status",
    "employer_type",
    "years_employed",
    "monthly_net_salary_kwd",
    "monthly_expenses_kwd",
    "existing_debt_monthly_kwd",
    "loan_amount_requested_kwd",
    "loan_purpose",
    "credit_score",
    "previous_defaults",
)

STRING_FIELDS = (
    "applicant_id",
    "gender",
    "nationality",
    "employment_status",
    "employer_type",
    "loan_purpose",
)

NUMERIC_FIELDS = (
    "age",
    "years_employed",
    "monthly_net_salary_kwd",
    "monthly_expenses_kwd",
    "existing_debt_monthly_kwd",
    "loan_amount_requested_kwd",
    "credit_score",
    "previous_defaults",
)

VALIDATION_SET_IDS = (
    "A001",
    "A005",
    "A007",
    "A008",
    "A031",
    "A032",
    "A033",
    "A034",
    "A035",
    "A036",
)


def project_root():
    return Path(__file__).resolve().parents[1]


def load_prompt(prompt_path=None):
    path = Path(prompt_path) if prompt_path is not None else project_root() / "prompts" / "screening_v1.txt"
    return path.read_text(encoding="utf-8")


def validate_application(application):
    errors = []
    if not isinstance(application, dict):
        return [{"code": "application_not_object", "message": "application must be a mapping."}]
    for field in ORIGINAL_APPLICATION_FIELDS:
        if field not in application:
            errors.append({"code": "missing_application_field", "field": field, "message": f"missing required application field: {field}"})
    for field in STRING_FIELDS:
        if field in application and application[field] is not None and (not isinstance(application[field], str) or not application[field].strip()):
            errors.append({"code": "invalid_application_string", "field": field, "message": f"{field} must be a non-empty string."})
    for field in NUMERIC_FIELDS:
        if field in application and (isinstance(application[field], bool) or not isinstance(application[field], (int, float))):
            errors.append({"code": "invalid_application_number", "field": field, "message": f"{field} must be numeric."})
    defaults = application.get("previous_defaults")
    if isinstance(defaults, (int, float)) and not isinstance(defaults, bool):
        if defaults < 0 or int(defaults) != defaults:
            errors.append({"code": "invalid_previous_defaults", "field": "previous_defaults", "message": "previous_defaults must be a non-negative integer."})
    return errors


def build_decision_context(application):
    application_errors = validate_application(application)
    if application_errors:
        raise ValueError(application_errors)
    source = copy.deepcopy(application)
    context = {}
    for field in ORIGINAL_APPLICATION_FIELDS:
        if field not in source:
            raise KeyError(f"Missing application field for decision context: {field}")
        context[field] = source[field]

    context.update(compute_derived_features(source))
    return context


def _retry_feedback(validation_errors):
    lines = ["The previous response violated these output-contract checks:"]
    seen = set()
    for error in validation_errors:
        code = error.get("code", "unknown_error")
        if code not in seen:
            lines.append(f"- {code}")
            seen.add(code)

    lines.extend(
        [
            "",
            "Correct only the listed provider-response contract categories.",
            "Return RAW JSON ONLY.",
            "Do not include field values, factor explanations, or target-outcome hints.",
        ]
    )
    return "\n".join(lines)


def build_messages(prompt_text, decision_context, retry=False, validation_errors=None):
    screening_control = build_screening_control(decision_context)
    context_json = json.dumps(decision_context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    control_json = json.dumps(screening_control, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    user_content = "Decision context JSON:\n" + context_json + "\nScreening control JSON:\n" + control_json
    if retry:
        user_content = _retry_feedback(validation_errors or []) + "\n" + user_content
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": user_content},
    ]


def _technical_failure(applicant_id, attempts, validation_errors, raw_responses, provider_error=None):
    result = {
        "applicant_id": applicant_id,
        "status": "TECHNICAL_FAILURE",
        "attempts": attempts,
        "validation_errors": validation_errors,
        "raw_responses": raw_responses,
    }
    if provider_error:
        result["provider_error"] = provider_error
    return result


def _call_chat(model_client, messages):
    if hasattr(model_client, "chat"):
        return model_client.chat(messages)
    return model_client(messages)


def screen_application(application, model_client, prompt_text=None, prompt_path=None):
    prompt = prompt_text if prompt_text is not None else load_prompt(prompt_path)
    decision_context = build_decision_context(application)
    screening_control = build_screening_control(decision_context)
    applicant_id = decision_context["applicant_id"]
    raw_responses = []

    first_messages = build_messages(prompt, decision_context, retry=False)
    try:
        first_raw = _call_chat(model_client, first_messages)
    except Exception as exc:
        return _technical_failure(
            applicant_id,
            1,
            [{"code": "provider_exception", "message": exc.__class__.__name__}],
            raw_responses,
            provider_error=exc.__class__.__name__,
        )

    raw_responses.append(first_raw)
    first_validation = validate_provider_output(first_raw, applicant_id, decision_context, screening_control)
    if first_validation["valid"]:
        final_result = build_final_screening_result(first_validation["parsed"], decision_context)
        final_validation = validate_final_screening_result(final_result, applicant_id, decision_context)
        if not final_validation["valid"]:
            return _technical_failure(applicant_id, 1, final_validation["errors"], raw_responses)
        return {
            "applicant_id": applicant_id,
            "status": "VALID",
            "attempts": 1,
            "retry_used": False,
            "decision_context": decision_context,
            "screening_control": screening_control,
            "messages": first_messages,
            "raw_responses": raw_responses,
            "validation_errors": [],
            "provider_response": first_validation["parsed"],
            "result": final_result,
            "initial_schema_valid": True,
        }

    retry_messages = build_messages(prompt, decision_context, retry=True, validation_errors=first_validation["errors"])
    try:
        retry_raw = _call_chat(model_client, retry_messages)
    except Exception as exc:
        return _technical_failure(
            applicant_id,
            2,
            first_validation["errors"] + [{"code": "provider_exception", "message": exc.__class__.__name__}],
            raw_responses,
            provider_error=exc.__class__.__name__,
        )

    raw_responses.append(retry_raw)
    retry_validation = validate_provider_output(retry_raw, applicant_id, decision_context, screening_control)
    if retry_validation["valid"]:
        final_result = build_final_screening_result(retry_validation["parsed"], decision_context)
        final_validation = validate_final_screening_result(final_result, applicant_id, decision_context)
        if not final_validation["valid"]:
            return _technical_failure(applicant_id, 2, first_validation["errors"] + final_validation["errors"], raw_responses)
        return {
            "applicant_id": applicant_id,
            "status": "VALID",
            "attempts": 2,
            "retry_used": True,
            "decision_context": decision_context,
            "screening_control": screening_control,
            "messages": retry_messages,
            "raw_responses": raw_responses,
            "validation_errors": first_validation["errors"],
            "provider_response": retry_validation["parsed"],
            "result": final_result,
            "initial_schema_valid": False,
        }

    return _technical_failure(
        applicant_id,
        2,
        first_validation["errors"] + retry_validation["errors"],
        raw_responses,
    )
