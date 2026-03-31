"""Tests for layer_fence hook: enforces one-way layer dependencies for pool agents."""

import json
from unittest.mock import patch

from hooks.layer_fence import get_layer, validate_layer_access


class TestGetLayer:
    def test_eval_top_level(self):
        assert get_layer("eval/criteria/rubric.md") == "eval"

    def test_eval_nested(self):
        assert get_layer("eval/scripts/check_format.py") == "eval"

    def test_eval_tiers(self):
        assert get_layer("eval/tiers/tier1.yaml") == "eval"

    def test_eval_gates(self):
        assert get_layer("eval/gates/gate1.yaml") == "eval"

    def test_eval_pools(self):
        assert get_layer("eval/pools/pool-e.yaml") == "eval"

    def test_eval_frozen_lock(self):
        assert get_layer("eval/FROZEN.lock") == "eval"

    def test_tpls_top_level(self):
        assert get_layer("tpls/template.py") == "tpls"

    def test_tpls_nested(self):
        assert get_layer("tpls/snapshots/candidate-0/cli/hooks/foo.py") == "tpls"

    def test_regs_top_level(self):
        assert get_layer("regs/config.yaml") == "regs"

    def test_regs_nested(self):
        assert get_layer("regs/omni-regs/ssot/status.md") == "regs"

    def test_orchestrator_top_level(self):
        assert get_layer("eval-loop/plan.md") == "eval-loop"

    def test_orchestrator_nested(self):
        assert get_layer("eval-loop/dispatch/task1.md") == "eval-loop"

    def test_unknown_layer_src(self):
        assert get_layer("src/main.py") is None

    def test_unknown_layer_root_file(self):
        assert get_layer("README.md") is None

    def test_unknown_layer_tests(self):
        assert get_layer("tests/test_foo.py") is None

    def test_empty_string(self):
        assert get_layer("") is None


# ─── pool-e (execute): read+write tpls/ only ───────────────────────

class TestPoolE:
    def test_write_tpls_allowed(self):
        result = validate_layer_access("pool-e", "tpls/template.py", "write")
        assert result["decision"] == "allow"

    def test_read_tpls_allowed(self):
        result = validate_layer_access("pool-e", "tpls/snapshots/foo.py", "read")
        assert result["decision"] == "allow"

    def test_read_eval_blocked(self):
        result = validate_layer_access("pool-e", "eval/criteria/rubric.md", "read")
        assert result["decision"] == "block"

    def test_write_eval_blocked(self):
        result = validate_layer_access("pool-e", "eval/scripts/check.py", "write")
        assert result["decision"] == "block"

    def test_read_regs_allowed(self):
        result = validate_layer_access("pool-e", "regs/config.yaml", "read")
        assert result["decision"] == "allow"

    def test_write_regs_allowed(self):
        result = validate_layer_access("pool-e", "regs/config.yaml", "write")
        assert result["decision"] == "allow"

    def test_read_orchestrator_blocked(self):
        result = validate_layer_access("pool-e", "eval-loop/plan.md", "read")
        assert result["decision"] == "block"

    def test_write_orchestrator_blocked(self):
        result = validate_layer_access("pool-e", "eval-loop/plan.md", "write")
        assert result["decision"] == "block"

    def test_read_unknown_layer_allowed(self):
        """Non-layer paths allow reads for pool-e."""
        result = validate_layer_access("pool-e", "src/main.py", "read")
        assert result["decision"] == "allow"

    def test_write_unknown_layer_blocked(self):
        """Pool roles cannot write non-layer paths."""
        result = validate_layer_access("pool-e", "src/main.py", "write")
        assert result["decision"] == "block"


# ─── pool-t (test author): nuanced eval access ─────────────────────

