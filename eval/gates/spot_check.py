"""Spot-check audit: random sampling of pool-v evidence for independent verification."""

import random
from pathlib import Path
from typing import Any, Optional


def _has_judgment_evidence(answer: dict) -> bool:
    """Check if any evidence item is reasoning-based (higher gaming risk)."""
    for ev in answer.get("evidence", []):
        if ev.get("type") == "reasoning":
            return True
    return False


def select_spot_checks(
    answers: list[dict],
    sample_size: int = 3,
) -> list[dict]:
    """Randomly select answers to verify, preferring judgment-based evidence.

    Judgment evidence (reasoning type) is weighted 3x for selection since
    it's harder to verify automatically and more susceptible to gaming.
    """
    if not answers:
        return []
    if len(answers) <= sample_size:
        return list(answers)

    # build weighted pool: reasoning items get 3x weight
    weighted: list[dict] = []
    for a in answers:
        weight = 3 if _has_judgment_evidence(a) else 1
        weighted.extend([a] * weight)

    selected: list[dict] = []
    seen: set[str] = set()
    attempts = 0
    max_attempts = sample_size * 20

    while len(selected) < sample_size and attempts < max_attempts:
        pick = random.choice(weighted)
        qid = pick.get("question", "")
        if qid not in seen:
            seen.add(qid)
            selected.append(pick)
        attempts += 1

    return selected


def verify_file_evidence(
    file_path: str,
    project_path: Path,
) -> dict[str, Any]:
    """Independently verify that a cited file exists at the given path.

    Returns {"verified": bool, "discrepancy": str | None}
    """
    full_path = Path(project_path) / file_path
    if full_path.exists():
        return {"verified": True, "discrepancy": None}
    return {"verified": False, "discrepancy": f"file not found: {file_path}"}
