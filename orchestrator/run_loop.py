"""Automated evolution loop runner.

Runs eval check scripts against the test project, scores results,
updates manifest, and tracks tier progression. Handles the non-mutation
phases (verify existing templates) and tracks consecutive passes for
tier advancement.

Usage:
    python orchestrator/run_loop.py [--rounds N] [--project cli-todo]
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add orchestrator/, tpls/cli/, and eval/gates/ to path for cross-module imports
_orch_dir = str(Path(__file__).parent)
_cli_dir = str(Path(__file__).parent.parent / "tpls" / "cli")
_gates_dir = str(Path(__file__).parent.parent / "eval" / "gates")
if _orch_dir not in sys.path:
    sys.path.insert(0, _orch_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)
if _gates_dir not in sys.path:
    sys.path.insert(0, _gates_dir)

from loop import prepare_mutation, decide_outcome, advance_phase, get_current_phase
from dispatch import prepare_workspace, cleanup_workspace
from hooks.utils.snapshot_manager import create_candidate, promote_candidate, load_manifest
from anti_gaming import validate_eval_integrity, validate_temporal_order, validate_no_regression


def run_check_script(script_path: str, project_path: str) -> dict:
    """Run a single check script and parse its YAML output."""
    try:
        result = subprocess.run(
            [sys.executable, script_path, project_path],
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).parent.parent)
        )
        output = result.stdout
        # Parse question and answer from YAML output
        question = ""
        answer = ""
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("question:"):
                question = line.split(":", 1)[1].strip().strip("'\"")
            elif line.startswith("answer:"):
                answer = line.split(":", 1)[1].strip().strip("'\"").lower()
        return {"question": question, "answer": answer, "raw": output}
    except Exception as e:
        return {"question": "unknown", "answer": "no", "raw": str(e)}


def get_active_tier_questions(tiers_dir: Path, tier: str) -> list[str]:
    """Get all question IDs active for the given tier and below."""
    import yaml
    tier_order = ["seed", "tier-2", "tier-3"]
    active_questions = []
    for t in tier_order:
        tier_file = tiers_dir / f"{t}.yaml"
        if tier_file.exists():
            data = yaml.safe_load(tier_file.read_text())
            active_questions.extend(data.get("questions", []))
        if t == tier:
            break
    return active_questions


def compute_pass_rates(results: list[dict], tier_questions: list[str]) -> dict:
    """Compute pass rates per category from check results."""
    # Map questions to categories
    categories = {}
    for r in results:
        qid = r["question"]
        if qid not in tier_questions:
            continue
        cat = qid.split(".")[0]  # e.g., "p1" from "p1.1"
        if cat not in categories:
            categories[cat] = {"passed": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["answer"] == "yes":
            categories[cat]["passed"] += 1

    pass_rates = {}
    total_passed = 0
    total_questions = 0
    for cat, counts in sorted(categories.items()):
        pass_rates[cat] = f"{counts['passed']}/{counts['total']}"
        total_passed += counts["passed"]
        total_questions += counts["total"]
    pass_rates["overall"] = f"{total_passed}/{total_questions}"
    return pass_rates


def run_evaluation_round(
    scripts_dir: Path,
    project_path: str,
    tiers_dir: Path,
    tier: str,
) -> tuple[dict, list[dict]]:
    """Run all check scripts and compute pass rates.

    Returns (pass_rates, results).
    """
    # Find all check scripts
    scripts = sorted(scripts_dir.glob("check_*.py"))

    # Get active questions for current tier
    tier_questions = get_active_tier_questions(tiers_dir, tier)

    results = []
    for script in scripts:
        r = run_check_script(str(script), project_path)
        results.append(r)

    pass_rates = compute_pass_rates(results, tier_questions)
    return pass_rates, results


def update_manifest_scores(manifest_path: Path, pass_rates: dict) -> dict:
    """Update manifest with new scores and handle tier progression."""
    manifest = json.loads(manifest_path.read_text())

    # Update active candidate's pass_rate
    active_id = manifest["active"]
    for c in manifest["candidates"]:
        if c["id"] == active_id:
            c["pass_rate"] = pass_rates
            break

    # Check if perfect score
    overall = pass_rates.get("overall", "0/0")
    parts = overall.split("/")
    passed = int(parts[0]) if len(parts) == 2 else 0
    total = int(parts[1]) if len(parts) == 2 else 0
    is_perfect = total > 0 and passed == total

    if is_perfect:
        manifest["consecutive_passes"] = manifest.get("consecutive_passes", 0) + 1
    else:
        manifest["consecutive_passes"] = 0

    # Check tier progression (100% for 3 consecutive runs)
    tier_order = ["seed", "tier-2", "tier-3"]
    current_tier = manifest.get("tier", "seed")
    consecutive = manifest["consecutive_passes"]

    advanced = False
    if is_perfect and consecutive >= 3:
        current_idx = tier_order.index(current_tier) if current_tier in tier_order else 0
        if current_idx + 1 < len(tier_order):
            manifest["tier"] = tier_order[current_idx + 1]
            manifest["consecutive_passes"] = 0
            advanced = True

    manifest["next_action"] = (
        f"tier advanced to {manifest['tier']}" if advanced
        else f"consecutive 100%: {manifest['consecutive_passes']}/3 for tier advance"
        if is_perfect
        else f"score: {overall}, consecutive reset to 0"
    )

    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def run_phase_prepare(manifest_path: Path, eval_dir: Path) -> dict:
    """Prepare phase: validate eval integrity, generate mutation directive."""
    # Anti-gaming: verify eval/ hasn't been tampered with
    integrity = validate_eval_integrity(eval_dir)
    if not integrity["valid"]:
        return {"phase": "prepare", "error": f"eval integrity failed: {integrity['violations']}"}

    result = prepare_mutation(manifest_path)
    advance_phase(manifest_path, {"directive": result["directive"]})
    return {"phase": "prepare", "directive": result["directive"], "target": result["target_category"]}


def run_phase_mutate(manifest_path: Path, snapshots_dir: Path) -> dict:
    """Mutate phase: prepare workspace for Pool-E mutation."""
    workspace = prepare_workspace(snapshots_dir)
    manifest = json.loads(manifest_path.read_text())
    directive = manifest.get("_last_directive", "")
    # Don't advance phase yet — orchestrator dispatches Pool-E first
    return {
        "phase": "mutate",
        "workspace": str(workspace),
        "directive": directive,
        "action_required": "dispatch Pool-E to mutate workspace, then run --phase execute",
    }


def run_phase_execute(manifest_path: Path, snapshots_dir: Path) -> dict:
    """Execute phase: capture workspace as candidate after Pool-E finishes."""
    workspace = snapshots_dir / "workspace"
    if not workspace.exists():
        return {"phase": "execute", "error": "workspace/ not found — was mutate phase run?"}

    manifest = json.loads(manifest_path.read_text())
    active_id = manifest.get("active")
    directive = manifest.get("_last_directive", "mutation")

    result = create_candidate(
        str(workspace), str(snapshots_dir), str(manifest_path),
        parent_id=active_id, mutation_description=directive
    )

    if result["id"] is None:
        advance_phase(manifest_path, {"candidate_id": "dedup"})
        return {"phase": "execute", "candidate_id": None, "dedup": True}

    advance_phase(manifest_path, {"candidate_id": result["id"]})
    return {
        "phase": "execute",
        "candidate_id": result["id"],
        "action_required": "dispatch Pool-E to execute spec cascade on test project, then dispatch Pool-V to verify, then run --phase verify",
    }


def run_phase_verify(
    manifest_path: Path, scripts_dir: Path, project_path: str,
    tiers_dir: Path, eval_dir: Path, evidence_dir: Path,
) -> dict:
    """Verify phase: run evaluation and anti-gaming checks."""
    # Anti-gaming: temporal order check
    temporal = validate_temporal_order(scripts_dir, evidence_dir)
    if not temporal["valid"]:
        return {"phase": "verify", "error": f"temporal order violation: {temporal['violations']}"}

    manifest = json.loads(manifest_path.read_text())
    tier = manifest.get("tier", "seed")

    pass_rates, results = run_evaluation_round(scripts_dir, project_path, tiers_dir, tier)

    # Update the LAST candidate's pass_rate (not the active one)
    candidate_id = manifest.get("_last_candidate")
    if candidate_id and candidate_id != "dedup":
        for c in manifest.get("candidates", []):
            if c["id"] == candidate_id:
                c["pass_rate"] = pass_rates
                break
        manifest_path.write_text(json.dumps(manifest, indent=2))

    advance_phase(manifest_path, {"evidence_path": str(evidence_dir)})

    failed = [r["question"] for r in results if r["answer"] == "no"]
    return {
        "phase": "verify",
        "pass_rates": pass_rates,
        "failed": failed,
        "candidate_id": candidate_id,
    }


def run_phase_decide(manifest_path: Path, snapshots_dir: Path) -> dict:
    """Decide phase: compare candidate vs active, promote or reject."""
    manifest = json.loads(manifest_path.read_text())
    candidate_id = manifest.get("_last_candidate")

    if not candidate_id or candidate_id == "dedup":
        advance_phase(manifest_path, {"outcome": "reject"})
        return {"phase": "decide", "outcome": "reject", "reason": "duplicate content"}

    # Anti-gaming: no-regression check
    regression = validate_no_regression(manifest_path, candidate_id)
    if not regression["valid"]:
        advance_phase(manifest_path, {"outcome": "reject"})
        return {"phase": "decide", "outcome": "reject", "reason": f"suspicious regression: {regression['suspicious_flips']}"}

    outcome = decide_outcome(manifest_path, candidate_id)

    if outcome == "promote":
        promote_candidate(candidate_id, str(snapshots_dir), str(manifest_path))

    advance_phase(manifest_path, {"outcome": outcome})
    return {"phase": "decide", "outcome": outcome, "candidate_id": candidate_id}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run evolution loop")
    parser.add_argument("--rounds", type=int, default=100)
    parser.add_argument("--project", default="cli-todo")
    parser.add_argument("--phase", choices=["prepare", "mutate", "execute", "verify", "decide"],
                        help="Run a single phase of the evolution loop")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    manifest_path = repo_root / "orchestrator" / "manifest.json"
    scripts_dir = repo_root / "eval" / "scripts"
    tiers_dir = repo_root / "eval" / "tiers"
    eval_dir = repo_root / "eval"
    snapshots_dir = repo_root / "tpls" / "snapshots"
    project_path = str(repo_root / "regs" / "test-regs" / f"{args.project}-regs")
    evidence_dir = Path(project_path)

    if args.phase:
        # Single-phase mode: run one phase, output JSON
        if args.phase == "prepare":
            result = run_phase_prepare(manifest_path, eval_dir)
        elif args.phase == "mutate":
            result = run_phase_mutate(manifest_path, snapshots_dir)
        elif args.phase == "execute":
            result = run_phase_execute(manifest_path, snapshots_dir)
        elif args.phase == "verify":
            result = run_phase_verify(manifest_path, scripts_dir, project_path, tiers_dir, eval_dir, evidence_dir)
        elif args.phase == "decide":
            result = run_phase_decide(manifest_path, snapshots_dir)
        print(json.dumps(result, indent=2))
        return

    # Existing rounds-based evaluation mode
    print(f"=== Evolution Loop: {args.rounds} rounds on {args.project} ===\n")

    prev_tier = None
    converged_at = None

    for round_num in range(1, args.rounds + 1):
        manifest = json.loads(manifest_path.read_text())
        tier = manifest.get("tier", "seed")

        if tier != prev_tier:
            print(f"\n--- Tier: {tier} ---")
            prev_tier = tier

        # Run evaluation
        pass_rates, results = run_evaluation_round(
            scripts_dir, project_path, tiers_dir, tier
        )

        # Update manifest
        manifest = update_manifest_scores(manifest_path, pass_rates)

        overall = pass_rates.get("overall", "0/0")
        consecutive = manifest.get("consecutive_passes", 0)

        # Print round summary
        status = "✓" if "yes" not in [r["answer"] for r in results if r["answer"] == "no"] else "○"
        failed = [r["question"] for r in results if r["answer"] == "no"]
        fail_str = f" FAILED: {', '.join(failed)}" if failed else ""
        print(f"  Round {round_num:3d}: {overall} | consecutive: {consecutive}/3 | tier: {manifest['tier']}{fail_str}")

        # Check convergence
        parts = overall.split("/")
        passed = int(parts[0]) if len(parts) == 2 else 0
        total = int(parts[1]) if len(parts) == 2 else 0

        if manifest["tier"] == "tier-3" and passed == total and consecutive >= 3:
            converged_at = round_num
            print(f"\n=== CONVERGED at round {round_num}: all tiers at 100% ===")
            break

        # If we just advanced a tier, we might need new check scripts
        if manifest["tier"] != tier:
            print(f"\n  *** TIER ADVANCED: {tier} → {manifest['tier']} ***")
            print(f"  New check scripts needed for {manifest['tier']} questions.")
            print(f"  Pausing for pool-t to write scripts.\n")
            # Signal that we need new scripts — don't break, let the caller handle
            break

    if converged_at:
        print(f"\nFinal: converged at round {converged_at}")
    else:
        manifest = json.loads(manifest_path.read_text())
        print(f"\nFinal state: tier={manifest['tier']}, consecutive={manifest.get('consecutive_passes', 0)}")

    return manifest


if __name__ == "__main__":
    main()
