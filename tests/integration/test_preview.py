"""Integration tests for preview command."""

import json
from datetime import UTC, datetime

import pytest
import yaml

from macsetup.cli import main
from macsetup.models.config import (
    Applications,
    Configuration,
    Dotfile,
    HomebrewApps,
    MacApp,
    Metadata,
    Preference,
    Profile,
    config_to_dict,
)


@pytest.fixture
def preview_config_dir(tmp_path):
    """Create a config directory with a test config."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

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
                        formulas=["git", "python"],
                        casks=["visual-studio-code"],
                    ),
                    mas=[MacApp(id=497799835, name="Xcode")],
                ),
                dotfiles=[Dotfile(path=".zshrc")],
                preferences=[
                    Preference(domain="com.apple.dock", key="autohide", value=True, type="bool")
                ],
            ),
            "work": Profile(
                name="work",
                extends="default",
                description="Work profile",
                applications=Applications(
                    homebrew=HomebrewApps(
                        formulas=["git", "python", "node"],
                        casks=["slack"],
                    ),
                ),
            ),
        },
    )

    config_path = config_dir / "config.yaml"
    with config_path.open("w") as f:
        yaml.dump(config_to_dict(config), f)

    return config_dir


class TestPreviewCommandIntegration:
    """Integration tests for the preview command."""

    def test_preview_command_lists_items(self, preview_config_dir, capsys):
        """Preview command lists items to be installed."""
        exit_code = main(["--config-dir", str(preview_config_dir), "preview"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "git" in captured.out
        assert "python" in captured.out
        assert "visual-studio-code" in captured.out

    def test_preview_command_json_output(self, preview_config_dir, capsys):
        """Preview command produces valid JSON."""
        exit_code = main(["--config-dir", str(preview_config_dir), "--json", "preview"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True
        assert "preview" in output
        assert "git" in output["preview"]["formulas"]

    def test_preview_command_missing_config(self, tmp_path, capsys):
        """Preview command fails gracefully when config missing."""
        empty = tmp_path / "empty"
        empty.mkdir()

        exit_code = main(["--config-dir", str(empty), "preview"])

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_preview_command_invalid_profile(self, preview_config_dir, capsys):
        """Preview command fails for invalid profile."""
        exit_code = main(
            ["--config-dir", str(preview_config_dir), "preview", "--profile", "nonexistent"]
        )

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestProfileCommandIntegration:
    """Integration tests for the profile command."""

    def test_profile_list(self, preview_config_dir, capsys):
        """Profile list shows all profiles."""
        exit_code = main(["--config-dir", str(preview_config_dir), "profile", "list"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "default" in captured.out
        assert "work" in captured.out

    def test_profile_list_json(self, preview_config_dir, capsys):
        """Profile list produces valid JSON."""
        exit_code = main(["--config-dir", str(preview_config_dir), "--json", "profile", "list"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "default" in output["profiles"]
        assert "work" in output["profiles"]

    def test_profile_show(self, preview_config_dir, capsys):
        """Profile show displays profile details."""
        exit_code = main(["--config-dir", str(preview_config_dir), "profile", "show", "default"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "default" in captured.out

    def test_profile_diff(self, preview_config_dir, capsys):
        """Profile diff compares two profiles."""
        exit_code = main(
            ["--config-dir", str(preview_config_dir), "profile", "diff", "default", "work"]
        )

        assert exit_code == 0
