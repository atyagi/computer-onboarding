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

    def test_reads_pointer_file_when_present(self, tmp_path):
        """get_config_dir() reads pointer file and returns the path it contains."""
        from macsetup.cli import get_config_dir

        # Set up pointer file pointing to an icloud-like dir
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer_file = default_dir / "config-dir"
        pointer_file.write_text(str(icloud_dir))

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("macsetup.cli.DEFAULT_CONFIG_DIR", default_dir),
        ):
            result = get_config_dir()
            assert result == icloud_dir

    def test_returns_default_when_pointer_absent(self, tmp_path):
        """get_config_dir() returns default when no pointer file exists."""
        from macsetup.cli import get_config_dir

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("macsetup.cli.DEFAULT_CONFIG_DIR", default_dir),
        ):
            result = get_config_dir()
            assert result == default_dir

    def test_cli_flag_overrides_pointer(self, tmp_path):
        """--config-dir CLI flag takes precedence over pointer file."""
        from macsetup.cli import main

        # Set up pointer file
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer_file = default_dir / "config-dir"
        pointer_file.write_text(str(icloud_dir))

        cli_override = tmp_path / "cli_override"
        cli_override.mkdir()
        create_valid_config(cli_override)

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("macsetup.cli.DEFAULT_CONFIG_DIR", default_dir),
            patch("macsetup.services.setup.SetupService") as mock_cls,
        ):
            mock_service = MagicMock()
            mock_service.run.return_value = MagicMock(
                success=True,
                completed_count=0,
                failed_count=0,
                failed_items=[],
                manual_apps=[],
                interrupted=False,
            )
            mock_cls.return_value = mock_service

            main(["--config-dir", str(cli_override), "--quiet", "setup"])
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["config_dir"] == cli_override

    def test_env_var_overrides_pointer(self, tmp_path):
        """MACSETUP_CONFIG_DIR env var takes precedence over pointer file."""
        from macsetup.cli import get_config_dir

        # Set up pointer file
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer_file = default_dir / "config-dir"
        pointer_file.write_text(str(icloud_dir))

        env_override = tmp_path / "env_override"
        env_override.mkdir()

        with (
            patch.dict("os.environ", {"MACSETUP_CONFIG_DIR": str(env_override)}),
            patch("macsetup.cli.DEFAULT_CONFIG_DIR", default_dir),
        ):
            result = get_config_dir()
            assert result == env_override

    def test_errors_when_pointer_references_nonexistent_path(self, tmp_path):
        """get_config_dir() raises ConfigDirError when pointer references nonexistent path."""
        from macsetup.cli import ConfigDirError, get_config_dir

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer_file = default_dir / "config-dir"
        pointer_file.write_text("/nonexistent/path/that/does/not/exist")

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("macsetup.cli.DEFAULT_CONFIG_DIR", default_dir),
        ):
            with pytest.raises(ConfigDirError):
                get_config_dir()


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
        args = parser.parse_args(
            [
                "setup",
                "--profile",
                "custom",
                "--dry-run",
                "--force",
                "--resume",
                "--no-dotfiles",
                "--no-preferences",
            ]
        )

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


