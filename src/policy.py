"""Assignment LAB_POLICY simulator.

This module evaluates only the assignment-provided LAB_POLICY boundary
calculation. It does not represent current CBK regulation and does not
produce a lending recommendation.
"""

LAB_POLICY_NAME = "LAB_POLICY"
LAB_POLICY_CONTEXT = (
    "Assignment-provided LAB_POLICY simulation for project testing; "
    "not current CBK regulation or real lender underwriting policy."
)
LAB_POLICY_CAPS = {
    "Kuwaiti": 0.50,
    "Expat": 0.40,
}

POLICY_OUTPUT_KEYS = (
    "policy_name",
    "policy_context",
    "computable",
    "lab_dbr_ratio",
    "lab_policy_cap",
    "result",
    "not_computable_reason",
)


def _base_output(computable, lab_dbr_ratio, lab_policy_cap, result, reason):
    return {
        "policy_name": LAB_POLICY_NAME,
        "policy_context": LAB_POLICY_CONTEXT,
        "computable": computable,
        "lab_dbr_ratio": lab_dbr_ratio,
        "lab_policy_cap": lab_policy_cap,
        "result": result,
        "not_computable_reason": reason,
    }


def _required_number(record, field_name):
    if field_name not in record:
        return None

    value = record[field_name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"Required LAB_POLICY input must be numeric: {field_name}")
    return value


def evaluate_lab_policy(record):
    """Evaluate LAB_POLICY only when explicit policy inputs are available.

    Required inputs are nationality, current monthly net salary, existing
    monthly debt, and proposed monthly installment. The proposed installment is
    never inferred from requested loan amount or any other field.
    """

    nationality = record.get("nationality")
    cap = LAB_POLICY_CAPS.get(nationality)
    if cap is None:
        return _base_output(
            False,
            None,
            None,
            "not_computable",
            "Unsupported nationality for LAB_POLICY cap; no additional category was inferred.",
        )

    salary = _required_number(record, "monthly_net_salary_kwd")
    existing_debt = _required_number(record, "existing_debt_monthly_kwd")
    proposed_installment = _required_number(record, "proposed_monthly_installment_kwd")

    if salary is None:
        return _base_output(
            False,
            None,
            cap,
            "not_computable",
            "monthly_net_salary_kwd is unavailable for LAB_POLICY evaluation.",
        )

    if existing_debt is None:
        return _base_output(
            False,
            None,
            cap,
            "not_computable",
            "existing_debt_monthly_kwd is unavailable for LAB_POLICY evaluation.",
        )

    if proposed_installment is None:
        return _base_output(
            False,
            None,
            cap,
            "not_computable",
            "proposed_monthly_installment_kwd is unavailable; the project does not estimate it.",
        )

    if salary == 0:
        return _base_output(
            False,
            None,
            cap,
            "not_computable",
            "monthly_net_salary_kwd is zero, so the LAB_POLICY denominator is invalid.",
        )

    ratio = (existing_debt + proposed_installment) / salary
    result = "within_lab_cap" if ratio <= cap else "exceeds_lab_cap"

    return _base_output(True, ratio, cap, result, None)
