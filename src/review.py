"""Deterministic human-review routing and reviewer action validation."""

from datetime import datetime, timezone


RECOMMENDATIONS = {"Approve", "Refer", "Decline"}
REVIEW_STATUSES = {"PENDING", "ACCEPTED", "OVERRIDDEN"}
REVIEW_ACTIONS = {"ACCEPT", "OVERRIDE"}
RECORD_CLASSES = ("REAL_EVIDENCE", "TEST_FIXTURE")
ACTION_CONTEXT_CONTROLLED_WORKFLOW = "CONTROLLED_REVIEW_DEMONSTRATION"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def route_for_review(screening_result):
    final_status = screening_result.get("final_status") or screening_result.get("status") or "VALID"
    recommendation = screening_result.get("recommendation")
    confidence = screening_result.get("confidence")
    reasons = []

    if final_status != "VALID":
        reasons.append("TECHNICAL_FAILURE")
    elif recommendation == "Decline":
        reasons.append("DECLINE_REQUIRES_REVIEW")
    elif recommendation == "Refer":
        reasons.append("REFER_REQUIRES_REVIEW")
    elif recommendation == "Approve":
        if isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and confidence < 0.75:
            reasons.append("LOW_CONFIDENCE_APPROVE")

    return {
        "review_required": bool(reasons),
        "review_reasons": reasons,
    }


def _require_record_class(record_class):
    if record_class is None:
        raise ValueError("missing_record_class")
    if record_class not in RECORD_CLASSES:
        raise ValueError("invalid_record_class")
    return record_class


def _record_class_validation_error(record_class):
    if record_class is None:
        return {"code": "missing_record_class", "message": "record_class is required."}
    if record_class not in RECORD_CLASSES:
        return {"code": "invalid_record_class", "message": "record_class must be REAL_EVIDENCE or TEST_FIXTURE."}
    return None


def build_review_queue_record(decision_record, timestamp_utc=None):
    routing = decision_record.get("routing", {})
    if not routing.get("review_required"):
        raise ValueError("Only mandatory-review decisions can be queued.")

    record_class = _require_record_class(decision_record.get("record_class"))
    applicant_id = decision_record["identity"]["applicant_id"]
    decision_id = decision_record["identity"]["decision_id"]
    return {
        "record_class": record_class,
        "review_id": f"REVIEW-{decision_id}",
        "decision_id": decision_id,
        "applicant_id": applicant_id,
        "application_snapshot": dict(decision_record["audit_profile"]["application_snapshot"]),
        "ai_recommendation": decision_record["screening"].get("recommendation"),
        "confidence": decision_record["screening"].get("confidence"),
        "justification": decision_record["screening"].get("justification"),
        "explanation": decision_record["explainability"],
        "decision_factors": list(decision_record["screening"].get("decision_factors", [])),
        "review_reasons": list(routing.get("review_reasons", [])),
        "created_at_utc": timestamp_utc or utc_now(),
        "review_status": "PENDING",
        "evidence_label": decision_record.get("evidence_label") or "controlled_review_demonstration",
    }


def validate_review_queue_record(record):
    required = {
        "review_id",
        "decision_id",
        "applicant_id",
        "application_snapshot",
        "ai_recommendation",
        "confidence",
        "justification",
        "explanation",
        "decision_factors",
        "review_reasons",
        "created_at_utc",
        "review_status",
        "record_class",
    }
    missing = sorted(required - set(record.keys()))
    if missing:
        return [{"code": "missing_review_queue_key", "message": ",".join(missing)}]
    record_class_error = _record_class_validation_error(record.get("record_class"))
    if record_class_error:
        return [record_class_error]
    if record.get("review_status") != "PENDING":
        return [{"code": "invalid_initial_review_status", "message": "Initial review status must be PENDING."}]
    if not record.get("review_reasons"):
        return [{"code": "missing_review_reason", "message": "Queued review record must include reason codes."}]
    return []


def build_review_action_record(queue_record, action, reviewer_recommendation, comment, timestamp_utc=None):
    record_class = _require_record_class(queue_record.get("record_class"))
    if action not in REVIEW_ACTIONS:
        raise ValueError("invalid_review_action")
    if not isinstance(comment, str) or not comment.strip():
        raise ValueError("missing_review_comment")
    ai_recommendation = queue_record.get("ai_recommendation")
    if action == "ACCEPT" and reviewer_recommendation != ai_recommendation:
        raise ValueError("accept_must_preserve_ai_recommendation")
    if reviewer_recommendation not in RECOMMENDATIONS:
        raise ValueError("invalid_reviewer_recommendation")

    return {
        "record_class": record_class,
        "action_context": ACTION_CONTEXT_CONTROLLED_WORKFLOW,
        "review_action_id": f"ACTION-{queue_record['review_id']}",
        "review_id": queue_record["review_id"],
        "decision_id": queue_record["decision_id"],
        "applicant_id": queue_record["applicant_id"],
        "ai_recommendation": ai_recommendation,
        "action": action,
        "reviewer_recommendation": reviewer_recommendation,
        "comment": comment.strip(),
        "reviewed_at_utc": timestamp_utc or utc_now(),
        "evidence_label": "controlled_review_demonstration",
    }


def validate_no_duplicate_final_action(existing_actions, new_action):
    review_id = new_action.get("review_id")
    for action in existing_actions:
        if action.get("review_id") == review_id:
            raise ValueError("duplicate_finalized_review_action")


def reconstruct_review_status(queue_records, action_records):
    statuses = {record["review_id"]: "PENDING" for record in queue_records}
    for action in action_records:
        review_id = action["review_id"]
        if review_id not in statuses:
            continue
        statuses[review_id] = "ACCEPTED" if action["action"] == "ACCEPT" else "OVERRIDDEN"
    return statuses