class TestPoolT:
    # Reads allowed
    def test_read_eval_criteria_allowed(self):
        result = validate_layer_access("pool-t", "eval/criteria/rubric.md", "read")
        assert result["decision"] == "allow"

    def test_read_eval_tiers_allowed(self):
        result = validate_layer_access("pool-t", "eval/tiers/tier1.yaml", "read")
        assert result["decision"] == "allow"

    # Write allowed
    def test_write_eval_scripts_allowed(self):
        result = validate_layer_access("pool-t", "eval/scripts/check_format.py", "write")
        assert result["decision"] == "allow"

    # Write blocked on other eval subdirs
    def test_write_eval_criteria_blocked(self):
        result = validate_layer_access("pool-t", "eval/criteria/rubric.md", "write")
        assert result["decision"] == "block"

    def test_write_eval_tiers_blocked(self):
        result = validate_layer_access("pool-t", "eval/tiers/tier1.yaml", "write")
        assert result["decision"] == "block"

    def test_write_eval_gates_blocked(self):
        result = validate_layer_access("pool-t", "eval/gates/gate1.yaml", "write")
        assert result["decision"] == "block"

    def test_write_eval_pools_blocked(self):
        result = validate_layer_access("pool-t", "eval/pools/pool-e.yaml", "write")
        assert result["decision"] == "block"

    def test_write_eval_frozen_lock_blocked(self):
        result = validate_layer_access("pool-t", "eval/FROZEN.lock", "write")
        assert result["decision"] == "block"

    # Read blocked on other eval subdirs
    def test_read_eval_scripts_blocked(self):
        result = validate_layer_access("pool-t", "eval/scripts/check.py", "read")
        assert result["decision"] == "block"

    def test_read_eval_gates_blocked(self):
        result = validate_layer_access("pool-t", "eval/gates/gate1.yaml", "read")
        assert result["decision"] == "block"

    def test_read_eval_pools_blocked(self):
        result = validate_layer_access("pool-t", "eval/pools/pool-e.yaml", "read")
        assert result["decision"] == "block"

    # tpls and regs blocked entirely
    def test_read_tpls_blocked(self):
        result = validate_layer_access("pool-t", "tpls/template.py", "read")
        assert result["decision"] == "block"

    def test_write_tpls_blocked(self):
        result = validate_layer_access("pool-t", "tpls/template.py", "write")
        assert result["decision"] == "block"

    def test_read_regs_blocked(self):
        result = validate_layer_access("pool-t", "regs/config.yaml", "read")
        assert result["decision"] == "block"

    def test_write_regs_blocked(self):
        result = validate_layer_access("pool-t", "regs/config.yaml", "write")
        assert result["decision"] == "block"

    # orchestrator blocked
    def test_read_orchestrator_blocked(self):
        result = validate_layer_access("pool-t", "eval-loop/plan.md", "read")
        assert result["decision"] == "block"

    def test_write_orchestrator_blocked(self):
        result = validate_layer_access("pool-t", "eval-loop/plan.md", "write")
        assert result["decision"] == "block"

    # Non-layer paths: reads pass through, writes blocked
    def test_read_unknown_layer_allowed(self):
        result = validate_layer_access("pool-t", "src/main.py", "read")
        assert result["decision"] == "allow"

    def test_write_unknown_layer_blocked(self):
        """Pool roles cannot write non-layer paths."""
        result = validate_layer_access("pool-t", "src/main.py", "write")
        assert result["decision"] == "block"


# ─── pool-v (verify): read eval/scripts + regs, no writes ──────────

class TestPoolV:
    # Read allowed
    def test_read_eval_scripts_allowed(self):
        result = validate_layer_access("pool-v", "eval/scripts/check.py", "read")
        assert result["decision"] == "allow"

    def test_read_regs_allowed(self):
        result = validate_layer_access("pool-v", "regs/config.yaml", "read")
        assert result["decision"] == "allow"

    # Read blocked
    def test_read_eval_criteria_blocked(self):
        result = validate_layer_access("pool-v", "eval/criteria/rubric.md", "read")
        assert result["decision"] == "block"

    def test_read_eval_tiers_blocked(self):
        result = validate_layer_access("pool-v", "eval/tiers/tier1.yaml", "read")
        assert result["decision"] == "block"

    def test_read_eval_gates_blocked(self):
        result = validate_layer_access("pool-v", "eval/gates/gate1.yaml", "read")
        assert result["decision"] == "block"

    def test_read_eval_pools_blocked(self):
        result = validate_layer_access("pool-v", "eval/pools/pool-e.yaml", "read")
        assert result["decision"] == "block"

    def test_read_tpls_blocked(self):
        result = validate_layer_access("pool-v", "tpls/template.py", "read")
        assert result["decision"] == "block"

    def test_read_orchestrator_blocked(self):
        result = validate_layer_access("pool-v", "eval-loop/plan.md", "read")
        assert result["decision"] == "block"

    # All writes blocked
    def test_write_eval_scripts_blocked(self):
        result = validate_layer_access("pool-v", "eval/scripts/check.py", "write")
        assert result["decision"] == "block"

    def test_write_regs_blocked(self):
        result = validate_layer_access("pool-v", "regs/config.yaml", "write")
        assert result["decision"] == "block"

    def test_write_tpls_blocked(self):
        result = validate_layer_access("pool-v", "tpls/template.py", "write")
        assert result["decision"] == "block"

    def test_write_orchestrator_blocked(self):
        result = validate_layer_access("pool-v", "eval-loop/plan.md", "write")
        assert result["decision"] == "block"

    # Non-layer pass through
    def test_read_unknown_layer_allowed(self):
        result = validate_layer_access("pool-v", "src/main.py", "read")
        assert result["decision"] == "allow"

    def test_write_unknown_layer_blocked(self):
        """pool-v cannot write anything, even non-layer paths."""
        result = validate_layer_access("pool-v", "src/main.py", "write")
        assert result["decision"] == "block"


