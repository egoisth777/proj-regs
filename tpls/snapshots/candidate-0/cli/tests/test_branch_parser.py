import subprocess
from unittest.mock import patch

from hooks.utils.branch_parser import parse_branch


class TestParseBranch:
    def test_worker_with_instance(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/path-validation/worker-1"):
            result = parse_branch()
        assert result == {"feature": "path-validation", "role": "worker"}

    def test_sdet_unit(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/my-feature/sdet-unit"):
            result = parse_branch()
        assert result == {"feature": "my-feature", "role": "sdet-unit"}

    def test_team_lead(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/my-feature/team-lead"):
            result = parse_branch()
        assert result == {"feature": "my-feature", "role": "team-lead"}

    def test_main_branch_fallback(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="main"):
            result = parse_branch()
        assert result == {"feature": None, "role": "orchestrator"}

    def test_develop_branch_fallback(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="develop"):
            result = parse_branch()
        assert result == {"feature": None, "role": "orchestrator"}

    def test_missing_role_segment(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/no-role"):
            result = parse_branch()
        assert result == {"feature": "no-role", "role": "orchestrator"}

    def test_extra_segments_ignored(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/my-feature/worker/extra"):
            result = parse_branch()
        assert result == {"feature": "my-feature", "role": "worker"}

    def test_special_characters_in_feature(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/fix-#123/worker-1"):
            result = parse_branch()
        assert result == {"feature": "fix-#123", "role": "worker"}

    def test_detached_head(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value=""):
            result = parse_branch()
        assert result == {"feature": None, "role": "orchestrator"}

    def test_sonders_role(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/new-arch/sonders"):
            result = parse_branch()
        assert result == {"feature": "new-arch", "role": "sonders"}

    def test_behavior_spec_writer(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/auth/behavior-spec-writer"):
            result = parse_branch()
        assert result == {"feature": "auth", "role": "behavior-spec-writer"}
