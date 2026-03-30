"""Tests for the destructive_git_gate hook."""

import json
from unittest.mock import patch

from hooks.destructive_git_gate import check_destructive_git


class TestBlockedCommands:
    """Commands that MUST be blocked."""

    def test_blocks_git_rm(self):
        result = check_destructive_git("git rm somefile.py")
        assert result["decision"] == "block"
        assert "reason" in result

    def test_blocks_git_reset_hard(self):
        result = check_destructive_git("git reset --hard")
        assert result["decision"] == "block"

    def test_blocks_git_reset_hard_with_ref(self):
        result = check_destructive_git("git reset --hard HEAD~3")
        assert result["decision"] == "block"

    def test_blocks_git_push_force(self):
        result = check_destructive_git("git push --force")
        assert result["decision"] == "block"

    def test_blocks_git_push_force_with_remote(self):
        result = check_destructive_git("git push --force origin main")
        assert result["decision"] == "block"

    def test_blocks_git_push_force_with_lease(self):
        result = check_destructive_git("git push --force-with-lease")
        assert result["decision"] == "block"

    def test_blocks_git_push_force_with_lease_and_remote(self):
        result = check_destructive_git("git push --force-with-lease origin feat/x")
        assert result["decision"] == "block"

    def test_blocks_git_branch_delete(self):
        result = check_destructive_git("git branch -D my-branch")
        assert result["decision"] == "block"

    def test_blocks_git_clean_force(self):
        result = check_destructive_git("git clean -f")
        assert result["decision"] == "block"

    def test_blocks_git_clean_fd(self):
        result = check_destructive_git("git clean -fd")
        assert result["decision"] == "block"

    def test_blocks_git_checkout_dot(self):
        result = check_destructive_git("git checkout -- .")
        assert result["decision"] == "block"

    def test_blocks_git_restore_dot(self):
        result = check_destructive_git("git restore .")
        assert result["decision"] == "block"

    def test_blocks_rm_rf(self):
        result = check_destructive_git("rm -rf /some/path")
        assert result["decision"] == "block"

    def test_blocks_rm_rf_current_dir(self):
        result = check_destructive_git("rm -rf .")
        assert result["decision"] == "block"

    def test_blocks_rm_fr(self):
        """rm -fr is equivalent to rm -rf."""
        result = check_destructive_git("rm -fr /tmp/stuff")
        assert result["decision"] == "block"


class TestAllowedCommands:
    """Commands that must NOT be blocked."""

    def test_allows_git_commit(self):
        result = check_destructive_git("git commit -m 'fix: something'")
        assert result["decision"] == "allow"

    def test_allows_git_push(self):
        result = check_destructive_git("git push origin main")
        assert result["decision"] == "allow"

    def test_allows_git_push_simple(self):
        result = check_destructive_git("git push")
        assert result["decision"] == "allow"

    def test_allows_git_branch_create(self):
        result = check_destructive_git("git branch my-new-branch")
        assert result["decision"] == "allow"

    def test_allows_git_branch_list(self):
        result = check_destructive_git("git branch")
        assert result["decision"] == "allow"

    def test_allows_git_merge(self):
        result = check_destructive_git("git merge feat/auth")
        assert result["decision"] == "allow"

    def test_allows_git_status(self):
        result = check_destructive_git("git status")
        assert result["decision"] == "allow"

    def test_allows_git_log(self):
        result = check_destructive_git("git log --oneline -5")
        assert result["decision"] == "allow"

    def test_allows_non_git_command(self):
        result = check_destructive_git("python -m pytest")
        assert result["decision"] == "allow"

    def test_allows_git_add(self):
        result = check_destructive_git("git add .")
        assert result["decision"] == "allow"

    def test_allows_git_diff(self):
        result = check_destructive_git("git diff HEAD")
        assert result["decision"] == "allow"

    def test_allows_git_checkout_branch(self):
        result = check_destructive_git("git checkout -b feat/new")
        assert result["decision"] == "allow"

    def test_allows_git_restore_specific_file(self):
        result = check_destructive_git("git restore somefile.py")
        assert result["decision"] == "allow"


class TestMainEntryPoint:
    """Test the main() hook entry point."""

    def test_non_bash_tool_allowed(self):
        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/foo.py", "content": "x = 1"},
        }
        with patch("sys.stdin") as mock_stdin, patch("sys.stdout") as mock_stdout:
            mock_stdin.read.return_value = json.dumps(input_data)
            mock_stdout.write = lambda s: None

            from hooks.destructive_git_gate import main

            # Capture what gets written to stdout
            import io
            output = io.StringIO()
            with patch("sys.stdout", output):
                main()
            result = json.loads(output.getvalue())
            assert result["decision"] == "allow"

    def test_bash_tool_safe_command_allowed(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        }
        import io
        output = io.StringIO()
        with patch("sys.stdin") as mock_stdin, patch("sys.stdout", output):
            mock_stdin.read.return_value = json.dumps(input_data)
            from hooks.destructive_git_gate import main
            main()
        result = json.loads(output.getvalue())
        assert result["decision"] == "allow"

    def test_bash_tool_destructive_command_blocked(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git reset --hard"},
        }
        import io
        output = io.StringIO()
        with patch("sys.stdin") as mock_stdin, patch("sys.stdout", output):
            mock_stdin.read.return_value = json.dumps(input_data)
            from hooks.destructive_git_gate import main
            main()
        result = json.loads(output.getvalue())
        assert result["decision"] == "block"

    def test_invalid_json_input_allows(self):
        import io
        output = io.StringIO()
        with patch("sys.stdin") as mock_stdin, patch("sys.stdout", output):
            mock_stdin.read.return_value = "not json"
            from hooks.destructive_git_gate import main
            main()
        result = json.loads(output.getvalue())
        assert result["decision"] == "allow"
