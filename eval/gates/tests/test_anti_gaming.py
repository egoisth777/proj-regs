"""Tests for anti_gaming.py --- integrity validation between phases."""

import json
import hashlib
import os
import time
import pytest
from pathlib import Path

from anti_gaming import (
    validate_eval_integrity,
    validate_temporal_order,
    validate_no_regression,
)


class TestValidateEvalIntegrity:
    def test_valid_eval_passes(self, tmp_path):
        eval_dir = tmp_path / "eval"
        eval_dir.mkdir()
        (eval_dir / "criteria").mkdir()
        (eval_dir / "criteria" / "p1.yaml").write_text("question: p1.1")

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

        # Set script mtime to 100 seconds ago
        script_time = time.time() - 100
        os.utime(script, (script_time, script_time))

        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
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

        # Set evidence mtime to 100 seconds ago
        evidence_time = time.time() - 100
        os.utime(evidence, (evidence_time, evidence_time))

        # Create script AFTER evidence (script is newer)
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
