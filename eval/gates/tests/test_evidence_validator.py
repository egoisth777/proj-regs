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