# ─── pool-r (read): read regs/ only, no writes ─────────────────────

class TestPoolR:
    # Read allowed
    def test_read_regs_allowed(self):
        result = validate_layer_access("pool-r", "regs/config.yaml", "read")
        assert result["decision"] == "allow"

    # Read blocked
    def test_read_eval_blocked(self):
        result = validate_layer_access("pool-r", "eval/criteria/rubric.md", "read")
        assert result["decision"] == "block"

    def test_read_tpls_blocked(self):
        result = validate_layer_access("pool-r", "tpls/template.py", "read")
        assert result["decision"] == "block"

    def test_read_orchestrator_blocked(self):
        result = validate_layer_access("pool-r", "eval-loop/plan.md", "read")
        assert result["decision"] == "block"

    # All writes blocked
    def test_write_regs_blocked(self):
        result = validate_layer_access("pool-r", "regs/config.yaml", "write")
        assert result["decision"] == "block"

    def test_write_eval_blocked(self):
        result = validate_layer_access("pool-r", "eval/scripts/check.py", "write")
        assert result["decision"] == "block"

    def test_write_tpls_blocked(self):
        result = validate_layer_access("pool-r", "tpls/template.py", "write")
        assert result["decision"] == "block"

    # Non-layer pass through for reads
    def test_read_unknown_layer_allowed(self):
        result = validate_layer_access("pool-r", "src/main.py", "read")
        assert result["decision"] == "allow"

    def test_write_unknown_layer_blocked(self):
        """pool-r cannot write anything."""
        result = validate_layer_access("pool-r", "src/main.py", "write")
        assert result["decision"] == "block"


# ─── orchestrator: read+write eval-loop/ only, no eval writes ────

class TestOrchestrator:
    # Read + write orchestrator allowed
    def test_read_orchestrator_allowed(self):
        result = validate_layer_access("orchestrator", "eval-loop/plan.md", "read")
        assert result["decision"] == "allow"

    def test_write_orchestrator_allowed(self):
        result = validate_layer_access("orchestrator", "eval-loop/dispatch/task.md", "write")
        assert result["decision"] == "allow"

    # Eval writes blocked
    def test_write_eval_blocked(self):
        result = validate_layer_access("orchestrator", "eval/scripts/check.py", "write")
        assert result["decision"] == "block"

    def test_write_eval_criteria_blocked(self):
        result = validate_layer_access("orchestrator", "eval/criteria/rubric.md", "write")
        assert result["decision"] == "block"

    # Other layers blocked
    def test_read_eval_blocked(self):
        result = validate_layer_access("orchestrator", "eval/criteria/rubric.md", "read")
        assert result["decision"] == "block"

    def test_read_tpls_blocked(self):
        result = validate_layer_access("orchestrator", "tpls/template.py", "read")
        assert result["decision"] == "block"

    def test_write_tpls_blocked(self):
        result = validate_layer_access("orchestrator", "tpls/template.py", "write")
        assert result["decision"] == "block"

    def test_read_regs_blocked(self):
        result = validate_layer_access("orchestrator", "regs/config.yaml", "read")
        assert result["decision"] == "block"

    def test_write_regs_blocked(self):
        result = validate_layer_access("orchestrator", "regs/config.yaml", "write")
        assert result["decision"] == "block"

    # Non-layer paths: reads pass through, writes blocked
    def test_read_unknown_layer_allowed(self):
        result = validate_layer_access("orchestrator", "src/main.py", "read")
        assert result["decision"] == "allow"

    def test_write_unknown_layer_blocked(self):
        """Pool roles cannot write non-layer paths."""
        result = validate_layer_access("orchestrator", "src/main.py", "write")
        assert result["decision"] == "block"


# ─── Non-pool roles pass through ───────────────────────────────────

class TestNonPoolRoles:
    def test_worker_passes_through(self):
        result = validate_layer_access("worker", "eval/criteria/rubric.md", "write")
        assert result["decision"] == "allow"

    def test_sdet_passes_through(self):
        result = validate_layer_access("sdet-unit", "tpls/template.py", "read")
        assert result["decision"] == "allow"

    def test_team_lead_passes_through(self):
        result = validate_layer_access("team-lead", "regs/config.yaml", "write")
        assert result["decision"] == "allow"

    def test_behavior_spec_writer_passes_through(self):
        result = validate_layer_access("behavior-spec-writer", "eval/scripts/check.py", "read")
        assert result["decision"] == "allow"

    def test_empty_role_passes_through(self):
        result = validate_layer_access("", "eval/criteria/rubric.md", "write")
        assert result["decision"] == "allow"

    def test_none_role_passes_through(self):
        result = validate_layer_access(None, "eval/criteria/rubric.md", "write")
        assert result["decision"] == "allow"


