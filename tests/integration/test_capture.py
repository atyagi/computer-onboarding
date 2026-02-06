"""Integration tests for capture command.

These tests verify the end-to-end flow of the capture command,
from CLI invocation through service execution.
"""

import json
from unittest.mock import patch

import pytest
import yaml

from macsetup.cli import main


@pytest.fixture
def capture_dir(tmp_path):
    """Create a temporary directory for capture output."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


class TestCaptureCommandIntegration:
    """Integration tests for the capture command."""

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_taps")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_formulas")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_casks")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.list_installed")
    def test_capture_command_creates_config_file(
        self,
        mock_mas_list,
        mock_mas_available,
        mock_brew_casks,
        mock_brew_formulas,
        mock_brew_taps,
        mock_brew_available,
        capture_dir,
        capsys,
    ):
        """Capture command creates a valid config.yaml file."""
        mock_brew_available.return_value = True
        mock_brew_taps.return_value = ["homebrew/cask-fonts"]
        mock_brew_formulas.return_value = ["git", "python"]
        mock_brew_casks.return_value = ["visual-studio-code"]
        mock_mas_available.return_value = True
        mock_mas_list.return_value = [(497799835, "Xcode")]

        exit_code = main(["--config-dir", str(capture_dir), "capture"])

        assert exit_code == 0

        config_path = capture_dir / "config.yaml"
        assert config_path.exists()

        with config_path.open() as f:
            config = yaml.safe_load(f)

        assert config["version"] == "1.0"
        assert "metadata" in config
        assert "profiles" in config
        profile = config["profiles"]["default"]
        assert profile["applications"]["homebrew"]["formulas"] == ["git", "python"]
        assert profile["applications"]["homebrew"]["casks"] == ["visual-studio-code"]
        assert profile["applications"]["homebrew"]["taps"] == ["homebrew/cask-fonts"]
        assert len(profile["applications"]["mas"]) == 1
        assert profile["applications"]["mas"][0]["id"] == 497799835

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_taps")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_formulas")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_casks")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_capture_command_json_output(
        self,
        mock_mas_available,
        mock_brew_casks,
        mock_brew_formulas,
        mock_brew_taps,
        mock_brew_available,
        capture_dir,
        capsys,
    ):
        """Capture command produces valid JSON with --json flag."""
        mock_brew_available.return_value = True
        mock_brew_taps.return_value = []
        mock_brew_formulas.return_value = ["git"]
        mock_brew_casks.return_value = []
        mock_mas_available.return_value = False

        exit_code = main(["--config-dir", str(capture_dir), "--json", "capture"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["success"] is True
        assert "config_path" in output
        assert "config" in output
        assert output["config"]["version"] == "1.0"

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_capture_command_with_custom_profile(
        self,
        mock_mas_available,
        mock_brew_available,
        capture_dir,
        capsys,
    ):
        """Capture command respects --profile flag."""
        mock_brew_available.return_value = False
        mock_mas_available.return_value = False

        exit_code = main(["--config-dir", str(capture_dir), "capture", "--profile", "work"])

        assert exit_code == 0

        config_path = capture_dir / "config.yaml"
        with config_path.open() as f:
            config = yaml.safe_load(f)

        assert "work" in config["profiles"]

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_taps")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_formulas")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.list_casks")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_capture_command_skip_apps(
        self,
        mock_mas_available,
        mock_brew_casks,
        mock_brew_formulas,
        mock_brew_taps,
        mock_brew_available,
        capture_dir,
        capsys,
    ):
        """Capture command respects --skip-apps flag."""
        mock_brew_available.return_value = True
        mock_brew_taps.return_value = ["homebrew/cask-fonts"]
        mock_brew_formulas.return_value = ["git"]
        mock_brew_casks.return_value = ["docker"]
        mock_mas_available.return_value = False

        exit_code = main(["--config-dir", str(capture_dir), "capture", "--skip-apps"])

        assert exit_code == 0

        # Homebrew list methods should not have been called
        mock_brew_taps.assert_not_called()
        mock_brew_formulas.assert_not_called()
        mock_brew_casks.assert_not_called()

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_capture_command_quiet_mode(
        self,
        mock_mas_available,
        mock_brew_available,
        capture_dir,
        capsys,
    ):
        """Capture command respects --quiet flag."""
        mock_brew_available.return_value = False
        mock_mas_available.return_value = False

        exit_code = main(["--config-dir", str(capture_dir), "--quiet", "capture"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_capture_command_populates_metadata(
        self,
        mock_mas_available,
        mock_brew_available,
        capture_dir,
    ):
        """Capture command populates metadata in the config file."""
        mock_brew_available.return_value = False
        mock_mas_available.return_value = False

        exit_code = main(["--config-dir", str(capture_dir), "capture"])

        assert exit_code == 0

        config_path = capture_dir / "config.yaml"
        with config_path.open() as f:
            config = yaml.safe_load(f)

        metadata = config["metadata"]
        assert "captured_at" in metadata
        assert "source_machine" in metadata
        assert "macos_version" in metadata
        assert metadata["tool_version"] == "1.0.0"
