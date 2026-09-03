"""Deterministic arithmetic feature computation for screening evidence.

The values returned here are factual arithmetic evidence for later
screening. They are not lending recommendations, regulatory DBR results,
projected post-loan affordability results, or qualitative risk labels.
"""

FEATURE_KEYS = (
    "existing_debt_service_ratio",
    "expense_to_income_ratio",
    "monthly_cash_surplus_before_new_loan",
    "requested_loan_to_annual_income",
)

_REQUIRED_FIELDS = (
    "monthly_net_salary_kwd",
    "monthly_expenses_kwd",
    "existing_debt_monthly_kwd",
    "loan_amount_requested_kwd",
)


def _required_number(application, field_name):
    if field_name not in application:
        raise KeyError(f"Missing required arithmetic input: {field_name}")

    value = application[field_name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"Required arithmetic input must be numeric: {field_name}")
    return value


def compute_derived_features(application):
    """Return exactly four deterministic arithmetic features for one record.

    ``existing_debt_service_ratio`` is current existing monthly debt service
    divided by current monthly net salary. It is not projected post-loan DBR,
    regulatory DBR, a compliance result, or an automatic lending threshold.

    For zero salary, denominator-based ratios are not computable and return
    ``None``. Cash surplus before any new loan is still computed normally and
    negative values are preserved.
    """

    salary = _required_number(application, "monthly_net_salary_kwd")
    expenses = _required_number(application, "monthly_expenses_kwd")
    existing_debt = _required_number(application, "existing_debt_monthly_kwd")
    requested_loan = _required_number(application, "loan_amount_requested_kwd")

    if salary == 0:
        existing_debt_service_ratio = None
        expense_to_income_ratio = None
        requested_loan_to_annual_income = None
    else:
        existing_debt_service_ratio = existing_debt / salary
        expense_to_income_ratio = expenses / salary
        requested_loan_to_annual_income = requested_loan / (salary * 12)

    return {
        "existing_debt_service_ratio": existing_debt_service_ratio,
        "expense_to_income_ratio": expense_to_income_ratio,
        "monthly_cash_surplus_before_new_loan": salary - expenses - existing_debt,
        "requested_loan_to_annual_income": requested_loan_to_annual_income,
    }
