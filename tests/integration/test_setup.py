"""Integration tests for setup command.

These tests verify the end-to-end flow of the setup command,
from CLI invocation through service execution.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from macsetup.cli import main
from macsetup.models.config import (
    Applications,
    Configuration,
    Dotfile,
    HomebrewApps,
    MacApp,
    ManualApp,
    Metadata,
    Preference,
    Profile,
    config_to_dict,
)


@pytest.fixture
def test_config_dir(tmp_path):
    """Create a temporary config directory with a valid config file."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create a sample configuration
    config = Configuration(
        version="1.0",
        metadata=Metadata(
            captured_at=datetime.now(UTC),
            source_machine="test-machine",
            macos_version="14.2",
            tool_version="1.0.0",
        ),
        profiles={
            "default": Profile(
                name="default",
                applications=Applications(
                    homebrew=HomebrewApps(
                        taps=["homebrew/cask-fonts"],
                        formulas=["git", "python@3.14"],
                        casks=["visual-studio-code", "iterm2"],
                    ),
                    mas=[
                        MacApp(id=497799835, name="Xcode"),
                        MacApp(id=1295203466, name="Microsoft Remote Desktop"),
                    ],
                    manual=[ManualApp(name="Adobe Creative Cloud", url="https://adobe.com")],
                ),
                dotfiles=[
                    Dotfile(path=".zshrc"),
                    Dotfile(path=".gitconfig"),
                ],
                preferences=[
                    Preference(domain="com.apple.dock", key="autohide", value=True, type="bool"),
                    Preference(domain="NSGlobalDomain", key="AppleShowAllExtensions", value=True, type="bool"),
                ],
            ),
            "minimal": Profile(
                name="minimal",
                applications=Applications(
                    homebrew=HomebrewApps(formulas=["git"]),
                ),
            ),
        },
    )

    # Write config to YAML file
    config_path = config_dir / "config.yaml"
    with config_path.open("w") as f:
        yaml.dump(config_to_dict(config), f)

    # Create dotfiles directory
    dotfiles_dir = config_dir / "dotfiles"
    dotfiles_dir.mkdir()

    # Create sample dotfiles
    (dotfiles_dir / ".zshrc").write_text("# Sample zshrc\nexport PATH=$HOME/bin:$PATH\n")
    (dotfiles_dir / ".gitconfig").write_text("[user]\n  name = Test User\n  email = test@example.com\n")

    return config_dir


