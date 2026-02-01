"""Unit tests for CLI module."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def create_valid_config(tmp_path: Path, profiles: dict | None = None) -> Path:
    """Create a valid config file for testing.

    Args:
        tmp_path: Temporary directory path.
        profiles: Optional dict of profiles. Defaults to a single 'default' profile.

    Returns:
        Path to the created config file.
    """
    if profiles is None:
        profiles = {"default": {"applications": {}}}

    config_content = (
        "version: 1\n"
        "metadata:\n"
        "  captured_at: '2024-01-01T00:00:00'\n"
        "  source_machine: test-machine\n"
        "  macos_version: '14.0'\n"
        "  tool_version: '0.1.0'\n"
        "profiles:\n"
    )

    for profile_name, profile_data in profiles.items():
        config_content += f"  {profile_name}:\n"
        if "applications" in profile_data:
            config_content += "    applications: {}\n"

    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)
    return config_path


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_returns_default_when_no_env(self):
        """Return default config dir when no environment variable set."""
        from macsetup.cli import get_config_dir

        with patch.dict("os.environ", {}, clear=True):
            result = get_config_dir()
            assert result == Path.home() / ".config" / "macsetup"

    def test_respects_env_override(self):
        """Return environment variable override when set."""
        from macsetup.cli import get_config_dir

        with patch.dict("os.environ", {"MACSETUP_CONFIG_DIR": "/custom/path"}):
            result = get_config_dir()
            assert result == Path("/custom/path")


class TestCmdSetup:
    """Tests for cmd_setup function."""

    def test_returns_error_when_config_missing(self, tmp_path):
        """Return exit code 2 when config file doesn't exist."""
        from macsetup.cli import cmd_setup

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dry_run=False,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        result = cmd_setup(args)
        assert result == 2

    def test_returns_error_for_invalid_config(self, tmp_path):
        """Return exit code 2 when config file is invalid."""
        from macsetup.cli import cmd_setup

        # Create invalid config
        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: content:")

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dry_run=False,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        result = cmd_setup(args)
        assert result == 2

    def test_returns_error_for_missing_profile(self, tmp_path):
        """Return exit code 2 when profile doesn't exist in config."""
        from macsetup.cli import cmd_setup

        # Create valid config with only 'default' profile
        create_valid_config(tmp_path)

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="nonexistent",
            json=False,
            quiet=True,
            dry_run=False,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        result = cmd_setup(args)
        assert result == 2

    def test_dry_run_returns_success(self, tmp_path):
        """Dry-run mode returns 0 without executing."""
        from macsetup.cli import cmd_setup

        # Create minimal valid config
        create_valid_config(tmp_path)

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dry_run=True,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        result = cmd_setup(args)
        assert result == 0

    def test_successful_setup_returns_zero(self, tmp_path):
        """Successful setup returns exit code 0."""
        from macsetup.cli import cmd_setup

        # Create minimal valid config
        create_valid_config(tmp_path)

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dry_run=False,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        # Mock SetupService
        with patch("macsetup.services.setup.SetupService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.run.return_value = MagicMock(
                success=True,
                completed_count=5,
                failed_count=0,
                failed_items=[],
                manual_apps=[],
                interrupted=False,
            )
            mock_service_class.return_value = mock_service

            result = cmd_setup(args)
            assert result == 0
            mock_service.run.assert_called_once_with(resume=False)

    def test_setup_with_failures_returns_three(self, tmp_path):
        """Setup with failures returns exit code 3."""
        from macsetup.cli import cmd_setup

        # Create minimal valid config
        create_valid_config(tmp_path)

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dry_run=False,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        # Mock SetupService with failures
        with patch("macsetup.services.setup.SetupService") as mock_service_class:
            mock_service = MagicMock()
            failed_item = MagicMock(type="formula", identifier="git", error="Already installed")
            mock_service.run.return_value = MagicMock(
                success=False,
                completed_count=3,
                failed_count=1,
                failed_items=[failed_item],
                manual_apps=[],
                interrupted=False,
            )
            mock_service_class.return_value = mock_service

            result = cmd_setup(args)
            assert result == 3

    def test_interrupted_setup_returns_130(self, tmp_path):
        """Interrupted setup (Ctrl+C) returns exit code 130."""
        from macsetup.cli import cmd_setup

        # Create minimal valid config
        create_valid_config(tmp_path)

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dry_run=False,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        # Mock SetupService with interruption
        with patch("macsetup.services.setup.SetupService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.run.return_value = MagicMock(
                success=False,
                completed_count=2,
                failed_count=0,
                failed_items=[],
                manual_apps=[],
                interrupted=True,
            )
            mock_service_class.return_value = mock_service

            result = cmd_setup(args)
            assert result == 130

    def test_json_output_format(self, tmp_path, capsys):
        """JSON output format includes all required fields."""
        from macsetup.cli import cmd_setup

        # Create minimal valid config
        create_valid_config(tmp_path)

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=True,
            quiet=False,
            dry_run=False,
            force=False,
            no_dotfiles=False,
            no_preferences=False,
            resume=False,
        )

        # Mock SetupService
        with patch("macsetup.services.setup.SetupService") as mock_service_class:
            mock_service = MagicMock()
            # Create proper mock objects with correct attributes
            failed_item = MagicMock()
            failed_item.type = "formula"
            failed_item.identifier = "git"
            failed_item.error = "Failed"

            manual_app = MagicMock()
            manual_app.name = "Xcode"
            manual_app.url = "https://developer.apple.com"

            mock_service.run.return_value = MagicMock(
                success=False,
                completed_count=3,
                failed_count=1,
                failed_items=[failed_item],
                manual_apps=[manual_app],
                interrupted=False,
            )
            mock_service_class.return_value = mock_service

            cmd_setup(args)
            captured = capsys.readouterr()
            output = json.loads(captured.out)

            assert output["success"] is False
            assert output["completed"] == 3
            assert output["failed"] == 1
            assert len(output["failures"]) == 1
            assert output["failures"][0]["type"] == "formula"
            assert output["failures"][0]["identifier"] == "git"
            assert len(output["manual_required"]) == 1
            assert output["manual_required"][0]["name"] == "Xcode"

    def test_service_created_with_correct_params(self, tmp_path):
        """SetupService is created with correct parameters."""
        from macsetup.cli import cmd_setup

        # Create minimal valid config with custom-profile
        create_valid_config(tmp_path, profiles={"custom-profile": {"applications": {}}})

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="custom-profile",
            json=False,
            quiet=True,
            dry_run=False,
            force=True,
            no_dotfiles=True,
            no_preferences=True,
            resume=True,
        )

        # Mock SetupService
        with patch("macsetup.services.setup.SetupService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.run.return_value = MagicMock(
                success=True,
                completed_count=0,
                failed_count=0,
                failed_items=[],
                manual_apps=[],
                interrupted=False,
            )
            mock_service_class.return_value = mock_service

            cmd_setup(args)

            # Verify SetupService was created with correct args
            call_kwargs = mock_service_class.call_args[1]
            assert call_kwargs["profile"] == "custom-profile"
            assert call_kwargs["force"] is True
            assert call_kwargs["skip_dotfiles"] is True
            assert call_kwargs["skip_preferences"] is True
            assert call_kwargs["config_dir"] == tmp_path

            # Verify run was called with resume=True
            mock_service.run.assert_called_once_with(resume=True)


