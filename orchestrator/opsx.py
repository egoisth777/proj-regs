"""CLI entry point for evolution loop operations (/opsx command).

Usage:
    python opsx.py status [--manifest PATH]
    python opsx.py tier [--manifest PATH]
    python opsx.py new-feature NAME --changes-dir PATH --template-dir PATH
    python opsx.py rollback CANDIDATE_ID [--manifest PATH] [--snapshots-dir PATH]
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


def cmd_status(manifest_path: Path) -> str:
    """Show current evolution loop state."""
    data = json.loads(Path(manifest_path).read_text())
    active = data.get("active", "unknown")
    phase = data.get("phase", "unknown")
    tier = data.get("tier", "unknown")
    next_action = data.get("next_action", "none")

    pass_rate = {}
    for c in data.get("candidates", []):
        if c["id"] == active:
            pass_rate = c.get("pass_rate", {})
            break

    lines = [
        f"Active: {active}",
        f"Phase: {phase}",
        f"Tier: {tier}",
        f"Pass rate: {pass_rate if pass_rate else 'none yet'}",
        f"Candidates: {len(data.get('candidates', []))}",
        f"Promoted: {len(data.get('promoted', []))}",
        f"Next action: {next_action}",
    ]
    return "\n".join(lines)


def cmd_tier(manifest_path: Path) -> str:
    """Show tier progression status."""
    data = json.loads(Path(manifest_path).read_text())
    tier = data.get("tier", "seed")
    consecutive = data.get("consecutive_passes", 0)

    lines = [
        f"Current tier: {tier}",
        f"Consecutive 100% passes: {consecutive}",
        f"Need 3 consecutive to advance",
    ]
    return "\n".join(lines)


def _next_feature_number(changes_dir: Path) -> int:
    """Scan feat-NNN- folders and return next sequence number."""
    pattern = re.compile(r"^feat-(\d{3})-")
    max_num = 0
    if changes_dir.exists():
        for entry in changes_dir.iterdir():
            if entry.is_dir():
                m = pattern.match(entry.name)
                if m:
                    max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def cmd_new_feature(
    name: str,
    changes_dir: Path,
    template_dir: Path,
) -> str:
    """Create a new feature folder with auto-incrementing sequence number."""
    num = _next_feature_number(changes_dir)
    folder_name = f"feat-{num:03d}-{name}"
    feat_dir = Path(changes_dir) / folder_name
    feat_dir.mkdir(parents=True)

    tpl = Path(template_dir)
    for f in tpl.iterdir():
        if f.is_file():
            shutil.copy2(str(f), str(feat_dir / f.name))

    return f"Created {folder_name}"


def main():
    parser = argparse.ArgumentParser(description="omni evolution loop operations")
    sub = parser.add_subparsers(dest="command")

    p_status = sub.add_parser("status", help="show current loop state")
    p_status.add_argument("--manifest", default="orchestrator/manifest.json")

    p_tier = sub.add_parser("tier", help="show tier progression")
    p_tier.add_argument("--manifest", default="orchestrator/manifest.json")

    p_feat = sub.add_parser("new-feature", help="create feature folder")
    p_feat.add_argument("name", help="feature name (e.g. add-task)")
    p_feat.add_argument("--changes-dir", required=True)
    p_feat.add_argument("--template-dir", required=True)

    p_rb = sub.add_parser("rollback", help="rollback to a candidate")
    p_rb.add_argument("candidate_id")
    p_rb.add_argument("--manifest", default="orchestrator/manifest.json")
    p_rb.add_argument("--snapshots-dir", default="tpls/snapshots")

    args = parser.parse_args()

    if args.command == "status":
        print(cmd_status(Path(args.manifest)))
    elif args.command == "tier":
        print(cmd_tier(Path(args.manifest)))
    elif args.command == "new-feature":
        print(cmd_new_feature(args.name, Path(args.changes_dir), Path(args.template_dir)))
    elif args.command == "rollback":
        _cli_dir = str(Path(__file__).parent.parent / "tpls" / "snapshots" / "candidate-0" / "cli")
        if _cli_dir not in sys.path:
            sys.path.insert(0, _cli_dir)
        from hooks.utils.snapshot_manager import rollback_to
        rollback_to(args.candidate_id, args.snapshots_dir, args.manifest)
        print(f"Rolled back to {args.candidate_id}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
