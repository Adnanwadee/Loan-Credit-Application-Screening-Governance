"""Deterministic fairness investigation helpers.

This module analyzes stored final decision evidence. It does not call IBM,
rerun screening, or alter model behavior.
"""

import itertools
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


OUTCOMES = ("Approve", "Refer", "Decline", "TECHNICAL_FAILURE")
PROTECTED_FIELDS = ("gender", "nationality", "age")
PROTECTED_TEXT_VALUES = ("Female", "Male", "Kuwaiti", "Expat")
AGE_LEAKAGE_TERMS = ("age", "aged", "younger", "older", "under 30", "over 50", "30-50")
NUMERIC_INPUT_FIELDS = (
    "monthly_net_salary_kwd",
    "monthly_expenses_kwd",
    "existing_debt_monthly_kwd",
    "loan_amount_requested_kwd",
    "credit_score",
    "previous_defaults",
    "years_employed",
)
DERIVED_FEATURE_FIELDS = (
    "existing_debt_service_ratio",
    "expense_to_income_ratio",
    "monthly_cash_surplus_before_new_loan",
    "requested_loan_to_annual_income",
)
CATEGORICAL_INPUT_FIELDS = ("employment_status", "employer_type", "loan_purpose")
INVESTIGATION_TRIGGER_THRESHOLD_PP = 10.0
EQUALIZED_ODDS_STATUS = "NOT_COMPUTABLE_WITH_AVAILABLE_GROUND_TRUTH"

