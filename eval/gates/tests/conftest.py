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