class TestMain:
    """Tests for main function."""

    def test_shows_help_when_no_command(self, capsys):
        """Show help when no command specified."""
        from macsetup.cli import main

        result = main([])
        assert result == 0

        captured = capsys.readouterr()
        assert "macsetup" in captured.out
        assert "commands" in captured.out

    def test_resolves_config_dir_from_flag(self, tmp_path):
        """Resolve config dir from --config-dir flag."""
        from macsetup.cli import main

        # Create minimal valid config
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        create_valid_config(custom_dir)

        # Mock SetupService
        with patch("macsetup.services.setup.SetupService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.run.return_value = MagicMock(
                success=True,
                completed_count=0,
                failed_count=0,
                failed_items=[],
                manual_apps=[],
                interrupted=False,
            )
            mock_service_class.return_value = mock_service

            main(["--config-dir", str(custom_dir), "--quiet", "setup"])

            # Verify config_dir was set correctly
            call_kwargs = mock_service_class.call_args[1]
            assert call_kwargs["config_dir"] == custom_dir

    def test_resolves_config_dir_from_env(self, tmp_path):
        """Resolve config dir from environment variable when no flag."""
        from macsetup.cli import main

        # Create minimal valid config
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        create_valid_config(custom_dir)

        # Mock SetupService
        with patch("macsetup.services.setup.SetupService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.run.return_value = MagicMock(
                success=True,
                completed_count=0,
                failed_count=0,
                failed_items=[],
                manual_apps=[],
                interrupted=False,
            )
            mock_service_class.return_value = mock_service

            with patch.dict("os.environ", {"MACSETUP_CONFIG_DIR": str(custom_dir)}):
                main(["--quiet", "setup"])

                # Verify config_dir was set from env
                call_kwargs = mock_service_class.call_args[1]
                assert call_kwargs["config_dir"] == custom_dir


class TestCreateParser:
    """Tests for create_parser function."""

    def test_parser_accepts_version_flag(self):
        """Parser accepts --version flag."""
        from macsetup.cli import create_parser

        parser = create_parser()

        # Version flag causes SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_setup_command_accepts_all_flags(self):
        """Setup command accepts all expected flags."""
        from macsetup.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "setup",
            "--profile", "custom",
            "--dry-run",
            "--force",
            "--resume",
            "--no-dotfiles",
            "--no-preferences",
        ])

        assert args.command == "setup"
        assert args.profile == "custom"
        assert args.dry_run is True
        assert args.force is True
        assert args.resume is True
        assert args.no_dotfiles is True
        assert args.no_preferences is True

    def test_global_flags_work_with_all_commands(self):
        """Global flags (--json, --quiet, --verbose) work with all commands."""
        from macsetup.cli import create_parser

        parser = create_parser()

        for cmd in ["setup", "capture", "preview"]:
            # Global flags must come before the command in argparse
            args = parser.parse_args(["--json", "--quiet", cmd])
            assert args.json is True
            assert args.quiet is True