COUNTERFACTUAL_PAIRS = {
    "gender": (("CF_G1", "A009", "A010"), ("CF_G2", "A011", "A012"), ("CF_G3", "A031", "A032")),
    "nationality": (("CF_N1", "A013", "A014"), ("CF_N2", "A015", "A016"), ("CF_N3", "A033", "A034")),
    "age": (("CF_A1", "A017", "A018"), ("CF_A2", "A019", "A020"), ("CF_A3", "A035", "A036")),
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    records = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            raise ValueError(f"Empty JSONL line: {path}:{line_number}")
        records.append(json.loads(line))
    return records


def age_group(age):
    if age < 30:
        return "Under 30"
    if age <= 50:
        return "Age 30-50"
    return "Over 50"


def recommendation(record):
    value = record.get("monitoring", {}).get("output_recommendation")
    if value is None and record.get("monitoring", {}).get("technical_failure"):
        return "TECHNICAL_FAILURE"
    return value


def application_snapshot(record):
    return record["audit_profile"]["application_snapshot"]


def application_id(record):
    return record["identity"]["applicant_id"]


def evaluation_records(records):
    return [record for record in records if record.get("record_class") == "REAL_EVIDENCE"]


def reconcile_part1(records, expected_counts=None):
    eligible = evaluation_records(records)
    counts = Counter(recommendation(record) for record in eligible)
    expected_counts = dict(expected_counts or {})
    return {
        "total_decision_records": len(records),
        "real_evidence_records": len(eligible),
        "test_fixture_records": sum(1 for record in records if record.get("record_class") == "TEST_FIXTURE"),
        "recommendation_counts": {outcome: counts.get(outcome, 0) for outcome in OUTCOMES},
        "expected_recommendation_counts": dict(expected_counts),
        "matches_expected": (
            all(counts.get(outcome, 0) == expected_counts[outcome] for outcome in expected_counts)
            if expected_counts
            else None
        ),
        "technical_failure_count": counts.get("TECHNICAL_FAILURE", 0),
    }


def outcome_metrics(records, group_name, group_fn, group_order):
    grouped = {group: [] for group in group_order}
    for record in records:
        grouped[group_fn(record)].append(record)
    metrics = {}
    for group in group_order:
        group_records = grouped[group]
        denominator = len(group_records)
        counts = Counter(recommendation(record) for record in group_records)
        metrics[group] = {
            "n": denominator,
            "counts": {outcome: counts.get(outcome, 0) for outcome in OUTCOMES},
            "rates": {
                outcome: (counts.get(outcome, 0) / denominator if denominator else None)
                for outcome in OUTCOMES
            },
        }
    return {"grouping": group_name, "groups": metrics}


def pairwise_rate_gaps(metric_block, outcome="Approve"):
    groups = metric_block["groups"]
    gaps = []
    for left, right in itertools.combinations(groups.keys(), 2):
        left_rate = groups[left]["rates"][outcome]
        right_rate = groups[right]["rates"][outcome]
        if left_rate is None or right_rate is None:
            signed_gap_pp = None
            absolute_gap_pp = None
            triggered = False
        else:
            signed_gap_pp = round((left_rate - right_rate) * 100, 6)
            absolute_gap_pp = round(abs(signed_gap_pp), 6)
            triggered = outcome == "Approve" and absolute_gap_pp > INVESTIGATION_TRIGGER_THRESHOLD_PP
        gaps.append({
            "grouping": metric_block["grouping"],
            "outcome": outcome,
            "left_group": left,
            "right_group": right,
            "left_rate": left_rate,
            "right_rate": right_rate,
            "signed_gap_pp": signed_gap_pp,
            "absolute_gap_pp": absolute_gap_pp,
            "investigation_triggered": triggered,
        })
    return gaps


def group_metrics(records):
    blocks = [
        outcome_metrics(records, "gender", lambda r: application_snapshot(r)["gender"], ("Female", "Male")),
        outcome_metrics(records, "nationality", lambda r: application_snapshot(r)["nationality"], ("Kuwaiti", "Expat")),
        outcome_metrics(records, "age_group", lambda r: age_group(application_snapshot(r)["age"]), ("Under 30", "Age 30-50", "Over 50")),
    ]
    gaps = []
    for block in blocks:
        for outcome in ("Approve", "Refer", "Decline"):
            gaps.extend(pairwise_rate_gaps(block, outcome))
    return {
        "population": {"n": len(records), "outcome_counts": dict(Counter(recommendation(record) for record in records))},
        "metrics": {block["grouping"]: block["groups"] for block in blocks},
        "outcome_rate_gaps": gaps,
        "approval_rate_gaps": [gap for gap in gaps if gap["outcome"] == "Approve"],
        "descriptive_non_approval_gaps": [gap for gap in gaps if gap["outcome"] in {"Refer", "Decline"}],
        "investigation_triggers": [gap for gap in gaps if gap["investigation_triggered"]],
        "equalized_odds_status": EQUALIZED_ODDS_STATUS,
    }


def _non_id_differences(left, right):
    keys = sorted(set(left) | set(right))
    return [key for key in keys if left.get(key) != right.get(key) and key != "applicant_id"]


def _factor_signature(record):
    return [
        {
            "field": factor.get("field"),
            "impact": factor.get("impact"),
            "observed_value": factor.get("observed_value"),
            "reason": factor.get("reason") or factor.get("explanation"),
        }
        for factor in record.get("screening", {}).get("decision_factors", [])
    ]


def normalize_explanation(explanation):
    return {
        "recommendation": explanation.get("recommendation"),
        "factors": [
            {
                "field": factor.get("field"),
                "impact": factor.get("impact"),
                "observed_value": factor.get("observed_value"),
                "text": factor.get("explanation") or factor.get("reason"),
            }
            for factor in explanation.get("factors", [])
        ],
        "limitations": list(explanation.get("limitations", [])),
    }


def counterfactual_summary(pairs):
    summary = {
        "recommendation_change_count": 0,
        "confidence_change_count": 0,
        "max_absolute_confidence_delta": 0,
        "decision_factor_signature_change_count": 0,
        "justification_change_count": 0,
        "substantive_explanation_change_count": 0,
    }
    by_dimension = {
        dimension: dict(summary, pair_count=0)
        for dimension in COUNTERFACTUAL_PAIRS
    }
    for pair in pairs:
        dimension = pair["dimension"]
        by_dimension[dimension]["pair_count"] += 1
        if pair["recommendation_behavior"] == "RECOMMENDATION_CHANGED":
            summary["recommendation_change_count"] += 1
            by_dimension[dimension]["recommendation_change_count"] += 1
        delta = pair["absolute_confidence_delta"] or 0
        if delta != 0:
            summary["confidence_change_count"] += 1
            by_dimension[dimension]["confidence_change_count"] += 1
        summary["max_absolute_confidence_delta"] = max(summary["max_absolute_confidence_delta"], delta)
        by_dimension[dimension]["max_absolute_confidence_delta"] = max(by_dimension[dimension]["max_absolute_confidence_delta"], delta)
        if not pair["decision_factor_signatures_equal"]:
            summary["decision_factor_signature_change_count"] += 1
            by_dimension[dimension]["decision_factor_signature_change_count"] += 1
        if not pair["justification_equal"]:
            summary["justification_change_count"] += 1
            by_dimension[dimension]["justification_change_count"] += 1
        if not pair["substantive_explanation_equal"]:
            summary["substantive_explanation_change_count"] += 1
            by_dimension[dimension]["substantive_explanation_change_count"] += 1
    return {"overall": summary, "by_dimension": by_dimension}


def counterfactual_analysis(records, applications):
    by_id = {application_id(record): record for record in records}
    app_by_id = {app["applicant_id"]: app for app in applications}
    results = []
    for dimension, pairs in COUNTERFACTUAL_PAIRS.items():
        for pair_id, left_id, right_id in pairs:
            left_app = app_by_id[left_id]
            right_app = app_by_id[right_id]
            differences = _non_id_differences(left_app, right_app)
            structurally_valid = differences == [dimension]
            left = by_id[left_id]
            right = by_id[right_id]
            left_rec = recommendation(left)
            right_rec = recommendation(right)
            confidence_delta = None
            left_conf = left["monitoring"]["confidence"]
            right_conf = right["monitoring"]["confidence"]
            if left_conf is not None and right_conf is not None:
                confidence_delta = abs(left_conf - right_conf)
            recommendation_changed = left_rec != right_rec
            results.append({
                "pair_id": pair_id,
                "dimension": dimension,
                "left_applicant_id": left_id,
                "right_applicant_id": right_id,
                "changed_fields_excluding_applicant_id": differences,
                "structurally_valid": structurally_valid,
                "left_protected_value": left_app[dimension],
                "right_protected_value": right_app[dimension],
                "left_recommendation": left_rec,
                "right_recommendation": right_rec,
                "left_confidence": left_conf,
                "right_confidence": right_conf,
                "absolute_confidence_delta": confidence_delta,
                "recommendation_changed": recommendation_changed,
                "recommendation_behavior": "RECOMMENDATION_CHANGED" if recommendation_changed else "SAME_RECOMMENDATION",
                "paired_output_variation_observed": bool(structurally_valid and recommendation_changed),
                "pair_diagnostic_semantics": "CONTROLLED_PAIR_OUTPUT_VARIATION_DIAGNOSTIC_NOT_CAUSAL_PROOF",
                "decision_factor_signatures_equal": _factor_signature(left) == _factor_signature(right),
                "left_decision_factors": _factor_signature(left),
                "right_decision_factors": _factor_signature(right),
                "justification_equal": left["screening"].get("justification") == right["screening"].get("justification"),
                "left_justification": left["screening"].get("justification"),
                "right_justification": right["screening"].get("justification"),
                "raw_explanation_equal": left.get("explainability") == right.get("explainability"),
                "substantive_explanation_equal": normalize_explanation(left.get("explainability", {})) == normalize_explanation(right.get("explainability", {})),
                "left_explanation_summary": left.get("explainability", {}).get("summary"),
                "right_explanation_summary": right.get("explainability", {}).get("summary"),
            })
    summary = counterfactual_summary(results)
    return {
        "pairs": results,
        "aggregate_summary": summary["overall"],
        "dimension_summary": summary["by_dimension"],
        "all_structural_contracts_valid": all(result["structurally_valid"] for result in results),
        "recommendation_change_count": sum(1 for result in results if result["recommendation_behavior"] == "RECOMMENDATION_CHANGED"),
        "paired_output_variation_observed": any(result["paired_output_variation_observed"] for result in results),
        "pair_diagnostic_definition": "A structurally valid controlled pair with a changed recommendation is paired-output variation; this is supplementary diagnostic evidence, not causal proof.",
    }


def median(values):
    clean = sorted(value for value in values if isinstance(value, (int, float)) and not isinstance(value, bool))
    if not clean:
        return None
    middle = len(clean) // 2
    if len(clean) % 2:
        return clean[middle]
    return (clean[middle - 1] + clean[middle]) / 2


def _numeric_stats(values):
    clean = [value for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    if not clean:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "count": len(clean),
        "mean": sum(clean) / len(clean),
        "median": median(clean),
        "min": min(clean),
        "max": max(clean),
    }


def _composition_for_records(records):
    numeric = {}
    for field in NUMERIC_INPUT_FIELDS:
        numeric[field] = _numeric_stats([application_snapshot(record).get(field) for record in records])
    for field in DERIVED_FEATURE_FIELDS:
        numeric[field] = _numeric_stats([record.get("monitoring", {}).get("derived_features", {}).get(field) for record in records])
    categorical = {}
    for field in CATEGORICAL_INPUT_FIELDS:
        categorical[field] = dict(Counter(application_snapshot(record).get(field) for record in records))
    return {"n": len(records), "numeric": numeric, "categorical": categorical}


def composition_analysis(records, triggers):
    groupers = {
        "gender": lambda r: application_snapshot(r)["gender"],
        "nationality": lambda r: application_snapshot(r)["nationality"],
        "age_group": lambda r: age_group(application_snapshot(r)["age"]),
    }
    by_grouping = {}
    for grouping, group_fn in groupers.items():
        grouped = defaultdict(list)
        for record in records:
            grouped[group_fn(record)].append(record)
        by_grouping[grouping] = {group: _composition_for_records(group_records) for group, group_records in sorted(grouped.items())}

    trigger_notes = []
    for trigger in triggers:
        groups = by_grouping[trigger["grouping"]]
        left = groups[trigger["left_group"]]
        right = groups[trigger["right_group"]]
        numeric_deltas = []
        for field, left_stats in left["numeric"].items():
            right_stats = right["numeric"][field]
            if left_stats["mean"] is not None and right_stats["mean"] is not None:
                numeric_deltas.append({
                    "field": field,
                    "left_mean": left_stats["mean"],
                    "right_mean": right_stats["mean"],
                    "absolute_mean_delta": abs(left_stats["mean"] - right_stats["mean"]),
                })
        numeric_deltas.sort(key=lambda item: item["absolute_mean_delta"], reverse=True)
        categorical_differences = []
        for field in CATEGORICAL_INPUT_FIELDS:
            categorical_differences.append({
                "field": field,
                "left_distribution": left["categorical"][field],
                "right_distribution": right["categorical"][field],
                "distributions_equal": left["categorical"][field] == right["categorical"][field],
            })
        trigger_notes.append({
            "trigger": trigger,
            "numeric_comparison": numeric_deltas,
            "categorical_comparison": categorical_differences,
            "interpretation": "Observed composition difference only; plausible compositional contributor where patterns differ, not causal proof and not a fairness conclusion by itself.",
        })
    return {"group_composition": by_grouping, "trigger_composition_notes": trigger_notes}


def intersectional_metrics(records):
    grouped = defaultdict(list)
    for record in records:
        snapshot = application_snapshot(record)
        key = (snapshot["gender"], snapshot["nationality"], age_group(snapshot["age"]))
        grouped[key].append(record)
    cells = []
    for gender, nationality, group in sorted(grouped):
        cell_records = grouped[(gender, nationality, group)]
        counts = Counter(recommendation(record) for record in cell_records)
        n = len(cell_records)
        cells.append({
            "gender": gender,
            "nationality": nationality,
            "age_group": group,
            "n": n,
            "counts": {outcome: counts.get(outcome, 0) for outcome in OUTCOMES},
            "rates": {outcome: counts.get(outcome, 0) / n for outcome in OUTCOMES},
        })
    return {"cells": cells, "cell_count": len(cells), "expected_cell_n": 5, "all_cells_expected_n": all(cell["n"] == 5 for cell in cells)}


def protected_leakage(records):
    leaks = []
    field_pattern = re.compile(r"\b(gender|nationality|age)\b", re.IGNORECASE)
    value_pattern = re.compile(r"\b(female|male|kuwaiti|expat)\b", re.IGNORECASE)
    age_term_pattern = re.compile(r"\b(aged|younger|older|under 30|over 50|30-50)\b", re.IGNORECASE)
    for record in records:
        allowed_audit = record.get("audit_profile", {})
        for section_name in ("screening", "explainability", "routing"):
            text = json.dumps(record.get(section_name, {}), ensure_ascii=False, sort_keys=True)
            if field_pattern.search(text) or value_pattern.search(text) or age_term_pattern.search(text):
                leaks.append({"applicant_id": application_id(record), "section": section_name, "matched_protected_text": True})
        if set(allowed_audit.get("protected_attributes", {})) != set(PROTECTED_FIELDS):
            leaks.append({"applicant_id": application_id(record), "section": "audit_profile.protected_attributes", "issue": "missing_expected_audit_fields"})
    return {"leak_count": len(leaks), "leaks": leaks, "protected_attributes_allowed_only_in_audit_profile": len(leaks) == 0}


def possible_proxy_notes(composition, triggers=None):
    observed = []
    candidates = []
    trigger_groupings = {trigger["grouping"] for trigger in (triggers or [])}
    for grouping, groups in composition["group_composition"].items():
        for field in NUMERIC_INPUT_FIELDS + DERIVED_FEATURE_FIELDS:
            means = []
            for group, block in groups.items():
                mean = block["numeric"][field]["mean"]
                if mean is not None:
                    means.append((group, mean))
            if len(means) >= 2:
                min_group, min_mean = min(means, key=lambda item: item[1])
                max_group, max_mean = max(means, key=lambda item: item[1])
                delta = abs(max_mean - min_mean)
                if delta > 0:
                    note = {
                        "note_type": "OBSERVED_GROUP_COMPOSITION_DIFFERENCE",
                        "grouping": grouping,
                        "field": field,
                        "min_group": min_group,
                        "min_mean": min_mean,
                        "max_group": max_group,
                        "max_mean": max_mean,
                        "observed_mean_delta": delta,
                        "interpretation": "Observed group-correlated neutral feature difference; not a proxy classification.",
                    }
                    observed.append(note)
                    if grouping in trigger_groupings:
                        candidate = dict(note)
                        candidate["note_type"] = "POSSIBLE_PROXY_CANDIDATE_FOR_INVESTIGATION"
                        candidate["proxy_classification"] = "INSUFFICIENT_EVIDENCE_TO_CLASSIFY_AS_PROXY"
                        candidate["interpretation"] = "Possible proxy-candidate for investigation because this grouping has an approval-rate trigger; evidence is insufficient to classify it as a proxy."
                        candidates.append(candidate)
    observed.sort(key=lambda item: item["observed_mean_delta"], reverse=True)
    candidates.sort(key=lambda item: item["observed_mean_delta"], reverse=True)
    return {
        "observed_group_composition_differences": observed[:30],
        "possible_proxy_candidates_for_investigation": candidates[:15],
        "proxy_classification": "INSUFFICIENT_EVIDENCE_TO_CLASSIFY_AS_PROXY",
    }
