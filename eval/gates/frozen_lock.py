"""Generate and verify FROZEN.lock for eval/ directory integrity."""

import hashlib
import json
import sys
from pathlib import Path


def generate_lock(eval_dir: Path) -> dict:
    """Generate sha-256 hashes for all files in eval/ (excluding FROZEN.lock itself)."""
    hashes = {}
    for fpath in sorted(eval_dir.rglob("*")):
        if fpath.is_file() and fpath.name != "FROZEN.lock":
            rel = str(fpath.relative_to(eval_dir))
            hashes[rel] = hashlib.sha256(fpath.read_bytes()).hexdigest()
    return {"version": "1.0", "hashes": hashes}


def verify_lock(eval_dir: Path) -> tuple[bool, list[str]]:
    """Verify eval/ files match FROZEN.lock. Returns (ok, list_of_mismatches)."""
    lock_path = eval_dir / "FROZEN.lock"
    if not lock_path.exists():
        return False, ["FROZEN.lock missing"]

    lock = json.loads(lock_path.read_text())
    expected = lock.get("hashes", {})
    actual = generate_lock(eval_dir)["hashes"]

    mismatches = []
    for path, expected_hash in expected.items():
        actual_hash = actual.get(path)
        if actual_hash is None:
            mismatches.append(f"MISSING: {path}")
        elif actual_hash != expected_hash:
            mismatches.append(f"CHANGED: {path}")

    for path in actual:
        if path not in expected:
            mismatches.append(f"NEW: {path}")

    return len(mismatches) == 0, mismatches


if __name__ == "__main__":
    eval_dir = Path(__file__).parent.parent
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        ok, mismatches = verify_lock(eval_dir)
        if ok:
            print("FROZEN.lock: OK")
        else:
            print("FROZEN.lock: MISMATCH")
            for m in mismatches:
                print(f"  {m}")
            sys.exit(1)
    else:
        lock = generate_lock(eval_dir)
        lock_path = eval_dir / "FROZEN.lock"
        lock_path.write_text(json.dumps(lock, indent=2))
        print(f"Generated FROZEN.lock with {len(lock['hashes'])} entries")