class TestCmdCapture:
    """Tests for cmd_capture function."""

    def _make_args(self, tmp_path, **overrides):
        """Create a Namespace with capture defaults."""
        defaults = {
            "resolved_config_dir": tmp_path,
            "profile": "default",
            "json": False,
            "quiet": True,
            "dotfiles": None,
            "preferences": None,
            "skip_apps": False,
            "skip_dotfiles": False,
            "skip_preferences": False,
            "exclude_dotfiles": None,
            "include_sensitive": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _mock_config(self):
        """Create a mock Configuration returned by CaptureService."""
        mock_config = MagicMock()
        mock_profile = MagicMock()
        mock_profile.applications = MagicMock()
        mock_profile.applications.homebrew = MagicMock(
            taps=["tap1"], formulas=["git"], casks=["firefox"]
        )
        mock_profile.applications.mas = [MagicMock(id=1, name="App")]
        mock_profile.dotfiles = [MagicMock(path="~/.zshrc")]
        mock_profile.preferences = [MagicMock(domain="com.apple.dock")]
        mock_config.profiles = {"default": mock_profile}
        return mock_config

    def test_capture_success(self, tmp_path, capsys):
        """Capture returns exit 0 and produces text output."""
        from macsetup.cli import cmd_capture

        args = self._make_args(tmp_path, quiet=False)
        mock_config = self._mock_config()

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            result = cmd_capture(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Capturing configuration" in captured.out

    def test_capture_json_output(self, tmp_path, capsys):
        """JSON output includes success, config_path, profile, config."""
        from macsetup.cli import cmd_capture

        args = self._make_args(tmp_path, json=True)
        mock_config = self._mock_config()

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
            patch("macsetup.models.config.config_to_dict", return_value={"version": 1}),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            result = cmd_capture(args)

        assert result == 0
        output = json.loads(capsys.readouterr().out)
        assert output["success"] is True
        assert "config_path" in output
        assert output["profile"] == "default"
        assert "config" in output

    def test_capture_quiet_suppresses_output(self, tmp_path, capsys):
        """No stdout when --quiet is set."""
        from macsetup.cli import cmd_capture

        args = self._make_args(tmp_path, quiet=True)
        mock_config = self._mock_config()

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            result = cmd_capture(args)

        assert result == 0
        assert capsys.readouterr().out == ""

    def test_capture_passes_skip_flags(self, tmp_path):
        """skip_apps, skip_dotfiles, skip_preferences forwarded to service."""
        from macsetup.cli import cmd_capture

        args = self._make_args(tmp_path, skip_apps=True, skip_dotfiles=True, skip_preferences=True)
        mock_config = self._mock_config()

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            cmd_capture(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["skip_apps"] is True
            assert call_kwargs["skip_dotfiles"] is True
            assert call_kwargs["skip_preferences"] is True

    def test_capture_parses_dotfiles_list(self, tmp_path):
        """Comma-separated --dotfiles parsed into list."""
        from macsetup.cli import cmd_capture

        args = self._make_args(tmp_path, dotfiles="~/.zshrc, ~/.gitconfig")
        mock_config = self._mock_config()

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            cmd_capture(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["dotfiles"] == ["~/.zshrc", "~/.gitconfig"]

    def test_capture_parses_preferences_list(self, tmp_path):
        """Comma-separated --preferences parsed into list."""
        from macsetup.cli import cmd_capture

        args = self._make_args(tmp_path, preferences="com.apple.dock, com.apple.finder")
        mock_config = self._mock_config()

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            cmd_capture(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["preference_domains"] == [
                "com.apple.dock",
                "com.apple.finder",
            ]

    def test_capture_custom_profile(self, tmp_path):
        """Profile name forwarded to service."""
        from macsetup.cli import cmd_capture

        args = self._make_args(tmp_path, profile="work")
        mock_config = self._mock_config()
        mock_config.profiles = {"work": mock_config.profiles["default"]}

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            cmd_capture(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["profile"] == "work"


class TestCmdPreview:
    """Tests for cmd_preview function."""

    def _make_args(self, tmp_path, **overrides):
        defaults = {
            "resolved_config_dir": tmp_path,
            "profile": "default",
            "json": False,
            "quiet": True,
            "diff": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_preview_missing_config(self, tmp_path):
        """Exit 2 when config file doesn't exist."""
        from macsetup.cli import cmd_preview

        args = self._make_args(tmp_path)
        result = cmd_preview(args)
        assert result == 2

    def test_preview_invalid_config(self, tmp_path):
        """Exit 2 when YAML is invalid."""
        from macsetup.cli import cmd_preview

        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: content:")

        args = self._make_args(tmp_path)
        result = cmd_preview(args)
        assert result == 2

    def test_preview_success(self, tmp_path, capsys):
        """Mock PreviewService, verify exit 0 and text output."""
        from macsetup.cli import cmd_preview

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, quiet=False)

        with patch("macsetup.services.preview.PreviewService") as mock_cls:
            mock_cls.return_value.preview.return_value = {
                "taps": ["homebrew/core"],
                "formulas": ["git"],
                "casks": ["firefox"],
                "mas": [],
                "dotfiles": [],
                "preferences": [],
            }
            result = cmd_preview(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Preview for profile" in captured.out

    def test_preview_json_output(self, tmp_path, capsys):
        """JSON structure includes {success, preview}."""
        from macsetup.cli import cmd_preview

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, json=True)

        with patch("macsetup.services.preview.PreviewService") as mock_cls:
            mock_cls.return_value.preview.return_value = {
                "taps": [],
                "formulas": ["git"],
                "casks": [],
                "mas": [],
                "dotfiles": [],
                "preferences": [],
            }
            result = cmd_preview(args)

        assert result == 0
        output = json.loads(capsys.readouterr().out)
        assert output["success"] is True
        assert "preview" in output

    def test_preview_diff_mode(self, tmp_path, capsys):
        """--diff calls service.diff()."""
        from macsetup.cli import cmd_preview

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, diff=True, quiet=False)

        with patch("macsetup.services.preview.PreviewService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.diff.return_value = {
                "taps_to_install": ["tap1"],
                "taps_installed": [],
                "formulas_to_install": [],
                "formulas_installed": [],
                "casks_to_install": [],
                "casks_installed": [],
                "mas_to_install": [],
                "mas_installed": [],
            }
            result = cmd_preview(args)

        assert result == 0
        mock_service.diff.assert_called_once()
        captured = capsys.readouterr()
        assert "Diff for profile" in captured.out

    def test_preview_diff_json_output(self, tmp_path, capsys):
        """Diff JSON structure includes {success, diff}."""
        from macsetup.cli import cmd_preview

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, diff=True, json=True)

        with patch("macsetup.services.preview.PreviewService") as mock_cls:
            mock_cls.return_value.diff.return_value = {
                "formulas_to_install": ["git"],
                "formulas_installed": [],
            }
            result = cmd_preview(args)

        assert result == 0
        output = json.loads(capsys.readouterr().out)
        assert output["success"] is True
        assert "diff" in output

    def test_preview_missing_profile(self, tmp_path):
        """Exit 2 when profile not found."""
        from macsetup.cli import cmd_preview

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, profile="nonexistent")
        result = cmd_preview(args)
        assert result == 2


class TestCmdSync:
    """Tests for cmd_sync function."""

    def _make_args(self, tmp_path, **overrides):
        defaults = {
            "resolved_config_dir": tmp_path,
            "json": False,
            "quiet": True,
            "sync_command": None,
            "interval": 60,
            "watch": True,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_sync_start_success(self, tmp_path):
        """Start sync returns exit 0 when not already running."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="start")

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.is_running.return_value = False
            mock_service.sync_now.return_value = True
            result = cmd_sync(args)

        assert result == 0

    def test_sync_start_already_running(self, tmp_path):
        """Exit 1 when daemon already running."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="start")

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.is_running.return_value = True
            result = cmd_sync(args)

        assert result == 1

    def test_sync_stop_success(self, tmp_path):
        """Stop returns exit 0."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="stop")

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.stop.return_value = True
            result = cmd_sync(args)

        assert result == 0

    def test_sync_stop_not_running(self, tmp_path):
        """Stop when not running still returns 0."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="stop")

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.stop.return_value = False
            result = cmd_sync(args)

        assert result == 0

    def test_sync_status(self, tmp_path, capsys):
        """Status text output."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="status", quiet=False)

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.status.return_value = {
                "running": True,
                "interval_minutes": 60,
                "config_dir": str(tmp_path),
            }
            result = cmd_sync(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "running" in captured.out.lower()

    def test_sync_status_json(self, tmp_path, capsys):
        """Status JSON includes running, interval_minutes, config_dir."""
        from macsetup.cli import cmd_sync

        status_data = {
            "running": False,
            "interval_minutes": 30,
            "config_dir": str(tmp_path),
        }
        args = self._make_args(tmp_path, sync_command="status", json=True)

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.status.return_value = status_data
            result = cmd_sync(args)

        assert result == 0
        output = json.loads(capsys.readouterr().out)
        assert output["running"] is False
        assert output["interval_minutes"] == 30
        assert "config_dir" in output

    def test_sync_now_success(self, tmp_path):
        """sync_now returns exit 0 on success."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="now")

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.sync_now.return_value = True
            result = cmd_sync(args)

        assert result == 0

    def test_sync_now_failure(self, tmp_path):
        """Exit 1 when sync_now fails."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="now")

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.sync_now.return_value = False
            result = cmd_sync(args)

        assert result == 1

    def test_sync_passes_interval(self, tmp_path):
        """--interval forwarded to SyncService."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="status", interval=120)

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.status.return_value = {
                "running": False,
                "interval_minutes": 120,
                "config_dir": str(tmp_path),
            }
            cmd_sync(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["interval_minutes"] == 120

    def test_sync_passes_watch(self, tmp_path):
        """--watch forwarded to SyncService."""
        from macsetup.cli import cmd_sync

        args = self._make_args(tmp_path, sync_command="status", watch=False)

        with patch("macsetup.services.sync.SyncService") as mock_cls:
            mock_cls.return_value.status.return_value = {
                "running": False,
                "interval_minutes": 60,
                "config_dir": str(tmp_path),
            }
            cmd_sync(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["watch"] is False


class TestCmdProfile:
    """Tests for cmd_profile function."""

    def _make_args(self, tmp_path, **overrides):
        defaults = {
            "resolved_config_dir": tmp_path,
            "json": False,
            "quiet": True,
            "profile_command": None,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_profile_list(self, tmp_path, capsys):
        """List profiles with text output."""
        from macsetup.cli import cmd_profile

        create_valid_config(
            tmp_path,
            profiles={
                "default": {"applications": {}},
                "work": {"applications": {}},
            },
        )
        args = self._make_args(tmp_path, profile_command="list", quiet=False)
        result = cmd_profile(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "default" in captured.out
        assert "work" in captured.out

    def test_profile_list_json(self, tmp_path, capsys):
        """JSON structure includes {profiles}."""
        from macsetup.cli import cmd_profile

        create_valid_config(
            tmp_path,
            profiles={
                "default": {"applications": {}},
                "work": {"applications": {}},
            },
        )
        args = self._make_args(tmp_path, profile_command="list", json=True)
        result = cmd_profile(args)

        assert result == 0
        output = json.loads(capsys.readouterr().out)
        assert "profiles" in output
        assert "default" in output["profiles"]
        assert "work" in output["profiles"]

    def test_profile_show(self, tmp_path, capsys):
        """Profile details displayed."""
        from macsetup.cli import cmd_profile

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, profile_command="show", name="default", quiet=False)

        with patch("macsetup.services.preview.PreviewService") as mock_cls:
            mock_cls.return_value.preview.return_value = {
                "taps": [],
                "formulas": ["git"],
                "casks": [],
                "mas": [],
                "dotfiles": [],
                "preferences": [],
            }
            result = cmd_profile(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Profile: default" in captured.out

    def test_profile_show_missing_profile(self, tmp_path):
        """Exit 2 for unknown profile."""
        from macsetup.cli import cmd_profile

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, profile_command="show", name="nonexistent")
        result = cmd_profile(args)
        assert result == 2

    def test_profile_diff(self, tmp_path, capsys):
        """Diff between two profiles."""
        from macsetup.cli import cmd_profile

        create_valid_config(
            tmp_path,
            profiles={
                "default": {"applications": {}},
                "work": {"applications": {}},
            },
        )
        args = self._make_args(
            tmp_path, profile_command="diff", name1="default", name2="work", quiet=False
        )

        with patch("macsetup.services.preview.PreviewService") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.preview.return_value = {
                "taps": [],
                "formulas": [],
                "casks": [],
                "mas": [],
                "dotfiles": [],
                "preferences": [],
            }
            mock_cls.return_value = mock_instance
            result = cmd_profile(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Comparing" in captured.out

    def test_profile_missing_config(self, tmp_path):
        """Exit 2 when config file doesn't exist."""
        from macsetup.cli import cmd_profile

        args = self._make_args(tmp_path, profile_command="list")
        result = cmd_profile(args)
        assert result == 2


class TestCaptureExcludeDotfilesFlag:
    """Tests for --exclude-dotfiles flag parsing (T016)."""

    def test_exclude_dotfiles_parses_comma_separated(self):
        """--exclude-dotfiles '.vimrc,.tmux.conf' parses to a list of paths."""
        from macsetup.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["capture", "--exclude-dotfiles", ".vimrc,.tmux.conf"])
        assert args.exclude_dotfiles == ".vimrc,.tmux.conf"

    def test_exclude_dotfiles_passed_to_service(self, tmp_path):
        """Exclusion list is passed through to CaptureService."""
        from macsetup.cli import cmd_capture

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dotfiles=None,
            preferences=None,
            skip_apps=False,
            skip_dotfiles=False,
            skip_preferences=False,
            exclude_dotfiles=".vimrc,.tmux.conf",
            include_sensitive=False,
        )
        mock_config = MagicMock()
        mock_profile = MagicMock()
        mock_profile.dotfiles = []
        mock_profile.preferences = []
        mock_profile.applications = MagicMock(homebrew=None, mas=[])
        mock_config.profiles = {"default": mock_profile}

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            cmd_capture(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["exclude_dotfiles"] == [".vimrc", ".tmux.conf"]


class TestCaptureIncludeSensitiveFlag:
    """Tests for --include-sensitive flag parsing (T017)."""

    def test_include_sensitive_is_boolean_flag(self):
        """--include-sensitive is a boolean flag."""
        from macsetup.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["capture", "--include-sensitive"])
        assert args.include_sensitive is True

    def test_include_sensitive_defaults_to_false(self):
        """--include-sensitive defaults to False."""
        from macsetup.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["capture"])
        assert args.include_sensitive is False

    def test_include_sensitive_passed_to_service(self, tmp_path):
        """Flag value is passed through to CaptureService."""
        from macsetup.cli import cmd_capture

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            profile="default",
            json=False,
            quiet=True,
            dotfiles=None,
            preferences=None,
            skip_apps=False,
            skip_dotfiles=False,
            skip_preferences=False,
            exclude_dotfiles=None,
            include_sensitive=True,
        )
        mock_config = MagicMock()
        mock_profile = MagicMock()
        mock_profile.dotfiles = []
        mock_profile.preferences = []
        mock_profile.applications = MagicMock(homebrew=None, mas=[])
        mock_config.profiles = {"default": mock_profile}

        with (
            patch("macsetup.services.capture.CaptureService") as mock_cls,
            patch("macsetup.models.config.save_config"),
        ):
            mock_cls.return_value.capture.return_value = mock_config
            cmd_capture(args)

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["include_sensitive"] is True


class TestCmdValidate:
    """Tests for cmd_validate function."""

    def _make_args(self, tmp_path, **overrides):
        defaults = {
            "resolved_config_dir": tmp_path,
            "json": False,
            "quiet": True,
            "strict": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_validate_valid_config(self, tmp_path, capsys):
        """Exit 0 for valid config."""
        from macsetup.cli import cmd_validate

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, quiet=False)

        with patch("macsetup.models.schema.validate_config", return_value=[]):
            result = cmd_validate(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "valid" in captured.out.lower()

    def test_validate_valid_json(self, tmp_path, capsys):
        """JSON output {valid: true} for valid config."""
        from macsetup.cli import cmd_validate

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, json=True)

        with patch("macsetup.models.schema.validate_config", return_value=[]):
            result = cmd_validate(args)

        assert result == 0
        output = json.loads(capsys.readouterr().out)
        assert output["valid"] is True

    def test_validate_missing_file(self, tmp_path):
        """Exit 2 when file doesn't exist."""
        from macsetup.cli import cmd_validate

        args = self._make_args(tmp_path)
        result = cmd_validate(args)
        assert result == 2

    def test_validate_invalid_yaml(self, tmp_path):
        """Exit 1 for YAML parse errors."""
        from macsetup.cli import cmd_validate

        config_path = tmp_path / "config.yaml"
        config_path.write_text(":\n  :\n    - :\n      bad")
        args = self._make_args(tmp_path)
        result = cmd_validate(args)
        assert result == 1

    def test_validate_schema_errors(self, tmp_path, capsys):
        """Exit 1 with error list for schema violations."""
        from macsetup.cli import cmd_validate

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, quiet=False)

        with patch(
            "macsetup.models.schema.validate_config",
            return_value=["$.version: missing", "$.metadata: invalid"],
        ):
            result = cmd_validate(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "2 error" in captured.out

    def test_validate_schema_errors_json(self, tmp_path, capsys):
        """JSON {valid: false, errors: [...]} for schema violations."""
        from macsetup.cli import cmd_validate

        create_valid_config(tmp_path)
        args = self._make_args(tmp_path, json=True)

        with patch(
            "macsetup.models.schema.validate_config",
            return_value=["$.version: missing"],
        ):
            result = cmd_validate(args)

        assert result == 1
        output = json.loads(capsys.readouterr().out)
        assert output["valid"] is False
        assert len(output["errors"]) == 1


class TestCmdInit:
    """Tests for cmd_init function (US1 - T012)."""

    def test_icloud_flag_routes_to_init_icloud(self, tmp_path):
        """--icloud flag routes to InitService.init_icloud()."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=True,
            local=False,
            status=False,
            force=False,
            json=False,
            quiet=True,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.init_icloud.return_value = {
                "success": True,
                "storage": "icloud",
                "config_dir": str(tmp_path / "icloud"),
                "migrated": False,
                "files_moved": 0,
            }
            result = cmd_init(args)

        assert result == 0
        mock_service.init_icloud.assert_called_once()

    def test_status_flag_routes_to_status(self, tmp_path):
        """--status flag routes to InitService.status()."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=False,
            local=False,
            status=True,
            force=False,
            json=False,
            quiet=False,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.status.return_value = {
                "storage": "local",
                "config_dir": str(tmp_path),
                "pointer_file": "not set",
            }
            result = cmd_init(args)

        assert result == 0
        mock_service.status.assert_called_once()

    def test_json_flag_produces_json_output(self, tmp_path, capsys):
        """--json flag produces JSON output."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=False,
            local=False,
            status=True,
            force=False,
            json=True,
            quiet=False,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.status.return_value = {
                "storage": "local",
                "config_dir": str(tmp_path),
                "pointer_file": "not set",
            }
            cmd_init(args)

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["storage"] == "local"

    def test_quiet_suppresses_output(self, tmp_path, capsys):
        """--quiet suppresses output."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=True,
            local=False,
            status=False,
            force=False,
            json=False,
            quiet=True,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.init_icloud.return_value = {
                "success": True,
                "storage": "icloud",
                "config_dir": str(tmp_path / "icloud"),
                "migrated": False,
                "files_moved": 0,
            }
            cmd_init(args)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_exit_code_1_when_icloud_unavailable(self, tmp_path):
        """Exit code 1 when iCloud Drive is not available."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=True,
            local=False,
            status=False,
            force=False,
            json=False,
            quiet=True,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.init_icloud.return_value = {
                "success": False,
                "error": "icloud_not_available",
                "message": "iCloud Drive is not available",
            }
            result = cmd_init(args)

        assert result == 1

    def test_local_flag_routes_to_init_local(self, tmp_path):
        """--local flag routes to InitService.init_local()."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=False,
            local=True,
            status=False,
            force=False,
            json=False,
            quiet=True,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.init_local.return_value = {
                "success": True,
                "storage": "local",
                "config_dir": str(tmp_path),
                "files_copied": 3,
                "icloud_dir": str(tmp_path / "icloud"),
            }
            result = cmd_init(args)

        assert result == 0
        mock_service.init_local.assert_called_once()

    def test_local_human_output(self, tmp_path, capsys):
        """--local human output matches contract format."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=False,
            local=True,
            status=False,
            force=False,
            json=False,
            quiet=False,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.init_local.return_value = {
                "success": True,
                "storage": "local",
                "config_dir": str(tmp_path),
                "files_copied": 3,
                "icloud_dir": str(tmp_path / "icloud"),
            }
            cmd_init(args)

        captured = capsys.readouterr()
        assert "local storage" in captured.out.lower()

    def test_local_json_output(self, tmp_path, capsys):
        """--local --json output format."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=False,
            local=True,
            status=False,
            force=False,
            json=True,
            quiet=False,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.init_local.return_value = {
                "success": True,
                "storage": "local",
                "config_dir": str(tmp_path),
                "files_copied": 3,
                "icloud_dir": str(tmp_path / "icloud"),
            }
            cmd_init(args)

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["storage"] == "local"
        assert output["success"] is True

    def test_local_exit_code_1_when_no_pointer(self, tmp_path):
        """Exit code 1 when no pointer file exists."""
        from macsetup.cli import cmd_init

        args = argparse.Namespace(
            resolved_config_dir=tmp_path,
            icloud=False,
            local=True,
            status=False,
            force=False,
            json=False,
            quiet=True,
        )

        with patch("macsetup.services.init.InitService") as mock_cls:
            mock_service = mock_cls.return_value
            mock_service.init_local.return_value = {
                "success": False,
                "error": "not_using_icloud",
                "message": "Not currently using iCloud storage (no pointer file)",
            }
            result = cmd_init(args)

        assert result == 1
