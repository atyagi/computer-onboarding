"""Unit tests for sync service."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory."""
    d = tmp_path / "config"
    d.mkdir()
    return d


class TestSyncService:
    """Tests for sync service (T062)."""

    def test_sync_service_can_be_created(self, config_dir):
        """Sync service can be instantiated."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)
        assert service is not None

    def test_sync_runs_capture(self, config_dir):
        """Sync service runs capture when triggered."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)

        with patch("macsetup.services.sync.CaptureService") as mock_capture_cls:
            mock_capture = MagicMock()
            mock_capture_cls.return_value = mock_capture
            mock_config = MagicMock()
            mock_capture.capture.return_value = mock_config

            with patch("macsetup.services.sync.save_config"):
                result = service.sync_now()

            assert result is True
            mock_capture.capture.assert_called_once()

    def test_sync_saves_config_after_capture(self, config_dir):
        """Sync service saves config after capture."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)

        with patch("macsetup.services.sync.CaptureService") as mock_capture_cls:
            mock_capture = MagicMock()
            mock_capture_cls.return_value = mock_capture
            mock_config = MagicMock()
            mock_capture.capture.return_value = mock_config

            with patch("macsetup.services.sync.save_config") as mock_save:
                service.sync_now()

            mock_save.assert_called_once_with(mock_config, config_dir / "config.yaml")

    def test_sync_returns_false_on_error(self, config_dir):
        """Sync service returns False when capture fails."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)

        with patch("macsetup.services.sync.CaptureService") as mock_capture_cls:
            mock_capture = MagicMock()
            mock_capture_cls.return_value = mock_capture
            mock_capture.capture.side_effect = Exception("capture failed")

            result = service.sync_now()

        assert result is False

    def test_sync_status_not_running_initially(self, config_dir):
        """Sync service reports not running initially."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)
        status = service.status()
        assert status["running"] is False

    def test_sync_interval_stored(self, config_dir):
        """Sync service stores the configured interval."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir, interval_minutes=30)
        assert service.interval_minutes == 30


class TestFileWatcher:
    """Tests for file watcher (T063)."""

    def test_watcher_detects_file_change(self, config_dir, tmp_path):
        """File watcher detects changes to tracked files."""
        from macsetup.services.sync import FileWatcher

        watched_file = tmp_path / ".zshrc"
        watched_file.write_text("original content")

        watcher = FileWatcher(paths=[str(watched_file)])
        assert watcher.has_changes() is False

        # Modify the file
        watched_file.write_text("modified content")
        assert watcher.has_changes() is True

    def test_watcher_tracks_multiple_files(self, tmp_path):
        """File watcher tracks multiple files."""
        from macsetup.services.sync import FileWatcher

        file1 = tmp_path / ".zshrc"
        file2 = tmp_path / ".gitconfig"
        file1.write_text("content1")
        file2.write_text("content2")

        watcher = FileWatcher(paths=[str(file1), str(file2)])
        assert watcher.has_changes() is False

    def test_watcher_ignores_nonexistent_files(self, tmp_path):
        """File watcher handles nonexistent files gracefully."""
        from macsetup.services.sync import FileWatcher

        watcher = FileWatcher(paths=[str(tmp_path / "nonexistent")])
        assert watcher.has_changes() is False

    def test_watcher_reset_clears_changes(self, tmp_path):
        """File watcher reset clears change detection state."""
        from macsetup.services.sync import FileWatcher

        watched_file = tmp_path / ".zshrc"
        watched_file.write_text("original")

        watcher = FileWatcher(paths=[str(watched_file)])
        watched_file.write_text("modified")
        assert watcher.has_changes() is True

        watcher.reset()
        assert watcher.has_changes() is False


class TestSyncDaemon:
    """Tests for sync daemon (T064 - basic unit tests)."""

    def test_pid_file_created_on_start(self, config_dir):
        """PID file is created when daemon conceptually starts."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)
        service.write_pid_file()

        pid_path = config_dir / ".sync.pid"
        assert pid_path.exists()

    def test_pid_file_removed_on_stop(self, config_dir):
        """PID file is removed when daemon stops."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)
        service.write_pid_file()
        service.remove_pid_file()

        pid_path = config_dir / ".sync.pid"
        assert not pid_path.exists()

    def test_is_running_checks_pid_file(self, config_dir):
        """is_running checks for PID file existence."""
        from macsetup.services.sync import SyncService

        service = SyncService(config_dir=config_dir)
        assert service.is_running() is False

        service.write_pid_file()
        assert service.is_running() is True

        service.remove_pid_file()
        assert service.is_running() is False
