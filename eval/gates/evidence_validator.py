"""Parse and validate pool-v evidence reports (YAML format)."""

from pathlib import Path
from typing import Any

import yaml


def parse_evidence_report(report_path: Path) -> dict[str, Any]:
    """Parse a YAML evidence report. Raises ValueError on invalid YAML."""
    p = Path(report_path)
    if not p.exists():
        raise FileNotFoundError(f"Evidence report not found: {report_path}")
    raw = p.read_text()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ValueError(f"invalid YAML: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("invalid YAML: expected a mapping at top level")
    return data


def _validate_evidence_item(item: dict, question_id: str) -> list[str]:
    """Validate a single evidence item. Returns list of error strings."""
    errors = []
    ev_type = item.get("type")
    if not ev_type:
        errors.append(f"{question_id}: evidence item missing 'type'")
        return errors

    if ev_type == "file_timestamp":
        if not item.get("path"):
            errors.append(f"{question_id}: file_timestamp evidence missing 'path'")

    elif ev_type == "command_output":
        if not item.get("command"):
            errors.append(f"{question_id}: command_output evidence missing 'command'")

    elif ev_type == "reasoning":
        text = item.get("text", "")
        if len(text) < 20:
            errors.append(
                f"{question_id}: reasoning evidence must be >= 20 chars, got {len(text)}"
            )

    return errors


def validate_evidence(report_path: Path) -> dict[str, Any]:
    """Validate an evidence report.

    Returns {"valid": bool, "errors": list[str], "parsed": list[dict]}
    """
    data = parse_evidence_report(report_path)
    errors: list[str] = []
    parsed: list[dict] = []

    answers = data.get("answers")
    if not answers:
        return {"valid": False, "errors": ["report missing 'answers' key"], "parsed": []}

    for i, answer in enumerate(answers):
        qid = answer.get("question")
        if not qid:
            errors.append(f"answer[{i}]: missing 'question' field")
            continue

        ans_val = answer.get("answer")
        if ans_val is None:
            errors.append(f"{qid}: missing 'answer' field")
            continue
        # YAML parses bare `yes`/`no` as booleans; accept both bool and string forms
        if isinstance(ans_val, bool):
            normalized = "yes" if ans_val else "no"
        else:
            normalized = str(ans_val).lower()
        if normalized not in ("yes", "no"):
            errors.append(f"{qid}: answer must be yes/no, got '{ans_val}'")
            continue

        evidence = answer.get("evidence")
        if not evidence:
            errors.append(f"{qid}: missing or empty evidence list")
            continue

        item_errors = []
        for ev_item in evidence:
            item_errors.extend(_validate_evidence_item(ev_item, qid))
        errors.extend(item_errors)

        if not item_errors:
            parsed.append(answer)

    return {"valid": len(errors) == 0, "errors": errors, "parsed": parsed}
