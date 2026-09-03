"""Append-only JSON Lines logging for screening governance evidence."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from features import compute_derived_features


DECISION_LOG_SCHEMA_VERSION = "decision_log_v1"
INPUT_SCHEMA_VERSION = "project3_application_v1"
SCREENING_VERSION = "Active simplified screening pipeline v1"
PROMPT_VERSION = "Active Prompt V1 - Simplified Free Recommendation"
MODEL_ID = "meta-llama/llama-3-3-70b-instruct"
PROTECTED_AUDIT_FIELDS = ("age", "gender", "nationality")
RECORD_CLASS_REAL_EVIDENCE = "REAL_EVIDENCE"
RECORD_CLASS_TEST_FIXTURE = "TEST_FIXTURE"
RECORD_CLASSES = (RECORD_CLASS_REAL_EVIDENCE, RECORD_CLASS_TEST_FIXTURE)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path):
    records = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.rstrip("\n")
            if not line:
                raise ValueError(f"Empty JSONL line: {line_number}")
            records.append(json.loads(line))
    return records


def write_jsonl(path, records):
    path = Path(path)
    if path.exists():
        path.unlink()
    for record in records:
        append_jsonl(path, record)


def validate_record_class(record_class):
    if record_class is None:
        return [{"code": "missing_record_class", "message": "record_class is required."}]
    if record_class not in RECORD_CLASSES:
        return [{"code": "invalid_record_class", "message": f"record_class must be one of: {','.join(RECORD_CLASSES)}"}]
    return []


def require_record_class(record_class):
    errors = validate_record_class(record_class)
    if errors:
        raise ValueError(errors[0]["code"])
    return record_class


def is_evaluation_record(record):
    """Fairness analysis must never include TEST_FIXTURE records."""
    record_class = require_record_class(record.get("record_class"))
    return record_class == RECORD_CLASS_REAL_EVIDENCE


def _protected_audit_profile(application):
    return {field: application.get(field) for field in PROTECTED_AUDIT_FIELDS}


def _screening_payload(screening_record):
    if screening_record.get("final_status") == "TECHNICAL_FAILURE":
        return {
            "recommendation": None,
            "confidence": None,
            "final_status": "TECHNICAL_FAILURE",
            "justification": None,
            "decision_factors": [],
            "validation_errors": list(screening_record.get("validation_errors", [])),
        }
    result = screening_record.get("final_project_screening_result") or screening_record.get("result") or screening_record
    return {
        "recommendation": result.get("recommendation"),
        "confidence": result.get("confidence"),
        "final_status": screening_record.get("final_status") or screening_record.get("status") or "VALID",
        "justification": result.get("justification"),
        "decision_factors": list(result.get("decision_factors", [])),
        "validation_errors": list(screening_record.get("final_validation_errors") or screening_record.get("validation_errors") or []),
    }


def build_decision_log_record(
    application,
    screening_record,
    explanation,
    routing,
    prompt_sha256,
    decision_id=None,
    event_id=None,
    timestamp_utc=None,
    evidence_label=None,
    record_class=None,
):
    record_class = require_record_class(record_class)
    applicant_id = application["applicant_id"]
    decision_id = decision_id or f"DECISION-{applicant_id}"
    timestamp = timestamp_utc or utc_now()
    screening = _screening_payload(screening_record)
    derived_features = compute_derived_features(application)
    retry_used = bool(screening_record.get("retry_used", False))
    technical_failure = screening["final_status"] != "VALID"

    return {
        "schema_version": DECISION_LOG_SCHEMA_VERSION,
        "record_class": record_class,
        "identity": {
            "event_id": event_id or f"EVENT-{decision_id}",
            "decision_id": decision_id,
            "applicant_id": applicant_id,
            "timestamp_utc": timestamp,
        },
        "screening": screening,
        "explainability": explanation,
        "model_version": {
            "model_id": MODEL_ID,
            "prompt_version": PROMPT_VERSION,
            "prompt_sha256": prompt_sha256,
            "screening_version": SCREENING_VERSION,
        },
        "monitoring": {
            "input_schema_version": INPUT_SCHEMA_VERSION,
            "derived_features": derived_features,
            "output_recommendation": screening["recommendation"],
            "confidence": screening["confidence"],
            "validation_status": screening["final_status"],
            "retry_used": retry_used,
            "technical_failure": technical_failure,
        },
        "routing": {
            "review_required": bool(routing.get("review_required")),
            "review_reasons": list(routing.get("review_reasons", [])),
        },
        "audit_profile": {
            "protected_attributes": _protected_audit_profile(application),
            "application_snapshot": dict(application),
        },
        "evidence_label": evidence_label,
    }


def validate_decision_log_record(record):
    required = {"schema_version", "record_class", "identity", "screening", "explainability", "model_version", "monitoring", "routing", "audit_profile"}
    errors = []
    missing = sorted(required - set(record.keys()))
    if missing:
        errors.append({"code": "missing_decision_log_key", "message": ",".join(missing)})
    errors.extend(validate_record_class(record.get("record_class")))
    if record.get("schema_version") != DECISION_LOG_SCHEMA_VERSION:
        errors.append({"code": "invalid_decision_log_schema_version", "message": "Unexpected decision log schema version."})
    audit_profile = record.get("audit_profile", {})
    if "protected_attributes" not in audit_profile or "application_snapshot" not in audit_profile:
        errors.append({"code": "audit_profile_not_separated", "message": "Protected audit data must be separated from screening/explanation."})
    explanation_text = json.dumps(record.get("explainability", {}), ensure_ascii=False).lower()
    for protected_field in PROTECTED_AUDIT_FIELDS:
        if f'"{protected_field}"' in explanation_text:
            errors.append({"code": "protected_field_in_explanation", "message": f"Protected field leaked into explanation: {protected_field}"})
    monitoring = record.get("monitoring", {})
    for key in ("input_schema_version", "derived_features", "output_recommendation", "confidence", "validation_status", "retry_used", "technical_failure"):
        if key not in monitoring:
            errors.append({"code": "missing_monitoring_field", "message": f"Missing monitoring field: {key}"})
    return errors