# ─── main() integration tests ──────────────────────────────────────

class TestMain:
    def test_main_write_tool_sets_write_operation(self):
        """Edit tool triggers write operation."""
        from hooks.layer_fence import main
        hook_input = json.dumps({
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/eval/criteria/rubric.md"},
        })
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
            patch("os.environ", {"OMNI_POOL": "pool-e"}),
            patch("hooks.layer_fence.find_project_root", return_value="/project"),
        ):
            mock_stdin.read.return_value = hook_input
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "block"

    def test_main_read_tool_sets_read_operation(self):
        """Read tool triggers read operation."""
        from hooks.layer_fence import main
        hook_input = json.dumps({
            "tool_name": "Read",
            "tool_input": {"file_path": "/project/eval/criteria/rubric.md"},
        })
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
            patch("os.environ", {"OMNI_POOL": "pool-e"}),
            patch("hooks.layer_fence.find_project_root", return_value="/project"),
        ):
            mock_stdin.read.return_value = hook_input
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "block"

    def test_main_no_pool_env_allows(self):
        """No OMNI_POOL env var means non-pool role, pass through."""
        from hooks.layer_fence import main
        hook_input = json.dumps({
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/eval/criteria/rubric.md"},
        })
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
            patch("os.environ", {}),
            patch("hooks.layer_fence.find_project_root", return_value="/project"),
        ):
            mock_stdin.read.return_value = hook_input
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "allow"

    def test_main_write_tool_name(self):
        """Write tool triggers write operation."""
        from hooks.layer_fence import main
        hook_input = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "/project/eval/scripts/check.py"},
        })
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
            patch("os.environ", {"OMNI_POOL": "pool-t"}),
            patch("hooks.layer_fence.find_project_root", return_value="/project"),
        ):
            mock_stdin.read.return_value = hook_input
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "allow"

    def test_main_notebook_edit_is_write(self):
        """NotebookEdit tool triggers write operation."""
        from hooks.layer_fence import main
        hook_input = json.dumps({
            "tool_name": "NotebookEdit",
            "tool_input": {"file_path": "/project/tpls/notebook.ipynb"},
        })
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
            patch("os.environ", {"OMNI_POOL": "pool-e"}),
            patch("hooks.layer_fence.find_project_root", return_value="/project"),
        ):
            mock_stdin.read.return_value = hook_input
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "allow"

    def test_main_invalid_json_allows(self):
        """Invalid JSON input gracefully allows."""
        from hooks.layer_fence import main
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdin.read.return_value = "not json"
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "allow"

    def test_main_no_project_root_allows(self):
        """No project root found gracefully allows."""
        from hooks.layer_fence import main
        hook_input = json.dumps({
            "tool_name": "Edit",
            "tool_input": {"file_path": "/some/path/eval/scripts/check.py"},
        })
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
            patch("os.environ", {"OMNI_POOL": "pool-e"}),
            patch("hooks.layer_fence.find_project_root", return_value=None),
        ):
            mock_stdin.read.return_value = hook_input
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "allow"

    def test_main_relative_path_extraction(self):
        """file_path is made relative to project_root for layer detection."""
        from hooks.layer_fence import main
        hook_input = json.dumps({
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/tpls/template.py"},
        })
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.stdout") as mock_stdout,
            patch("os.environ", {"OMNI_POOL": "pool-e"}),
            patch("hooks.layer_fence.find_project_root", return_value="/project"),
        ):
            mock_stdin.read.return_value = hook_input
            written = []
            mock_stdout.write = lambda x: written.append(x)
            main()
            output = json.loads("".join(written))
            assert output["decision"] == "allow"


# ─── Edge cases and reason messages ─────────────────────────────────

class TestBlockReasons:
    def test_block_reason_includes_role(self):
        result = validate_layer_access("pool-e", "eval/scripts/check.py", "write")
        assert "pool-e" in result["reason"]

    def test_block_reason_includes_layer(self):
        result = validate_layer_access("pool-e", "eval/scripts/check.py", "write")
        assert "eval" in result["reason"]

    def test_block_reason_includes_operation(self):
        result = validate_layer_access("pool-v", "eval/scripts/check.py", "write")
        assert "write" in result["reason"]
