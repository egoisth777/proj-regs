# evolution loop system — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the self-evolution loop: eval gates, orchestrator state machine, test project scaffolding, and /opsx CLI — completing the omni system's self-improvement capability.

**Architecture:** Four subsystems built in dependency order. Eval gates (stateless validators) come first since the loop depends on them. The orchestrator state machine manages the 5-phase cycle (prepare→mutate→execute→verify→decide). Test projects provide seed evaluation targets. /opsx wraps everything in a CLI. All new python files use the existing pytest + pyproject.toml setup under `tpls/snapshots/candidate-0/cli/`.

**Tech Stack:** Python 3.10+, pytest, PyYAML, existing snapshot_manager.py and frozen_lock.py

**Spec:** `docs/superpowers/specs/2026-03-30-evolution-loop-design.md`

---

## file map

### new files to create

```
eval/gates/
├── pool_isolation.py           # validates sparse-checkout matches pool permissions
├── evidence_validator.py       # parses pool-v YAML reports, rejects incomplete evidence
└── spot_check.py               # random audit sampling + independent verification

orchestrator/
├── loop.py                     # 5-phase state machine + tier progression
├── dispatch.py                 # pool worktree creation/cleanup + workspace management
└── anti_gaming.py              # integrity validation between phases

orchestrator/tests/
├── conftest.py                 # shared fixtures for orchestrator tests
├── test_loop.py
├── test_dispatch.py
└── test_anti_gaming.py

eval/gates/tests/
├── conftest.py                 # shared fixtures for gate tests
├── test_pool_isolation.py
├── test_evidence_validator.py
└── test_spot_check.py

regs/test-regs/
└── cli-todo-regs/
    └── manifest.yaml           # seed test project definition

orchestrator/opsx.py            # /opsx CLI entry point
```

### modified files

```
eval/FROZEN.lock                # regenerated after adding gate files
orchestrator/manifest.json      # schema additions (consecutive_passes field)
```

### dependency map

```
eval/gates/frozen_lock.py (existing)
    ↑
eval/gates/evidence_validator.py ← anti_gaming.py
eval/gates/spot_check.py        ← anti_gaming.py
eval/gates/pool_isolation.py    ← dispatch.py

snapshot_manager.py (existing)
    ↑
orchestrator/loop.py ← orchestrator/dispatch.py
                     ← orchestrator/anti_gaming.py
                     ← orchestrator/opsx.py
```

---

## phase 1: eval gates

### task 1: implement evidence_validator.py

**Files:**
- Create: `eval/gates/evidence_validator.py`
- Create: `eval/gates/tests/conftest.py`
- Create: `eval/gates/tests/test_evidence_validator.py`

- [ ] **Step 1: Create test conftest with shared fixtures**

Create `eval/gates/tests/__init__.py` (empty) and `eval/gates/tests/conftest.py`:

```python
"""Shared fixtures for eval gate tests."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_evidence_report(tmp_path):
    """A valid evidence report YAML string."""
    return """
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: p1.1
    answer: yes
    evidence:
      - type: file_timestamp
        path: regs/test-regs/cli-todo-regs/ssot/runtime/openspec/changes/feat-001-add-task/proposal.md
        detail: "proposal.md created before behavior_spec.md"
  - question: o1.1
    answer: yes
    evidence:
      - type: command_output
        command: "python -m py_compile todo.py"
        stdout: ""
        exit_code: 0
        detail: "compiles without errors"
"""


@pytest.fixture
def evidence_report_file(tmp_path, sample_evidence_report):
    """Write the sample report to a file and return its path."""
    report_path = tmp_path / "evidence.yaml"
    report_path.write_text(sample_evidence_report)
    return report_path
```

- [ ] **Step 2: Write failing tests for evidence_validator**

Create `eval/gates/tests/test_evidence_validator.py`:

```python
"""Tests for evidence_validator — parses and validates pool-v YAML reports."""

import pytest
from pathlib import Path

from evidence_validator import validate_evidence, parse_evidence_report


class TestParseEvidenceReport:
    def test_parses_valid_yaml(self, evidence_report_file):
        result = parse_evidence_report(evidence_report_file)
        assert result["candidate"] == "candidate-1"
        assert len(result["answers"]) == 2

    def test_rejects_invalid_yaml(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("{{invalid yaml: [")
        with pytest.raises(ValueError, match="invalid YAML"):
            parse_evidence_report(bad)

    def test_rejects_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_evidence_report(tmp_path / "nonexistent.yaml")


class TestValidateEvidence:
    def test_valid_report_passes(self, evidence_report_file):
        result = validate_evidence(evidence_report_file)
        assert result["valid"] is True
        assert result["errors"] == []
        assert len(result["parsed"]) == 2

    def test_missing_question_field(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - answer: yes
    evidence:
      - type: reasoning
        text: "some reasoning about things"
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("question" in e for e in result["errors"])

    def test_missing_answer_field(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: p1.1
    evidence:
      - type: reasoning
        text: "some reasoning about things"
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("answer" in e for e in result["errors"])

    def test_invalid_answer_value(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: p1.1
    answer: maybe
    evidence:
      - type: reasoning
        text: "some reasoning about things"
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("yes/no" in e for e in result["errors"])

    def test_empty_evidence_rejected(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: p1.1
    answer: yes
    evidence: []
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("evidence" in e for e in result["errors"])

    def test_file_timestamp_without_path_rejected(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: p1.1
    answer: yes
    evidence:
      - type: file_timestamp
        detail: "timestamp looks ok"
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("path" in e for e in result["errors"])

    def test_command_output_without_command_rejected(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: o1.1
    answer: yes
    evidence:
      - type: command_output
        stdout: "all good"
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("command" in e for e in result["errors"])

    def test_reasoning_with_short_text_rejected(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: p1.1
    answer: yes
    evidence:
      - type: reasoning
        text: "ok"
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("20 char" in e for e in result["errors"])

    def test_missing_answers_key_rejected(self, tmp_path):
        report = tmp_path / "report.yaml"
        report.write_text("""
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
""")
        result = validate_evidence(report)
        assert result["valid"] is False
        assert any("answers" in e for e in result["errors"])
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd eval/gates && python -m pytest tests/test_evidence_validator.py -v
```

Expected: `ModuleNotFoundError: No module named 'evidence_validator'`

- [ ] **Step 4: Implement evidence_validator.py**

Create `eval/gates/evidence_validator.py`:

```python
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
        if str(ans_val).lower() not in ("yes", "no"):
            errors.append(f"{qid}: answer must be yes/no, got '{ans_val}'")
            continue

        evidence = answer.get("evidence")
        if not evidence:
            errors.append(f"{qid}: missing or empty evidence list")
            continue

        for ev_item in evidence:
            errors.extend(_validate_evidence_item(ev_item, qid))

        if not errors or not any(qid in e for e in errors):
            parsed.append(answer)

    return {"valid": len(errors) == 0, "errors": errors, "parsed": parsed if not errors else [a for a in answers if a.get("question")]}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd eval/gates && python -m pytest tests/test_evidence_validator.py -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add eval/gates/evidence_validator.py eval/gates/tests/
git commit -m "feat: implement evidence_validator for pool-v report parsing"
```

---

### task 2: implement spot_check.py

**Files:**
- Create: `eval/gates/spot_check.py`
- Create: `eval/gates/tests/test_spot_check.py`

- [ ] **Step 1: Write failing tests**

Create `eval/gates/tests/test_spot_check.py`:

```python
"""Tests for spot_check — random audit sampling of evidence reports."""

import pytest
from pathlib import Path

from spot_check import select_spot_checks, verify_file_evidence


class TestSelectSpotChecks:
    def test_selects_requested_sample_size(self):
        answers = [
            {"question": "p1.1", "answer": "yes", "evidence": [{"type": "file_timestamp", "path": "a.md"}]},
            {"question": "p1.3", "answer": "yes", "evidence": [{"type": "reasoning", "text": "x" * 30}]},
            {"question": "o1.1", "answer": "no", "evidence": [{"type": "command_output", "command": "echo hi"}]},
            {"question": "o1.2", "answer": "yes", "evidence": [{"type": "file_timestamp", "path": "b.md"}]},
            {"question": "p2.1", "answer": "yes", "evidence": [{"type": "reasoning", "text": "y" * 30}]},
        ]
        result = select_spot_checks(answers, sample_size=3)
        assert len(result) == 3
        assert all("question" in r for r in result)

    def test_returns_all_if_fewer_than_sample_size(self):
        answers = [
            {"question": "p1.1", "answer": "yes", "evidence": [{"type": "reasoning", "text": "x" * 30}]},
        ]
        result = select_spot_checks(answers, sample_size=3)
        assert len(result) == 1

    def test_prefers_judgment_evidence(self):
        """Reasoning-type evidence should be sampled more often (higher gaming risk)."""
        answers = [
            {"question": "p1.1", "answer": "yes", "evidence": [{"type": "reasoning", "text": "x" * 30}]},
            {"question": "o1.1", "answer": "yes", "evidence": [{"type": "command_output", "command": "echo"}]},
            {"question": "o1.2", "answer": "yes", "evidence": [{"type": "command_output", "command": "echo"}]},
            {"question": "p1.3", "answer": "yes", "evidence": [{"type": "reasoning", "text": "y" * 30}]},
            {"question": "o1.3", "answer": "yes", "evidence": [{"type": "command_output", "command": "echo"}]},
        ]
        # run multiple times and check reasoning questions appear more often
        reasoning_count = 0
        trials = 100
        for _ in range(trials):
            selected = select_spot_checks(answers, sample_size=2)
            for s in selected:
                if any(e.get("type") == "reasoning" for e in s["evidence"]):
                    reasoning_count += 1
        # reasoning should appear in > 50% of selections (2 of 5 are reasoning)
        assert reasoning_count > trials * 0.5

    def test_empty_answers_returns_empty(self):
        result = select_spot_checks([], sample_size=3)
        assert result == []


class TestVerifyFileEvidence:
    def test_existing_file_verifies(self, tmp_path):
        (tmp_path / "proposal.md").write_text("# proposal")
        result = verify_file_evidence(
            file_path="proposal.md",
            project_path=tmp_path,
        )
        assert result["verified"] is True
        assert result["discrepancy"] is None

    def test_missing_file_fails(self, tmp_path):
        result = verify_file_evidence(
            file_path="nonexistent.md",
            project_path=tmp_path,
        )
        assert result["verified"] is False
        assert "not found" in result["discrepancy"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd eval/gates && python -m pytest tests/test_spot_check.py -v
```

Expected: `ModuleNotFoundError: No module named 'spot_check'`

- [ ] **Step 3: Implement spot_check.py**

Create `eval/gates/spot_check.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd eval/gates && python -m pytest tests/test_spot_check.py -v
```

Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add eval/gates/spot_check.py eval/gates/tests/test_spot_check.py
git commit -m "feat: implement spot_check for audit sampling"
```

---

### task 3: implement pool_isolation.py

**Files:**
- Create: `eval/gates/pool_isolation.py`
- Create: `eval/gates/tests/test_pool_isolation.py`

- [ ] **Step 1: Write failing tests**

Create `eval/gates/tests/test_pool_isolation.py`:

```python
"""Tests for pool_isolation — validates sparse-checkout matches pool permissions."""

import pytest
from pathlib import Path

from pool_isolation import (
    get_expected_paths,
    validate_pool_isolation,
    POOL_SPARSE_CONFIGS,
)


class TestGetExpectedPaths:
    def test_pool_e_mutate_paths(self):
        paths = get_expected_paths("pool-e", "mutate")
        assert "tpls/snapshots/workspace/" in paths
        assert "eval/" not in paths

    def test_pool_e_execute_paths(self):
        paths = get_expected_paths("pool-e", "execute")
        assert any("tpls/" in p for p in paths)
        assert any("regs/test-regs/" in p for p in paths)
        assert "eval/" not in paths

    def test_pool_t_paths(self):
        paths = get_expected_paths("pool-t")
        assert any("eval/criteria/" in p for p in paths)
        assert any("eval/tiers/" in p for p in paths)
        assert any("eval/scripts/" in p for p in paths)

    def test_pool_v_paths(self):
        paths = get_expected_paths("pool-v")
        assert any("eval/scripts/" in p for p in paths)
        assert any("regs/test-regs/" in p for p in paths)

    def test_pool_r_paths(self):
        paths = get_expected_paths("pool-r")
        assert any("regs/" in p for p in paths)

    def test_unknown_pool_raises(self):
        with pytest.raises(ValueError, match="unknown pool"):
            get_expected_paths("pool-x")


