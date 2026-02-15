"""Integration tests for sync command."""

import json
from unittest.mock import patch

import pytest

from macsetup.adapters.dotfiles import DiscoveryResult
from macsetup.cli import main


@pytest.fixture
def sync_dir(tmp_path):
    """Create a temporary directory for sync."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


class TestSyncCommandIntegration:
    """Integration tests for the sync command."""

    def test_sync_status_when_not_running(self, sync_dir, capsys):
        """Sync status reports not running."""
        exit_code = main(["--config-dir", str(sync_dir), "sync", "status"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "not running" in captured.out

    def test_sync_status_json(self, sync_dir, capsys):
        """Sync status produces valid JSON."""
        exit_code = main(["--config-dir", str(sync_dir), "--json", "sync", "status"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["running"] is False

    def test_sync_stop_when_not_running(self, sync_dir, capsys):
        """Sync stop gracefully handles not-running state."""
        exit_code = main(["--config-dir", str(sync_dir), "sync", "stop"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "not running" in captured.out

    @patch("macsetup.adapters.dotfiles.DotfilesAdapter.copy_to_config")
    @patch(
        "macsetup.adapters.dotfiles.DotfilesAdapter.discover_dotfiles",
        return_value=DiscoveryResult(),
    )
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_sync_now_runs_capture(
        self,
        mock_mas_available,
        mock_brew_available,
        _mock_discover,
        _mock_copy,
        sync_dir,
        capsys,
    ):
        """Sync now runs capture and saves config."""
        mock_brew_available.return_value = False
        mock_mas_available.return_value = False

        exit_code = main(["--config-dir", str(sync_dir), "sync", "now"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Sync complete" in captured.out

        # Verify config file was created
        config_path = sync_dir / "config.yaml"
        assert config_path.exists()

    @patch("macsetup.adapters.dotfiles.DotfilesAdapter.copy_to_config")
    @patch(
        "macsetup.adapters.dotfiles.DotfilesAdapter.discover_dotfiles",
        return_value=DiscoveryResult(),
    )
    @patch("macsetup.adapters.homebrew.HomebrewAdapter.is_available")
    @patch("macsetup.adapters.mas.MasAdapter.is_available")
    def test_sync_now_json_output(
        self,
        mock_mas_available,
        mock_brew_available,
        _mock_discover,
        _mock_copy,
        sync_dir,
        capsys,
    ):
        """Sync now produces valid JSON output."""
        mock_brew_available.return_value = False
        mock_mas_available.return_value = False

        exit_code = main(["--config-dir", str(sync_dir), "--json", "sync", "now"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True

    def test_sync_no_subcommand_shows_usage(self, sync_dir, capsys):
        """Sync without subcommand shows usage."""
        exit_code = main(["--config-dir", str(sync_dir), "sync"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Usage" in captured.out or "sync" in captured.out
