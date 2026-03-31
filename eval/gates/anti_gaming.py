"""Integrity validation between evolution loop phases.

Stateless checks the orchestrator calls to detect gaming, corruption,
or temporal violations.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from frozen_lock import verify_lock


def validate_eval_integrity(eval_dir: Path) -> dict[str, Any]:
    """Verify eval/ matches FROZEN.lock.

    Returns {"valid": bool, "violations": list[str]}.
    """
    ed = Path(eval_dir)
    if not (ed / "FROZEN.lock").exists():
        return {"valid": False, "violations": ["FROZEN.lock missing"]}

    ok, mismatches = verify_lock(ed)
    return {"valid": ok, "violations": mismatches}


def validate_temporal_order(
    scripts_dir: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Check that pool-t scripts have earlier mtimes than pool-v evidence.

    Returns {"valid": bool, "violations": list[str]}.
    """
    sd = Path(scripts_dir)
    ed = Path(evidence_dir)
    violations: list[str] = []

    script_files = [f for f in sd.rglob("*") if f.is_file()]
    if not script_files:
        return {"valid": True, "violations": []}

    latest_script = max(f.stat().st_mtime for f in script_files)

    evidence_files = [f for f in ed.rglob("*") if f.is_file()]
    if not evidence_files:
        return {"valid": True, "violations": []}

    earliest_evidence = min(f.stat().st_mtime for f in evidence_files)

    if earliest_evidence < latest_script:
        violations.append(
            f"evidence file predates script file: "
            f"earliest evidence mtime={earliest_evidence:.0f} < "
            f"latest script mtime={latest_script:.0f}"
        )

    return {"valid": len(violations) == 0, "violations": violations}


def _parse_rate(rate_str: str) -> tuple[int, int]:
    """Parse 'N/M' into (N, M)."""
    parts = rate_str.split("/")
    if len(parts) != 2:
        return (0, 0)
    try:
        return (int(parts[0]), int(parts[1]))
    except ValueError:
        return (0, 0)


def validate_no_regression(
    manifest_path: Path,
    candidate_id: str,
) -> dict[str, Any]:
    """Check that score regressions correlate with meaningful mutations.

    A regression where the candidate has the same sha256 as its parent
    (no actual content change) is suspicious.

    Returns {"valid": bool, "suspicious_flips": list[str]}.
    """
    manifest = json.loads(Path(manifest_path).read_text())
    suspicious: list[str] = []

    candidate = None
    parent = None
    for c in manifest.get("candidates", []):
        if c["id"] == candidate_id:
            candidate = c
    if candidate:
        for c in manifest.get("candidates", []):
            if c["id"] == candidate.get("parent"):
                parent = c

    if not candidate or not parent:
        return {"valid": True, "suspicious_flips": []}

    candidate_rates = candidate.get("pass_rate", {})
    parent_rates = parent.get("pass_rate", {})

    for cat in parent_rates:
        if cat == "overall":
            continue
        p_passed, p_total = _parse_rate(parent_rates.get(cat, "0/0"))
        c_passed, c_total = _parse_rate(candidate_rates.get(cat, "0/0"))

        if c_total > 0 and p_total > 0 and c_passed < p_passed:
            if candidate.get("sha256") == parent.get("sha256"):
                suspicious.append(
                    f"{cat}: regressed from {p_passed}/{p_total} to {c_passed}/{c_total} "
                    f"with identical content hash"
                )

    return {"valid": len(suspicious) == 0, "suspicious_flips": suspicious}