class TestValidatePoolIsolation:
    def test_valid_pool_e_worktree(self, tmp_path):
        """Simulate a pool-e mutate worktree with only workspace/ present."""
        # create expected structure
        (tmp_path / "tpls" / "snapshots" / "workspace").mkdir(parents=True)
        # should not have eval/
        result = validate_pool_isolation(tmp_path, "pool-e", "mutate")
        assert result["valid"] is True

    def test_pool_e_with_eval_present_fails(self, tmp_path):
        """If eval/ exists in a pool-e worktree, isolation is violated."""
        (tmp_path / "tpls" / "snapshots" / "workspace").mkdir(parents=True)
        (tmp_path / "eval" / "criteria").mkdir(parents=True)
        result = validate_pool_isolation(tmp_path, "pool-e", "mutate")
        assert result["valid"] is False
        assert any("eval" in v for v in result["violations"])

    def test_pool_t_without_tpls(self, tmp_path):
        """pool-t worktree should not contain tpls/."""
        (tmp_path / "eval" / "criteria").mkdir(parents=True)
        (tmp_path / "eval" / "tiers").mkdir(parents=True)
        (tmp_path / "eval" / "scripts").mkdir(parents=True)
        result = validate_pool_isolation(tmp_path, "pool-t")
        assert result["valid"] is True

    def test_pool_t_with_tpls_fails(self, tmp_path):
        (tmp_path / "eval" / "criteria").mkdir(parents=True)
        (tmp_path / "tpls").mkdir()
        result = validate_pool_isolation(tmp_path, "pool-t")
        assert result["valid"] is False
        assert any("tpls" in v for v in result["violations"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd eval/gates && python -m pytest tests/test_pool_isolation.py -v
```

Expected: `ModuleNotFoundError: No module named 'pool_isolation'`

- [ ] **Step 3: Implement pool_isolation.py**

Create `eval/gates/pool_isolation.py`:

```python
"""Validate that a pool worktree's sparse-checkout matches expected permissions."""

from pathlib import Path
from typing import Any, Optional

# Expected paths each pool can see, and paths that MUST be absent
POOL_SPARSE_CONFIGS = {
    "pool-e": {
        "mutate": {
            "include": ["tpls/snapshots/workspace/"],
            "exclude": ["eval/", "orchestrator/"],
        },
        "execute": {
            "include": ["tpls/", "regs/test-regs/"],
            "exclude": ["eval/", "orchestrator/"],
        },
    },
    "pool-t": {
        "default": {
            "include": ["eval/criteria/", "eval/tiers/", "eval/scripts/"],
            "exclude": ["tpls/", "regs/", "orchestrator/"],
        },
    },
    "pool-v": {
        "default": {
            "include": ["eval/scripts/", "regs/test-regs/"],
            "exclude": ["eval/criteria/", "tpls/", "orchestrator/"],
        },
    },
    "pool-r": {
        "default": {
            "include": ["regs/"],
            "exclude": ["eval/", "tpls/", "orchestrator/"],
        },
    },
}


def get_expected_paths(pool: str, phase: Optional[str] = None) -> list[str]:
    """Return the list of included paths for a pool/phase combination."""
    if pool not in POOL_SPARSE_CONFIGS:
        raise ValueError(f"unknown pool: {pool}")
    configs = POOL_SPARSE_CONFIGS[pool]
    key = phase if phase and phase in configs else "default"
    if key not in configs:
        # pool-e requires a phase
        raise ValueError(f"pool '{pool}' requires a phase, got '{phase}'")
    return configs[key]["include"]


def validate_pool_isolation(
    worktree_path: Path,
    pool: str,
    phase: Optional[str] = None,
) -> dict[str, Any]:
    """Check that a worktree contains only what the pool should see.

    Verifies that excluded directories are NOT present in the worktree.
    Returns {"valid": bool, "violations": list[str]}.
    """
    wt = Path(worktree_path)
    if pool not in POOL_SPARSE_CONFIGS:
        raise ValueError(f"unknown pool: {pool}")

    configs = POOL_SPARSE_CONFIGS[pool]
    key = phase if phase and phase in configs else "default"
    if key not in configs:
        raise ValueError(f"pool '{pool}' requires a phase, got '{phase}'")

    config = configs[key]
    violations: list[str] = []

    # Check excluded paths are absent
    for excluded in config["exclude"]:
        excluded_path = wt / excluded.rstrip("/")
        if excluded_path.exists():
            violations.append(f"excluded path present: {excluded}")

    return {"valid": len(violations) == 0, "violations": violations}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd eval/gates && python -m pytest tests/test_pool_isolation.py -v
```

Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add eval/gates/pool_isolation.py eval/gates/tests/test_pool_isolation.py
git commit -m "feat: implement pool_isolation for worktree validation"
```

---

### task 4: add pyproject.toml for eval gates and regenerate FROZEN.lock

**Files:**
- Create: `eval/gates/pyproject.toml`
- Modify: `eval/FROZEN.lock`

- [ ] **Step 1: Create pyproject.toml for eval/gates tests**

Create `eval/gates/pyproject.toml`:

```toml
[project]
name = "eval-gates"
version = "1.0.0"
description = "Anti-gaming enforcement gates for the eval layer"
requires-python = ">=3.10"
dependencies = ["pyyaml>=6.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Install pyyaml dependency**

```bash
pip install pyyaml
```

- [ ] **Step 3: Run all gate tests**

```bash
cd eval/gates && python -m pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 4: Regenerate FROZEN.lock**

```bash
cd /home/aeonli/repos/omni && python eval/gates/frozen_lock.py
```

Expected: `Generated FROZEN.lock with N entries` (more than previous 24)

- [ ] **Step 5: Verify FROZEN.lock**

```bash
python eval/gates/frozen_lock.py verify
```

Expected: `FROZEN.lock: OK`

- [ ] **Step 6: Commit**

```bash
git add eval/gates/pyproject.toml eval/gates/tests/__init__.py eval/FROZEN.lock
git commit -m "chore: add eval gates pyproject.toml and regenerate FROZEN.lock"
```

---

## phase 2: orchestrator state machine

### task 5: implement loop.py — phase state machine

**Files:**
- Create: `orchestrator/loop.py`
- Create: `orchestrator/tests/conftest.py`
- Create: `orchestrator/tests/test_loop.py`
- Create: `orchestrator/pyproject.toml`

- [ ] **Step 1: Create orchestrator pyproject.toml and test scaffolding**

Create `orchestrator/pyproject.toml`:

```toml
[project]
name = "orchestrator"
version = "1.0.0"
description = "Evolution loop orchestrator state machine"
requires-python = ">=3.10"
dependencies = ["pyyaml>=6.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

Create `orchestrator/tests/__init__.py` (empty) and `orchestrator/tests/conftest.py`:

```python
"""Shared fixtures for orchestrator tests."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def manifest_dir(tmp_path):
    """Create a minimal manifest structure for testing."""
    manifest = {
        "active": "candidate-0",
        "phase": "prepare",
        "tier": "seed",
        "test_domain": None,
        "consecutive_passes": 0,
        "candidates": [
            {
                "id": "candidate-0",
                "parent": None,
                "status": "active",
                "mutation": None,
                "sha256": None,
                "pass_rate": {},
                "created": "2026-03-29T00:00:00Z",
            }
        ],
        "promoted": ["candidate-0"],
        "next_action": "begin evolution",
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return tmp_path


@pytest.fixture
def manifest_path(manifest_dir):
    return manifest_dir / "manifest.json"


@pytest.fixture
def seed_tier_path(tmp_path):
    """Create a minimal seed.yaml tier file."""
    tier_dir = tmp_path / "eval" / "tiers"
    tier_dir.mkdir(parents=True)
    seed = tier_dir / "seed.yaml"
    seed.write_text("""tier: seed
description: "foundational questions"
questions:
  - p1.1
  - p1.3
  - p1.6
  - p2.1
  - p2.3
  - o1.1
  - o1.2
  - o4.1
  - p4.1
unlock_condition: "always active"
""")
    tier2 = tier_dir / "tier-2.yaml"
    tier2.write_text("""tier: tier-2
description: "expanded questions"
questions:
  - p1.2
  - p1.4
  - p2.2
unlock_condition: "seed at 100% for 3 consecutive runs"
""")
    return tmp_path / "eval" / "tiers"
```

- [ ] **Step 2: Write failing tests for loop.py**

Create `orchestrator/tests/test_loop.py`:

```python
"""Tests for loop.py — phase state machine + tier progression."""

import json
import pytest
from pathlib import Path

from loop import (
    get_current_phase,
    advance_phase,
    prepare_mutation,
    decide_outcome,
    check_tier_progression,
    VALID_TRANSITIONS,
)


class TestGetCurrentPhase:
    def test_returns_current_phase(self, manifest_path):
        assert get_current_phase(manifest_path) == "prepare"

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            get_current_phase(tmp_path / "nonexistent.json")


class TestAdvancePhase:
    def test_prepare_to_mutate(self, manifest_path):
        new_phase = advance_phase(manifest_path, {"directive": "improve p1"})
        assert new_phase == "mutate"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["phase"] == "mutate"

    def test_mutate_to_execute(self, manifest_path):
        # first move to mutate
        advance_phase(manifest_path, {"directive": "test"})
        new_phase = advance_phase(manifest_path, {"candidate_id": "candidate-1"})
        assert new_phase == "execute"

    def test_invalid_transition_raises(self, manifest_path):
        """Cannot go from prepare directly to verify."""
        with pytest.raises(ValueError, match="invalid transition"):
            # hack phase to verify
            m = json.loads(manifest_path.read_text())
            m["phase"] = "verify"
            manifest_path.write_text(json.dumps(m))
            advance_phase(manifest_path, {})
            # now try to go to mutate (verify -> mutate is invalid)
            m = json.loads(manifest_path.read_text())
            m["phase"] = "prepare"
            manifest_path.write_text(json.dumps(m))
            # prepare -> decide is invalid
            m = json.loads(manifest_path.read_text())
            m["phase"] = "execute"
            manifest_path.write_text(json.dumps(m))
            # try execute -> prepare (invalid, should go to verify)
            advance_phase(manifest_path, {})  # execute -> verify (valid)
            advance_phase(manifest_path, {})  # verify -> decide (valid)
            # now at decide, try to go to mutate (invalid)

    def test_full_cycle(self, manifest_path):
        """Walk through all 5 phases."""
        assert get_current_phase(manifest_path) == "prepare"
        advance_phase(manifest_path, {"directive": "improve p1"})
        assert get_current_phase(manifest_path) == "mutate"
        advance_phase(manifest_path, {"candidate_id": "candidate-1"})
        assert get_current_phase(manifest_path) == "execute"
        advance_phase(manifest_path, {"test_domain": "cli-todo"})
        assert get_current_phase(manifest_path) == "verify"
        advance_phase(manifest_path, {"evidence_path": "/tmp/evidence.yaml"})
        assert get_current_phase(manifest_path) == "decide"
        advance_phase(manifest_path, {"outcome": "promote"})
        assert get_current_phase(manifest_path) == "prepare"


class TestPrepareMutation:
    def test_identifies_weakest_category(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {
            "p1": "2/3", "p2": "3/3", "o1": "1/3", "o4": "3/3", "p4": "3/3",
        }
        manifest_path.write_text(json.dumps(m))

        result = prepare_mutation(manifest_path)
        assert result["target_category"] == "o1"
        assert "o1" in result["directive"].lower() or "correctness" in result["directive"].lower()

    def test_no_pass_rate_returns_general_directive(self, manifest_path):
        result = prepare_mutation(manifest_path)
        assert "directive" in result
        assert result["target_category"] is None

    def test_perfect_scores_returns_general(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"p1": "3/3", "o1": "3/3"}
        manifest_path.write_text(json.dumps(m))
        result = prepare_mutation(manifest_path)
        assert "directive" in result


class TestDecideOutcome:
    def test_promote_when_improved(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"overall": "4/9"}
        m["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "test",
            "sha256": "abc", "pass_rate": {"overall": "6/9"},
            "created": "2026-03-30T00:00:00Z",
        })
        manifest_path.write_text(json.dumps(m))

        result = decide_outcome(manifest_path, "candidate-1")
        assert result == "promote"

    def test_reject_when_regressed(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"overall": "6/9"}
        m["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "test",
            "sha256": "abc", "pass_rate": {"overall": "4/9"},
            "created": "2026-03-30T00:00:00Z",
        })
        manifest_path.write_text(json.dumps(m))

        result = decide_outcome(manifest_path, "candidate-1")
        assert result == "reject"

    def test_tie_when_equal(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"overall": "5/9"}
        m["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "test",
            "sha256": "abc", "pass_rate": {"overall": "5/9"},
            "created": "2026-03-30T00:00:00Z",
        })
        manifest_path.write_text(json.dumps(m))

        result = decide_outcome(manifest_path, "candidate-1")
        assert result == "tie"


class TestCheckTierProgression:
    def test_no_progression_at_zero_passes(self, manifest_path, seed_tier_path):
        result = check_tier_progression(manifest_path, seed_tier_path)
        assert result["should_advance"] is False
        assert result["current_tier"] == "seed"

    def test_advances_after_three_consecutive(self, manifest_path, seed_tier_path):
        m = json.loads(manifest_path.read_text())
        m["consecutive_passes"] = 3
        m["candidates"][0]["pass_rate"] = {"overall": "9/9"}
        manifest_path.write_text(json.dumps(m))

        result = check_tier_progression(manifest_path, seed_tier_path)
        assert result["should_advance"] is True
        assert result["next_tier"] == "tier-2"

    def test_no_advance_if_not_perfect(self, manifest_path, seed_tier_path):
        m = json.loads(manifest_path.read_text())
        m["consecutive_passes"] = 3
        m["candidates"][0]["pass_rate"] = {"overall": "8/9"}
        manifest_path.write_text(json.dumps(m))

        result = check_tier_progression(manifest_path, seed_tier_path)
        assert result["should_advance"] is False
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd orchestrator && python -m pytest tests/test_loop.py -v
```

Expected: `ModuleNotFoundError: No module named 'loop'`

- [ ] **Step 4: Implement loop.py**

Create `orchestrator/loop.py`:

```python
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
    # Remove 'overall' key for category analysis
    categories = {k: v for k, v in pass_rate.items() if k != "overall"}

    if not categories:
        return {
            "directive": "general improvement — no category breakdown available",
            "target_category": None,
        }

    # Find lowest-scoring category
    worst_cat = None
    worst_ratio = 1.1  # higher than any possible ratio
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

    # Compare overall scores
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

    # Check if active candidate has perfect score
    active_id = manifest.get("active")
    active_rate = {}
    for c in manifest.get("candidates", []):
        if c["id"] == active_id:
            active_rate = c.get("pass_rate", {})
            break

    overall = active_rate.get("overall", "0/0")
    passed, total = _parse_pass_rate(overall)
    is_perfect = total > 0 and passed == total

    # Determine next tier
    current_idx = TIER_ORDER.index(current_tier) if current_tier in TIER_ORDER else 0
    next_tier = TIER_ORDER[current_idx + 1] if current_idx + 1 < len(TIER_ORDER) else None

    should_advance = is_perfect and consecutive >= 3 and next_tier is not None

    return {
        "should_advance": should_advance,
        "current_tier": current_tier,
        "next_tier": next_tier,
    }
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd orchestrator && python -m pytest tests/test_loop.py -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add orchestrator/loop.py orchestrator/pyproject.toml orchestrator/tests/
git commit -m "feat: implement evolution loop phase state machine"
```

---

### task 6: implement dispatch.py — pool worktree management

**Files:**
- Create: `orchestrator/dispatch.py`
- Create: `orchestrator/tests/test_dispatch.py`

- [ ] **Step 1: Write failing tests**

Create `orchestrator/tests/test_dispatch.py`:

```python
"""Tests for dispatch.py — pool worktree management."""

import json
import os
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from dispatch import (
    get_sparse_checkout_config,
    prepare_workspace,
    cleanup_workspace,
)


class TestGetSparseCheckoutConfig:
    def test_pool_e_mutate_includes_workspace(self):
        config = get_sparse_checkout_config("pool-e", "mutate")
        assert any("workspace" in p for p in config["include"])
        assert any("eval" in p for p in config["exclude"])

    def test_pool_e_execute_includes_tpls_and_regs(self):
        config = get_sparse_checkout_config("pool-e", "execute")
        assert any("tpls" in p for p in config["include"])
        assert any("regs" in p for p in config["include"])

    def test_pool_t_config(self):
        config = get_sparse_checkout_config("pool-t")
        assert any("criteria" in p for p in config["include"])
        assert any("tpls" in p for p in config["exclude"])

    def test_pool_v_config(self):
        config = get_sparse_checkout_config("pool-v")
        assert any("scripts" in p for p in config["include"])
        assert any("criteria" in p for p in config["exclude"])

    def test_pool_r_config(self):
        config = get_sparse_checkout_config("pool-r")
        assert any("regs" in p for p in config["include"])

    def test_unknown_pool_raises(self):
        with pytest.raises(ValueError, match="unknown pool"):
            get_sparse_checkout_config("pool-x")


class TestPrepareWorkspace:
    def test_copies_active_snapshot_to_workspace(self, tmp_path):
        # create fake snapshot structure
        snapshots = tmp_path / "tpls" / "snapshots"
        c0 = snapshots / "candidate-0"
        (c0 / "sys").mkdir(parents=True)
        (c0 / "sys" / "role.md").write_text("# role")
        (c0 / "cli").mkdir(parents=True)
        (c0 / "cli" / "hook.py").write_text("print('hook')")

        # create active symlink
        (snapshots / "active").symlink_to("candidate-0")

        workspace = prepare_workspace(snapshots)
        assert (workspace / "sys" / "role.md").read_text() == "# role"
        assert (workspace / "cli" / "hook.py").read_text() == "print('hook')"
        assert workspace.name == "workspace"

    def test_raises_if_workspace_already_exists(self, tmp_path):
        snapshots = tmp_path / "tpls" / "snapshots"
        c0 = snapshots / "candidate-0"
        (c0 / "sys").mkdir(parents=True)
        (snapshots / "active").symlink_to("candidate-0")
        (snapshots / "workspace").mkdir()

        with pytest.raises(FileExistsError, match="workspace already exists"):
            prepare_workspace(snapshots)


class TestCleanupWorkspace:
    def test_removes_workspace(self, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "file.txt").write_text("data")
        cleanup_workspace(workspace)
        assert not workspace.exists()

    def test_no_error_if_missing(self, tmp_path):
        workspace = tmp_path / "nonexistent"
        cleanup_workspace(workspace)  # should not raise
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd orchestrator && python -m pytest tests/test_dispatch.py -v
```

Expected: `ModuleNotFoundError: No module named 'dispatch'`

- [ ] **Step 3: Implement dispatch.py**

Create `orchestrator/dispatch.py`:

```python
"""Pool worktree management — creates isolated workspaces for pool agents.

The orchestrator agent uses this module to:
1. Prepare a mutable workspace from the active snapshot (for pool-e mutation)
2. Get sparse-checkout configs for each pool (for agent dispatch)
3. Clean up workspaces after use
"""

import shutil
from pathlib import Path
from typing import Any, Optional


# Sparse-checkout configs per pool/phase
_CONFIGS = {
    "pool-e": {
        "mutate": {
            "include": ["tpls/snapshots/workspace/"],
            "exclude": ["eval/", "orchestrator/", "regs/"],
        },
        "execute": {
            "include": ["tpls/sys/", "tpls/cli/", "regs/test-regs/"],
            "exclude": ["eval/", "orchestrator/"],
        },
    },
    "pool-t": {
        "default": {
            "include": ["eval/criteria/", "eval/tiers/", "eval/scripts/"],
            "exclude": ["tpls/", "regs/", "orchestrator/"],
        },
    },
    "pool-v": {
        "default": {
            "include": ["eval/scripts/", "regs/test-regs/"],
            "exclude": ["eval/criteria/", "eval/tiers/", "tpls/", "orchestrator/"],
        },
    },
    "pool-r": {
        "default": {
            "include": ["regs/"],
            "exclude": ["eval/", "tpls/", "orchestrator/"],
        },
    },
}


def get_sparse_checkout_config(
    pool: str,
    phase: Optional[str] = None,
) -> dict[str, list[str]]:
    """Return the sparse-checkout include/exclude lists for a pool.

    Args:
        pool: Pool name (pool-e, pool-t, pool-v, pool-r).
        phase: Required for pool-e (mutate or execute). Ignored for others.

    Returns {"include": [...], "exclude": [...]}.
    """
    if pool not in _CONFIGS:
        raise ValueError(f"unknown pool: {pool}")
    configs = _CONFIGS[pool]
    key = phase if phase and phase in configs else "default"
    if key not in configs:
        raise ValueError(f"pool '{pool}' requires a phase, got '{phase}'")
    return configs[key]


def prepare_workspace(snapshots_dir: Path) -> Path:
    """Copy the active snapshot's sys/ and cli/ into workspace/.

    The workspace is a mutable copy that pool-e modifies during mutation.
    After mutation, snapshot_manager.create_candidate() captures and destroys it.

    Returns the workspace path.
    Raises FileExistsError if workspace/ already exists (stale from a crash).
    """
    sd = Path(snapshots_dir)
    workspace = sd / "workspace"
    if workspace.exists():
        raise FileExistsError(
            f"workspace already exists at {workspace} — "
            "clean up stale workspace before starting a new mutation"
        )

    active = sd / "active"
    if not active.exists():
        raise FileNotFoundError(f"no active symlink at {active}")

    # Resolve the symlink to get the actual candidate dir
    active_resolved = active.resolve()

    workspace.mkdir()
    for subdir in ("sys", "cli"):
        src = active_resolved / subdir
        if src.is_dir():
            shutil.copytree(str(src), str(workspace / subdir))

    return workspace


def cleanup_workspace(workspace: Path) -> None:
    """Remove a workspace directory. No-op if it doesn't exist."""
    ws = Path(workspace)
    if ws.exists():
        shutil.rmtree(str(ws))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd orchestrator && python -m pytest tests/test_dispatch.py -v
```

Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add orchestrator/dispatch.py orchestrator/tests/test_dispatch.py
git commit -m "feat: implement pool worktree dispatch management"
```

---

### task 7: implement anti_gaming.py — integrity validation

**Files:**
- Create: `orchestrator/anti_gaming.py`
- Create: `orchestrator/tests/test_anti_gaming.py`

- [ ] **Step 1: Write failing tests**

Create `orchestrator/tests/test_anti_gaming.py`:

```python
"""Tests for anti_gaming.py — integrity validation between phases."""

import json
import pytest
from pathlib import Path

from anti_gaming import (
    validate_eval_integrity,
    validate_temporal_order,
    validate_no_regression,
)


class TestValidateEvalIntegrity:
    def test_valid_eval_passes(self, tmp_path):
        """Create eval dir with FROZEN.lock that matches."""
        eval_dir = tmp_path / "eval"
        eval_dir.mkdir()
        (eval_dir / "criteria").mkdir()
        (eval_dir / "criteria" / "p1.yaml").write_text("question: p1.1")

        # Generate lock
        import hashlib
        content = (eval_dir / "criteria" / "p1.yaml").read_bytes()
        h = hashlib.sha256(content).hexdigest()
        lock = {"version": "1.0", "hashes": {"criteria/p1.yaml": h}}
        (eval_dir / "FROZEN.lock").write_text(json.dumps(lock))

        result = validate_eval_integrity(eval_dir)
        assert result["valid"] is True

    def test_modified_file_fails(self, tmp_path):
        eval_dir = tmp_path / "eval"
        eval_dir.mkdir()
        (eval_dir / "criteria").mkdir()
        (eval_dir / "criteria" / "p1.yaml").write_text("question: p1.1")

        import hashlib
        lock = {"version": "1.0", "hashes": {"criteria/p1.yaml": "wrong_hash"}}
        (eval_dir / "FROZEN.lock").write_text(json.dumps(lock))

        result = validate_eval_integrity(eval_dir)
        assert result["valid"] is False
        assert any("CHANGED" in v for v in result["violations"])

    def test_missing_frozen_lock_fails(self, tmp_path):
        eval_dir = tmp_path / "eval"
        eval_dir.mkdir()
        result = validate_eval_integrity(eval_dir)
        assert result["valid"] is False


class TestValidateTemporalOrder:
    def test_scripts_before_evidence_passes(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script = scripts_dir / "check_p1.py"
        script.write_text("# check script")

        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        # Set script mtime to before evidence
        import os, time
        script_time = time.time() - 100
        os.utime(script, (script_time, script_time))

        evidence = evidence_dir / "report.yaml"
        evidence.write_text("answers: []")

        result = validate_temporal_order(scripts_dir, evidence_dir)
        assert result["valid"] is True

    def test_evidence_before_scripts_fails(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        evidence = evidence_dir / "report.yaml"
        evidence.write_text("answers: []")

        # Set evidence mtime to before script
        import os, time
        evidence_time = time.time() - 100
        os.utime(evidence, (evidence_time, evidence_time))

        script = scripts_dir / "check_p1.py"
        script.write_text("# check script")

        result = validate_temporal_order(scripts_dir, evidence_dir)
        assert result["valid"] is False


class TestValidateNoRegression:
    def test_no_flips_passes(self, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        manifest = {
            "active": "candidate-0",
            "phase": "decide",
            "tier": "seed",
            "candidates": [
                {"id": "candidate-0", "pass_rate": {"p1": "2/3", "overall": "2/3"}, "status": "active", "parent": None, "mutation": None, "sha256": "a", "created": "2026-01-01"},
                {"id": "candidate-1", "pass_rate": {"p1": "3/3", "overall": "3/3"}, "status": "pending", "parent": "candidate-0", "mutation": "improved p1", "sha256": "b", "created": "2026-01-02"},
            ],
            "promoted": ["candidate-0"],
        }
        manifest_path.write_text(json.dumps(manifest))

        result = validate_no_regression(manifest_path, "candidate-1")
        assert result["valid"] is True

    def test_regression_without_mutation_flagged(self, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        manifest = {
            "active": "candidate-0",
            "phase": "decide",
            "tier": "seed",
            "candidates": [
                {"id": "candidate-0", "pass_rate": {"p1": "3/3", "overall": "3/3"}, "status": "active", "parent": None, "mutation": None, "sha256": "a", "created": "2026-01-01"},
                {"id": "candidate-1", "pass_rate": {"p1": "1/3", "overall": "1/3"}, "status": "pending", "parent": "candidate-0", "mutation": "no-op", "sha256": "a", "created": "2026-01-02"},
            ],
            "promoted": ["candidate-0"],
        }
        manifest_path.write_text(json.dumps(manifest))

        result = validate_no_regression(manifest_path, "candidate-1")
        assert result["valid"] is False
        assert len(result["suspicious_flips"]) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd orchestrator && python -m pytest tests/test_anti_gaming.py -v
```

Expected: `ModuleNotFoundError: No module named 'anti_gaming'`

- [ ] **Step 3: Implement anti_gaming.py**

Create `orchestrator/anti_gaming.py`:

```python
"""Integrity validation between evolution loop phases.

Stateless checks the orchestrator calls to detect gaming, corruption,
or temporal violations.
"""

import json
import os
from pathlib import Path
from typing import Any

# Import frozen_lock for eval integrity checking
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "eval" / "gates"))
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

    # Find latest script mtime
    script_files = list(sd.rglob("*"))
    script_files = [f for f in script_files if f.is_file()]
    if not script_files:
        # No scripts means nothing to validate
        return {"valid": True, "violations": []}

    latest_script = max(f.stat().st_mtime for f in script_files)

    # Find earliest evidence mtime
    evidence_files = list(ed.rglob("*"))
    evidence_files = [f for f in evidence_files if f.is_file()]
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
        if candidate and c["id"] == candidate.get("parent"):
            parent = c

    if not candidate or not parent:
        return {"valid": True, "suspicious_flips": []}

    # Check for regressions
    candidate_rates = candidate.get("pass_rate", {})
    parent_rates = parent.get("pass_rate", {})

    for cat in parent_rates:
        if cat == "overall":
            continue
        p_passed, p_total = _parse_rate(parent_rates.get(cat, "0/0"))
        c_passed, c_total = _parse_rate(candidate_rates.get(cat, "0/0"))

        if c_total > 0 and p_total > 0 and c_passed < p_passed:
            # Regression detected — is the mutation meaningful?
            if candidate.get("sha256") == parent.get("sha256"):
                suspicious.append(
                    f"{cat}: regressed from {p_passed}/{p_total} to {c_passed}/{c_total} "
                    f"with identical content hash"
                )

    return {"valid": len(suspicious) == 0, "suspicious_flips": suspicious}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd orchestrator && python -m pytest tests/test_anti_gaming.py -v
```

Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add orchestrator/anti_gaming.py orchestrator/tests/test_anti_gaming.py
git commit -m "feat: implement anti_gaming integrity validation"
```

---

## phase 3: test project scaffolding

### task 8: create cli-todo test project manifest

**Files:**
- Create: `regs/test-regs/cli-todo-regs/manifest.yaml`

- [ ] **Step 1: Create the manifest**

Create `regs/test-regs/cli-todo-regs/manifest.yaml`:

```yaml
name: cli-todo
domain: cli-tools
complexity: minimal
tier: seed
description: >
  a command-line todo list application. supports add, list, complete,
  and delete operations. stores tasks in a local json file.
features:
  - name: add-task
    description: add a new task with a title and optional priority
    spec_cascade: full
  - name: list-tasks
    description: list all tasks, optionally filtered by status
    spec_cascade: full
  - name: complete-task
    description: mark a task as completed by id
    spec_cascade: full
expected_roles:
  - behavior-spec-writer
  - test-spec-writer
  - team-lead
  - worker
  - sdet-unit
tech_stack:
  language: python
  test_framework: pytest
  min_python: "3.10"
```

- [ ] **Step 2: Commit**

```bash
git add regs/test-regs/cli-todo-regs/manifest.yaml
git commit -m "feat: add cli-todo seed test project manifest"
```

---

## phase 4: /opsx CLI

### task 9: implement opsx.py CLI entry point

**Files:**
- Create: `orchestrator/opsx.py`
- Create: `orchestrator/tests/test_opsx.py`

- [ ] **Step 1: Write failing tests**

Create `orchestrator/tests/test_opsx.py`:

```python
"""Tests for opsx.py — CLI entry point for evolution loop operations."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from opsx import (
    cmd_status,
    cmd_tier,
    cmd_new_feature,
    _next_feature_number,
)


@pytest.fixture
def omni_root(tmp_path, manifest_path):
    """Create a minimal omni directory for opsx commands."""
    # manifest already created by conftest
    # create openspec template
    tpl = tmp_path / "tpls" / "sys" / "tpl-proj" / "runtime" / "openspec" / "template"
    tpl.mkdir(parents=True)
    (tpl / "proposal.md").write_text("# Proposal\n")
    (tpl / "behavior_spec.md").write_text("# Behavior Spec\n")
    (tpl / "test_spec.md").write_text("# Test Spec\n")
    (tpl / "tasks.md").write_text("# Tasks\n")
    (tpl / "status.md").write_text("# Status\n")
    return tmp_path


class TestCmdStatus:
    def test_returns_manifest_summary(self, manifest_path):
        result = cmd_status(manifest_path)
        assert "candidate-0" in result
        assert "prepare" in result
        assert "seed" in result


class TestCmdTier:
    def test_returns_tier_info(self, manifest_path):
        result = cmd_tier(manifest_path)
        assert "seed" in result
        assert "consecutive" in result.lower()


class TestNextFeatureNumber:
    def test_empty_changes_returns_001(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        assert _next_feature_number(changes) == 1

    def test_increments_from_existing(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        (changes / "feat-001-add-task").mkdir()
        (changes / "feat-002-list-tasks").mkdir()
        assert _next_feature_number(changes) == 3

    def test_handles_gaps(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        (changes / "feat-001-add-task").mkdir()
        (changes / "feat-005-delete").mkdir()
        assert _next_feature_number(changes) == 6


class TestCmdNewFeature:
    def test_creates_feature_folder(self, omni_root):
        changes_dir = omni_root / "regs" / "test-regs" / "cli-todo-regs" / "ssot" / "runtime" / "openspec" / "changes"
        changes_dir.mkdir(parents=True)
        template_dir = omni_root / "tpls" / "sys" / "tpl-proj" / "runtime" / "openspec" / "template"

        result = cmd_new_feature(
            "add-task",
            changes_dir=changes_dir,
            template_dir=template_dir,
        )

        feat_dir = changes_dir / "feat-001-add-task"
        assert feat_dir.exists()
        assert (feat_dir / "proposal.md").exists()
        assert (feat_dir / "behavior_spec.md").exists()
        assert (feat_dir / "test_spec.md").exists()
        assert (feat_dir / "tasks.md").exists()
        assert (feat_dir / "status.md").exists()
        assert "feat-001-add-task" in result

    def test_auto_increments(self, omni_root):
        changes_dir = omni_root / "regs" / "test-regs" / "cli-todo-regs" / "ssot" / "runtime" / "openspec" / "changes"
        changes_dir.mkdir(parents=True)
        (changes_dir / "feat-001-add-task").mkdir()
        template_dir = omni_root / "tpls" / "sys" / "tpl-proj" / "runtime" / "openspec" / "template"

        result = cmd_new_feature(
            "list-tasks",
            changes_dir=changes_dir,
            template_dir=template_dir,
        )
        assert "feat-002-list-tasks" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd orchestrator && python -m pytest tests/test_opsx.py -v
```

Expected: `ModuleNotFoundError: No module named 'opsx'`

- [ ] **Step 3: Implement opsx.py**

Create `orchestrator/opsx.py`:

```python
"""CLI entry point for evolution loop operations (/opsx command).

Usage:
    python opsx.py status [--manifest PATH]
    python opsx.py tier [--manifest PATH]
    python opsx.py new-feature NAME --changes-dir PATH --template-dir PATH
    python opsx.py evolve [--manifest PATH]
    python opsx.py rollback CANDIDATE_ID [--manifest PATH]
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Optional


def cmd_status(manifest_path: Path) -> str:
    """Show current evolution loop state."""
    data = json.loads(Path(manifest_path).read_text())
    active = data.get("active", "unknown")
    phase = data.get("phase", "unknown")
    tier = data.get("tier", "unknown")
    next_action = data.get("next_action", "none")

    # Find active candidate's pass rate
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

    # Copy template files
    tpl = Path(template_dir)
    for f in tpl.iterdir():
        if f.is_file():
            shutil.copy2(str(f), str(feat_dir / f.name))

    return f"Created {folder_name}"


def main():
    parser = argparse.ArgumentParser(description="omni evolution loop operations")
    sub = parser.add_subparsers(dest="command")

    # status
    p_status = sub.add_parser("status", help="show current loop state")
    p_status.add_argument("--manifest", default="orchestrator/manifest.json")

    # tier
    p_tier = sub.add_parser("tier", help="show tier progression")
    p_tier.add_argument("--manifest", default="orchestrator/manifest.json")

    # new-feature
    p_feat = sub.add_parser("new-feature", help="create feature folder")
    p_feat.add_argument("name", help="feature name (e.g. add-task)")
    p_feat.add_argument("--changes-dir", required=True, help="path to openspec/changes/")
    p_feat.add_argument("--template-dir", required=True, help="path to openspec/template/")

    # rollback
    p_rb = sub.add_parser("rollback", help="rollback to a candidate")
    p_rb.add_argument("candidate_id", help="candidate id (e.g. candidate-0)")
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
        sys.path.insert(0, str(Path(__file__).parent.parent / "tpls" / "snapshots" / "candidate-0" / "cli"))
        from hooks.utils.snapshot_manager import rollback_to
        rollback_to(args.candidate_id, args.snapshots_dir, args.manifest)
        print(f"Rolled back to {args.candidate_id}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd orchestrator && python -m pytest tests/test_opsx.py -v
```

Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add orchestrator/opsx.py orchestrator/tests/test_opsx.py
git commit -m "feat: implement /opsx CLI entry point"
```

---

## phase 5: update manifest schema and final verification

### task 10: update manifest.json with consecutive_passes field

**Files:**
- Modify: `orchestrator/manifest.json`

- [ ] **Step 1: Add consecutive_passes field**

Update `orchestrator/manifest.json` to include the new field needed by tier progression:

```json
{
  "active": "candidate-0",
  "phase": "prepare",
  "tier": "seed",
  "test_domain": null,
  "consecutive_passes": 0,
  "candidates": [
    {
      "id": "candidate-0",
      "parent": null,
      "status": "active",
      "mutation": null,
      "sha256": null,
      "pass_rate": {},
      "created": "2026-03-29T00:00:00Z"
    }
  ],
  "promoted": ["candidate-0"],
  "next_action": "begin self-evolution loop - run first test project against seed tier"
}
```

- [ ] **Step 2: Commit**

```bash
git add orchestrator/manifest.json
git commit -m "chore: add consecutive_passes field to manifest schema"
```

---

### task 11: run full test suite

**Files:** all test files

- [ ] **Step 1: Run eval gate tests**

```bash
cd eval/gates && python -m pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 2: Run orchestrator tests**

```bash
cd orchestrator && python -m pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 3: Run existing cli hook tests**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/ -v
```

Expected: all existing tests still pass

- [ ] **Step 4: Verify FROZEN.lock**

```bash
cd /home/aeonli/repos/omni && python eval/gates/frozen_lock.py verify
```

Expected: `FROZEN.lock: OK`

- [ ] **Step 5: Final commit if any fixes needed**

```bash
git add -A && git commit -m "chore: verify full test suite passes"
```

---

## summary

| phase | tasks | what it produces |
|-------|-------|------------------|
| 1: eval gates | 1-4 | evidence_validator, spot_check, pool_isolation + FROZEN.lock |
| 2: orchestrator | 5-7 | loop.py state machine, dispatch.py, anti_gaming.py |
| 3: test projects | 8 | cli-todo manifest.yaml |
| 4: /opsx CLI | 9 | opsx.py with status, tier, new-feature, rollback |
| 5: finalize | 10-11 | manifest schema update, full test verification |
