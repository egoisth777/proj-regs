#!/usr/bin/env python3
"""Check o2.1: Does line coverage exceed 70%?

Tries to run coverage via pytest-cov. Falls back to a heuristic based on
test count vs source line count.
"""

import os
import re
import subprocess
import sys
import yaml


def count_source_lines(directory):
    """Count non-blank, non-comment Python source lines in a directory."""
    total = 0
    if not os.path.isdir(directory):
        return 0
    for root, _dirs, files in os.walk(directory):
        # Skip test directories
        parts = root.replace("\\", "/").split("/")
        if any(p in ("tests", "test", "__pycache__") for p in parts):
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            if f.startswith("test_") or f.endswith("_test.py") or f == "conftest.py":
                continue
            fp = os.path.join(root, f)
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        stripped = line.strip()
                        if stripped and not stripped.startswith("#"):
                            total += 1
            except OSError:
                pass
    return total


def count_test_functions(directory):
    """Count test functions in test files."""
    count = 0
    if not os.path.isdir(directory):
        return 0
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if not f.endswith(".py"):
                continue
            if not (f.startswith("test_") or f.endswith("_test.py")):
                continue
            fp = os.path.join(root, f)
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                func_pattern = re.compile(
                    r"^\s*(?:def|async\s+def)\s+test_\w+\s*\(", re.MULTILINE
                )
                count += len(func_pattern.findall(content))
            except OSError:
                pass
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o2_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    artifacts_dir = os.path.join(project_path, "artifacts")
    src_dir = os.path.join(project_path, "artifacts", "src")
    cwd = artifacts_dir if os.path.isdir(artifacts_dir) else project_path

    evidence = []
    answer = "no"
    coverage_pct = None

    # Strategy 1: Try running pytest-cov
    try:
        source_arg = src_dir if os.path.isdir(src_dir) else artifacts_dir
        if os.path.isdir(source_arg):
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "--co", "-q",
                 f"--cov={source_arg}", "--cov-report=term-missing", "--tb=no", "-q"],
                capture_output=True, text=True,
                cwd=cwd,
                timeout=120
            )

            if proc.returncode in (0, 1, 5):
                # Parse coverage percentage from output
                # Look for "TOTAL ... XX%" pattern
                total_pattern = re.compile(r"TOTAL\s+\d+\s+\d+\s+(\d+)%")
                match = total_pattern.search(proc.stdout)
                if match:
                    coverage_pct = int(match.group(1))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Strategy 2: Try coverage run directly
    if coverage_pct is None:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "coverage", "run", "-m", "pytest", "-q", "--tb=no"],
                capture_output=True, text=True,
                cwd=cwd,
                timeout=120
            )
            if proc.returncode in (0, 1):
                report_proc = subprocess.run(
                    [sys.executable, "-m", "coverage", "report"],
                    capture_output=True, text=True,
                    cwd=cwd,
                    timeout=30
                )
                if report_proc.returncode == 0:
                    total_pattern = re.compile(r"TOTAL\s+\d+\s+\d+\s+(\d+)%")
                    match = total_pattern.search(report_proc.stdout)
                    if match:
                        coverage_pct = int(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    if coverage_pct is not None:
        answer = "yes" if coverage_pct >= 70 else "no"
        evidence.append({
            "type": "command_output",
            "command": "coverage report",
            "stdout": f"Coverage: {coverage_pct}%",
            "exit_code": 0,
            "detail": f"Line coverage is {coverage_pct}% ({'>=70% -- OK' if coverage_pct >= 70 else '<70% -- INSUFFICIENT'})"
        })
    else:
        # Strategy 3: Heuristic based on test/source ratio
        source_dir = src_dir if os.path.isdir(src_dir) else artifacts_dir
        source_lines = count_source_lines(source_dir)

        test_dirs = [
            os.path.join(project_path, "artifacts", "tests"),
            os.path.join(project_path, "artifacts", "test"),
            os.path.join(project_path, "artifacts"),
            os.path.join(project_path, "tests"),
        ]
        test_count = 0
        for td in test_dirs:
            test_count += count_test_functions(td)

        if source_lines == 0:
            evidence.append({
                "type": "command_output",
                "command": "heuristic coverage check",
                "stdout": "",
                "exit_code": -1,
                "detail": "No source lines found to compute coverage heuristic"
            })
        else:
            # Rough heuristic: each test covers ~5-10 lines on average
            estimated_coverage = min(100, int((test_count * 7 / source_lines) * 100))
            answer = "yes" if estimated_coverage >= 70 else "no"
            evidence.append({
                "type": "command_output",
                "command": "heuristic coverage (coverage/pytest-cov not available)",
                "stdout": (
                    f"Source lines: {source_lines}, Test functions: {test_count}, "
                    f"Estimated coverage: ~{estimated_coverage}%"
                ),
                "exit_code": 0,
                "detail": (
                    f"Heuristic estimate: {test_count} tests / {source_lines} source lines "
                    f"=> ~{estimated_coverage}% ({'>=70% -- OK' if estimated_coverage >= 70 else '<70% -- INSUFFICIENT'})"
                )
            })

    result = {
        "question": "o2.1",
        "answer": answer,
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