class TestSetupCommandIntegration:
    """Integration tests for the setup command."""

    def test_setup_command_missing_config_file(self, tmp_path, capsys):
        """Setup command fails gracefully when config file doesn't exist."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        exit_code = main(["--config-dir", str(empty_dir), "setup"])

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "Configuration file not found" in captured.out

    def test_setup_command_invalid_profile(self, test_config_dir, capsys):
        """Setup command fails gracefully when profile doesn't exist."""
        exit_code = main(["--config-dir", str(test_config_dir), "setup", "--profile", "nonexistent"])

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "Profile 'nonexistent' not found" in captured.out
        assert "default, minimal" in captured.out

    def test_setup_command_dry_run(self, test_config_dir, capsys):
        """Setup command dry-run mode doesn't make changes."""
        exit_code = main(["--config-dir", str(test_config_dir), "setup", "--dry-run"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Dry-run" in captured.out
        assert "default" in captured.out

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_tap_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_formula_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_cask_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_tap")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_formula")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_cask")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.is_signed_in")
    @patch("macsetup.adapters.mas.MasAdapter.is_installed")
    @patch("macsetup.adapters.mas.MasAdapter.install")
    @patch("macsetup.adapters.dotfiles.DotfilesAdapter.symlink")
    @patch("macsetup.adapters.defaults.DefaultsAdapter.write")
    def test_setup_command_successful_execution(
        self,
        mock_defaults_write,
        mock_dotfiles_symlink,
        mock_mas_install,
        mock_mas_is_installed,
        mock_mas_is_signed_in,
        mock_mas_is_available,
        mock_brew_install_cask,
        mock_brew_install_formula,
        mock_brew_install_tap,
        mock_brew_is_cask_installed,
        mock_brew_is_formula_installed,
        mock_brew_is_tap_installed,
        mock_brew_is_available,
        test_config_dir,
        capsys,
    ):
        """Setup command executes successfully with mocked adapters."""
        from macsetup.adapters import AdapterResult

        # Mock all adapter methods to return success
        mock_brew_is_available.return_value = True
        mock_brew_is_tap_installed.return_value = False
        mock_brew_is_formula_installed.return_value = False
        mock_brew_is_cask_installed.return_value = False
        mock_brew_install_tap.return_value = AdapterResult(success=True)
        mock_brew_install_formula.return_value = AdapterResult(success=True)
        mock_brew_install_cask.return_value = AdapterResult(success=True)

        mock_mas_is_available.return_value = True
        mock_mas_is_signed_in.return_value = True
        mock_mas_is_installed.return_value = False
        mock_mas_install.return_value = AdapterResult(success=True)

        mock_dotfiles_symlink.return_value = AdapterResult(success=True)
        mock_defaults_write.return_value = AdapterResult(success=True)

        # Run setup command
        exit_code = main(["--config-dir", str(test_config_dir), "setup"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Setup complete!" in captured.out

        # Verify adapter methods were called
        assert mock_brew_install_tap.called
        assert mock_brew_install_formula.called
        assert mock_brew_install_cask.called
        assert mock_mas_install.called
        assert mock_dotfiles_symlink.called
        assert mock_defaults_write.called

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_tap_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_formula_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_cask_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_tap")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_formula")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    @patch("macsetup.adapters.dotfiles.DotfilesAdapter.symlink")
    @patch("macsetup.adapters.defaults.DefaultsAdapter.write")
    def test_setup_command_with_failures(
        self,
        mock_defaults_write,
        mock_dotfiles_symlink,
        mock_mas_is_available,
        mock_brew_install_formula,
        mock_brew_install_tap,
        mock_brew_is_cask_installed,
        mock_brew_is_formula_installed,
        mock_brew_is_tap_installed,
        mock_brew_is_available,
        test_config_dir,
        capsys,
    ):
        """Setup command handles failures gracefully."""
        from macsetup.adapters import AdapterResult

        # Mock some failures
        mock_brew_is_available.return_value = True
        mock_brew_is_tap_installed.return_value = False
        mock_brew_is_formula_installed.return_value = False
        mock_brew_is_cask_installed.return_value = False
        mock_brew_install_tap.return_value = AdapterResult(success=True)
        mock_brew_install_formula.return_value = AdapterResult(
            success=False, error="Network error: could not download formula"
        )

        mock_mas_is_available.return_value = False  # MAS not available
        mock_dotfiles_symlink.return_value = AdapterResult(success=True)
        mock_defaults_write.return_value = AdapterResult(success=True)

        # Run setup command
        exit_code = main(["--config-dir", str(test_config_dir), "setup"])

        # Should return exit code 3 for failures
        assert exit_code == 3
        captured = capsys.readouterr()
        assert "failure" in captured.out.lower()

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_tap_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_formula_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_cask_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_tap")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_formula")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_cask")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.is_signed_in")
    @patch("macsetup.adapters.mas.MasAdapter.is_installed")
    @patch("macsetup.adapters.mas.MasAdapter.install")
    @patch("macsetup.adapters.dotfiles.DotfilesAdapter.symlink")
    @patch("macsetup.adapters.defaults.DefaultsAdapter.write")
    def test_setup_command_json_output(
        self,
        mock_defaults_write,
        mock_dotfiles_symlink,
        mock_mas_install,
        mock_mas_is_installed,
        mock_mas_is_signed_in,
        mock_mas_is_available,
        mock_brew_install_cask,
        mock_brew_install_formula,
        mock_brew_install_tap,
        mock_brew_is_cask_installed,
        mock_brew_is_formula_installed,
        mock_brew_is_tap_installed,
        mock_brew_is_available,
        test_config_dir,
        capsys,
    ):
        """Setup command produces valid JSON output with --json flag."""
        from macsetup.adapters import AdapterResult

        # Mock all adapter methods to return success
        mock_brew_is_available.return_value = True
        mock_brew_is_tap_installed.return_value = False
        mock_brew_is_formula_installed.return_value = False
        mock_brew_is_cask_installed.return_value = False
        mock_brew_install_tap.return_value = AdapterResult(success=True)
        mock_brew_install_formula.return_value = AdapterResult(success=True)
        mock_brew_install_cask.return_value = AdapterResult(success=True)

        mock_mas_is_available.return_value = True
        mock_mas_is_signed_in.return_value = True
        mock_mas_is_installed.return_value = False
        mock_mas_install.return_value = AdapterResult(success=True)

        mock_dotfiles_symlink.return_value = AdapterResult(success=True)
        mock_defaults_write.return_value = AdapterResult(success=True)

        # Run setup command with --json
        exit_code = main(["--config-dir", str(test_config_dir), "--json", "setup"])

        assert exit_code == 0
        captured = capsys.readouterr()

        # Parse JSON output
        output = json.loads(captured.out)
        assert output["success"] is True
        assert output["completed"] > 0
        assert output["failed"] == 0
        assert isinstance(output["failures"], list)
        assert isinstance(output["manual_required"], list)

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_tap_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_formula_installed")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_setup_command_skip_dotfiles_flag(
        self,
        mock_mas_is_available,
        mock_brew_is_formula_installed,
        mock_brew_is_tap_installed,
        mock_brew_is_available,
        test_config_dir,
        capsys,
    ):
        """Setup command respects --no-dotfiles flag."""
        from macsetup.adapters import AdapterResult

        mock_brew_is_available.return_value = True
        mock_brew_is_tap_installed.return_value = True
        mock_brew_is_formula_installed.return_value = True
        mock_mas_is_available.return_value = False

        with patch("macsetup.adapters.dotfiles.DotfilesAdapter.symlink") as mock_symlink:
            mock_symlink.return_value = AdapterResult(success=True)

            exit_code = main(["--config-dir", str(test_config_dir), "setup", "--no-dotfiles"])

            assert exit_code == 0
            # Dotfiles symlink should not be called when --no-dotfiles is used
            assert not mock_symlink.called

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_tap_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_formula_installed")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_setup_command_skip_preferences_flag(
        self,
        mock_mas_is_available,
        mock_brew_is_formula_installed,
        mock_brew_is_tap_installed,
        mock_brew_is_available,
        test_config_dir,
        capsys,
    ):
        """Setup command respects --no-preferences flag."""
        from macsetup.adapters import AdapterResult

        mock_brew_is_available.return_value = True
        mock_brew_is_tap_installed.return_value = True
        mock_brew_is_formula_installed.return_value = True
        mock_mas_is_available.return_value = False

        with patch("macsetup.adapters.defaults.DefaultsAdapter.write") as mock_write:
            mock_write.return_value = AdapterResult(success=True)

            exit_code = main(["--config-dir", str(test_config_dir), "setup", "--no-preferences"])

            assert exit_code == 0
            # Defaults write should not be called when --no-preferences is used
            assert not mock_write.called

    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_tap_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_formula_installed")
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.install_formula")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_setup_command_minimal_profile(
        self,
        mock_mas_is_available,
        mock_brew_install_formula,
        mock_brew_is_formula_installed,
        mock_brew_is_tap_installed,
        mock_brew_is_available,
        test_config_dir,
        capsys,
    ):
        """Setup command works with minimal profile."""
        from macsetup.adapters import AdapterResult

        mock_brew_is_available.return_value = True
        mock_brew_is_tap_installed.return_value = True
        mock_brew_is_formula_installed.return_value = False
        mock_brew_install_formula.return_value = AdapterResult(success=True)
        mock_mas_is_available.return_value = False

        exit_code = main(["--config-dir", str(test_config_dir), "setup", "--profile", "minimal"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Setup complete!" in captured.out
        # Should only install git
        assert mock_brew_install_formula.call_count == 1
