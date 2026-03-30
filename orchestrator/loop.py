"""Phase state machine for the self-evolution loop.

Manages the 5-phase cycle: prepare -> mutate -> execute -> verify -> decide.
The orchestrator agent calls these functions to advance the loop.
"""

import json
from pathlib import Path
from typing import Any, Optional

import yaml


# Valid phase transitions (current -> next)
VALID_TRANSITIONS = {
    "prepare": "mutate",
    "mutate": "execute",
    "execute": "verify",
    "verify": "decide",
    "decide": "prepare",
}

TIER_ORDER = ["seed", "tier-2", "tier-3"]

CATEGORY_NAMES = {
    "p1": "spec cascade",
    "p2": "role boundary",
    "p3": "orchestration",
    "p4": "ssot integrity",
    "o1": "correctness",
    "o2": "test quality",
    "o3": "code quality",
    "o4": "spec fidelity",
}


def _load(manifest_path: Path) -> dict:
    p = Path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    return json.loads(p.read_text())


def _save(manifest_path: Path, data: dict) -> None:
    p = Path(manifest_path)
    p.write_text(json.dumps(data, indent=2))


def get_current_phase(manifest_path: Path) -> str:
    """Return the current phase from manifest.json."""
    return _load(manifest_path)["phase"]


def advance_phase(manifest_path: Path, result: dict) -> str:
    """Advance to the next phase. Validates the transition is legal.

    Args:
        manifest_path: Path to manifest.json.
        result: Phase-specific data to store. Keys vary by phase:
            - prepare->mutate: {"directive": str}
            - mutate->execute: {"candidate_id": str}
            - execute->verify: {"test_domain": str}
            - verify->decide: {"evidence_path": str}
            - decide->prepare: {"outcome": str}

    Returns the new phase name.
    """
    manifest = _load(manifest_path)
    current = manifest["phase"]
    next_phase = VALID_TRANSITIONS.get(current)
    if next_phase is None:
        raise ValueError(f"invalid transition: unknown phase '{current}'")

    manifest["phase"] = next_phase

    # Store phase-specific results
    if current == "prepare" and "directive" in result:
        manifest["_last_directive"] = result["directive"]
    elif current == "mutate" and "candidate_id" in result:
        manifest["_last_candidate"] = result["candidate_id"]
    elif current == "execute" and "test_domain" in result:
        manifest["test_domain"] = result["test_domain"]
    elif current == "verify" and "evidence_path" in result:
        manifest["_last_evidence"] = result["evidence_path"]
    elif current == "decide" and "outcome" in result:
        manifest["next_action"] = f"last outcome: {result['outcome']}, continuing loop"

    _save(manifest_path, manifest)
    return next_phase


def _parse_pass_rate(rate_str: str) -> tuple[int, int]:
    """Parse '6/9' into (6, 9)."""
    parts = rate_str.split("/")
    if len(parts) != 2:
        return (0, 0)
    try:
        return (int(parts[0]), int(parts[1]))
    except ValueError:
        return (0, 0)


def prepare_mutation(manifest_path: Path) -> dict[str, Any]:
    """Analyze pass_rate to generate a mutation directive targeting the weakest area.

    Returns {"directive": str, "target_category": str | None}.
    """
    manifest = _load(manifest_path)
    active_id = manifest.get("active")
    active = None
    for c in manifest.get("candidates", []):
        if c["id"] == active_id:
            active = c
            break

    if not active or not active.get("pass_rate"):
        return {
            "directive": "general improvement — no pass rate data yet, focus on spec cascade and role enforcement fundamentals",
            "target_category": None,
        }

    pass_rate = active["pass_rate"]
    categories = {k: v for k, v in pass_rate.items() if k != "overall"}

    if not categories:
        return {
            "directive": "general improvement — no category breakdown available",
            "target_category": None,
        }

    worst_cat = None
    worst_ratio = 1.1
    for cat, rate in categories.items():
        passed, total = _parse_pass_rate(rate)
        if total == 0:
            continue
        ratio = passed / total
        if ratio < worst_ratio:
            worst_ratio = ratio
            worst_cat = cat

    if worst_cat is None or worst_ratio >= 1.0:
        return {
            "directive": "all categories passing — focus on robustness and edge cases",
            "target_category": None,
        }

    cat_name = CATEGORY_NAMES.get(worst_cat, worst_cat)
    passed, total = _parse_pass_rate(categories[worst_cat])
    return {
        "directive": f"improve {cat_name} ({worst_cat}) — currently at {passed}/{total}. analyze template weaknesses that cause {cat_name} failures and strengthen enforcement.",
        "target_category": worst_cat,
    }


def decide_outcome(manifest_path: Path, candidate_id: str) -> str:
    """Compare candidate pass_rate vs active. Returns 'promote', 'reject', or 'tie'."""
    manifest = _load(manifest_path)

    active_id = manifest.get("active")
    active_rate = {}
    candidate_rate = {}

    for c in manifest.get("candidates", []):
        if c["id"] == active_id:
            active_rate = c.get("pass_rate", {})
        if c["id"] == candidate_id:
            candidate_rate = c.get("pass_rate", {})

    active_overall = active_rate.get("overall", "0/0")
    candidate_overall = candidate_rate.get("overall", "0/0")

    a_passed, a_total = _parse_pass_rate(active_overall)
    c_passed, c_total = _parse_pass_rate(candidate_overall)

    if c_total == 0 and a_total == 0:
        return "tie"
    if c_total > 0 and a_total > 0:
        c_ratio = c_passed / c_total
        a_ratio = a_passed / a_total
        if c_ratio > a_ratio:
            return "promote"
        elif c_ratio < a_ratio:
            return "reject"
        else:
            return "tie"
    if c_total > 0:
        return "promote"
    return "tie"


def check_tier_progression(
    manifest_path: Path,
    tiers_dir: Path,
) -> dict[str, Any]:
    """Check if the current tier should advance.

    Tier advances when at 100% pass rate for 3 consecutive runs.
    Returns {"should_advance": bool, "current_tier": str, "next_tier": str | None}.
    """
    manifest = _load(manifest_path)
    current_tier = manifest.get("tier", "seed")
    consecutive = manifest.get("consecutive_passes", 0)

    active_id = manifest.get("active")
    active_rate = {}
    for c in manifest.get("candidates", []):
        if c["id"] == active_id:
            active_rate = c.get("pass_rate", {})
            break

    overall = active_rate.get("overall", "0/0")
    passed, total = _parse_pass_rate(overall)
    is_perfect = total > 0 and passed == total

    current_idx = TIER_ORDER.index(current_tier) if current_tier in TIER_ORDER else 0
    next_tier = TIER_ORDER[current_idx + 1] if current_idx + 1 < len(TIER_ORDER) else None

    should_advance = is_perfect and consecutive >= 3 and next_tier is not None

    return {
        "should_advance": should_advance,
        "current_tier": current_tier,
        "next_tier": next_tier,
    }
