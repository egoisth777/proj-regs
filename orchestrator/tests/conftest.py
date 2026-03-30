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
