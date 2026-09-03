"""Run a live screening evaluation with optional protected-field mitigation."""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence import build_final_screening_result, build_screening_control  # noqa: E402
from explainability import build_explanation, build_technical_failure_explanation, validate_explanation  # noqa: E402
from fairness_analysis import evaluation_records, group_metrics  # noqa: E402
from logging_layer import RECORD_CLASS_REAL_EVIDENCE, build_decision_log_record, validate_decision_log_record  # noqa: E402
from review import build_review_queue_record, route_for_review, validate_review_queue_record  # noqa: E402
from screening import build_decision_context, build_messages, load_prompt  # noqa: E402
from validation import validate_final_screening_result, validate_provider_output  # noqa: E402
from watsonx_client import WatsonxChatClient  # noqa: E402


PROTECTED_FIELDS = {"age", "gender", "nationality"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )


def model_visible_context(application, variant):
    context = build_decision_context(application)
    if variant == "mitigated":
        return {key: value for key, value in context.items() if key not in PROTECTED_FIELDS}
    return context


def technical_failure(applicant_id, attempts, validation_errors, raw_response_hashes):
    return {
        "applicant_id": applicant_id,
        "status": "TECHNICAL_FAILURE",
        "attempts": attempts,
        "validation_errors": list(validation_errors),
        "raw_response_sha256": list(raw_response_hashes),
    }


def evaluate_application(application, model_client, prompt_text, variant):
    decision_context = model_visible_context(application, variant)
    applicant_id = application["applicant_id"]
    raw_hashes = []

    messages = build_messages(prompt_text, decision_context, retry=False)
    raw = model_client.chat(messages)
    raw_hashes.append(hashlib.sha256(raw.encode("utf-8")).hexdigest().upper())
    control = build_screening_control(decision_context)
    validation = validate_provider_output(raw, applicant_id, decision_context, control)
    if validation["valid"]:
        result = build_final_screening_result(validation["parsed"], decision_context)
        final_validation = validate_final_screening_result(result, applicant_id, decision_context)
        if final_validation["valid"]:
            return {
                "applicant_id": applicant_id,
                "status": "VALID",
                "attempts": 1,
                "retry_used": False,
                "decision_context": decision_context,
                "provider_response": validation["parsed"],
                "result": result,
                "validation_errors": [],
                "raw_response_sha256": raw_hashes,
            }
        validation_errors = final_validation["errors"]
    else:
        validation_errors = validation["errors"]

    retry_messages = build_messages(prompt_text, decision_context, retry=True, validation_errors=validation_errors)
    retry_raw = model_client.chat(retry_messages)
    raw_hashes.append(hashlib.sha256(retry_raw.encode("utf-8")).hexdigest().upper())
    retry_validation = validate_provider_output(retry_raw, applicant_id, decision_context, control)
    if retry_validation["valid"]:
        result = build_final_screening_result(retry_validation["parsed"], decision_context)
        final_validation = validate_final_screening_result(result, applicant_id, decision_context)
        if final_validation["valid"]:
            return {
                "applicant_id": applicant_id,
                "status": "VALID",
                "attempts": 2,
                "retry_used": True,
                "decision_context": decision_context,
                "provider_response": retry_validation["parsed"],
                "result": result,
                "validation_errors": validation_errors,
                "raw_response_sha256": raw_hashes,
            }
        return technical_failure(applicant_id, 2, validation_errors + final_validation["errors"], raw_hashes)
    return technical_failure(applicant_id, 2, validation_errors + retry_validation["errors"], raw_hashes)


def build_decision_record(application, slot, prompt_hash, variant):
    if slot["status"] == "VALID":
        explanation = build_explanation(slot["result"], slot["decision_context"])
        explanation_errors = validate_explanation(explanation, slot["result"])
        if explanation_errors:
            raise RuntimeError(f"explanation validation failed for {slot['applicant_id']}: {explanation_errors}")
        routing = route_for_review(slot["result"])
        screening_record = {"status": "VALID", "result": slot["result"], "retry_used": slot["retry_used"]}
    else:
        explanation = build_technical_failure_explanation(slot["applicant_id"], slot["validation_errors"])
        routing = route_for_review({"final_status": "TECHNICAL_FAILURE"})
        screening_record = {
            "final_status": "TECHNICAL_FAILURE",
            "validation_errors": slot["validation_errors"],
            "retry_used": slot["attempts"] > 1,
        }

    record = build_decision_log_record(
        application,
        screening_record,
        explanation,
        routing,
        prompt_hash,
        decision_id=f"{variant}-{slot['applicant_id']}",
        record_class=RECORD_CLASS_REAL_EVIDENCE,
        evidence_label=("controlled_baseline_evaluation" if variant == "baseline" else "protected_attribute_mitigation_evaluation"),
    )
    record["evaluation_variant"] = variant
    record["provider_provenance"] = {
        "provider_call_performed": True,
        "raw_response_sha256": list(slot["raw_response_sha256"]),
        "attempt_count": slot["attempts"],
    }
    record["screening"]["model_declared_key_factor_fields"] = [
        factor["field"] for factor in record["screening"].get("decision_factors", [])
    ]
    errors = validate_decision_log_record(record)
    if errors:
        raise RuntimeError(f"decision log validation failed for {slot['applicant_id']}: {errors}")
    return record


def build_review_queue(decisions):
    queue = []
    for decision in decisions:
        if decision["routing"]["review_required"]:
            record = build_review_queue_record(decision)
            errors = validate_review_queue_record(record)
            if errors:
                raise RuntimeError(f"review queue validation failed for {decision['identity']['applicant_id']}: {errors}")
            queue.append(record)
    return queue


def run(args):
    applications = read_json(args.dataset)
    prompt_text = load_prompt(args.prompt)
    prompt_hash = sha256(args.prompt)
    model_client = WatsonxChatClient(json_response_mode=True)

    slots = [evaluate_application(application, model_client, prompt_text, args.variant) for application in applications]
    decisions = [
        build_decision_record(application, slot, prompt_hash, args.variant)
        for application, slot in zip(applications, slots)
    ]
    queue = build_review_queue(decisions)
    metrics = group_metrics(evaluation_records(decisions))

    output_dir = Path(args.output_dir)
    write_jsonl(output_dir / f"{args.variant}_decisions.jsonl", decisions)
    write_jsonl(output_dir / f"{args.variant}_review_queue.jsonl", queue)
    write_json(output_dir / f"{args.variant}_fairness_metrics.json", metrics)
    write_json(
        output_dir / f"{args.variant}_run_summary.json",
        {
            "schema_version": "screening_evaluation_summary_v1",
            "generated_at_utc": utc_now(),
            "variant": args.variant,
            "application_count": len(applications),
            "decision_count": len(decisions),
            "review_queue_count": len(queue),
            "provider_call_count": sum(slot["attempts"] for slot in slots),
            "technical_failure_count": sum(1 for slot in slots if slot["status"] != "VALID"),
            "prompt_sha256": prompt_hash,
        },
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Run the loan screening evaluation pipeline.")
    parser.add_argument("--variant", choices=("baseline", "mitigated"), required=True)
    parser.add_argument("--dataset", default=str(ROOT / "data" / "applications_60.json"))
    parser.add_argument("--prompt", default=str(ROOT / "prompts" / "screening_v1.txt"))
    parser.add_argument("--output-dir", default=str(ROOT / "outputs"))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
