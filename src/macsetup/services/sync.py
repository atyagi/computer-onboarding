"""Sync service for macsetup."""

import contextlib
import os
import signal
from pathlib import Path

from macsetup.models.config import save_config
from macsetup.services.capture import CaptureService


class FileWatcher:
    """Watches files for changes using modification time."""

    def __init__(self, paths: list[str] | None = None):
        self._paths = paths or []
        self._mtimes: dict[str, float] = {}
        self.reset()

    def reset(self):
        """Record current modification times as baseline."""
        self._mtimes = {}
        for path in self._paths:
            with contextlib.suppress(OSError):
                self._mtimes[path] = os.path.getmtime(path)

    def has_changes(self) -> bool:
        """Check if any tracked file has been modified since last reset."""
        for path in self._paths:
            try:
                current_mtime = os.path.getmtime(path)
                if path in self._mtimes:
                    if current_mtime != self._mtimes[path]:
                        return True
                else:
                    # File appeared since last reset
                    return True
            except OSError:
                # File disappeared
                if path in self._mtimes:
                    return True
        return False


class SyncService:
    """Service for syncing machine configuration periodically."""

    def __init__(
        self,
        config_dir: Path,
        interval_minutes: int = 60,
        watch: bool = True,
        dotfiles: list[str] | None = None,
        preference_domains: list[str] | None = None,
    ):
        self.config_dir = config_dir
        self.interval_minutes = interval_minutes
        self.watch = watch
        self.dotfiles = dotfiles or []
        self.preference_domains = preference_domains or []
        self._interrupted = False

    def sync_now(self) -> bool:
        """Run a single sync (capture + save).

        Returns:
            True if sync succeeded, False otherwise.
        """
        try:
            capture = CaptureService(
                config_dir=self.config_dir,
                dotfiles=self.dotfiles,
                preference_domains=self.preference_domains,
            )
            config = capture.capture()
            save_config(config, self.config_dir / "config.yaml")
            return True
        except Exception:
            return False

    def write_pid_file(self):
        """Write the current PID to the pid file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        pid_path = self.config_dir / ".sync.pid"
        pid_path.write_text(str(os.getpid()))

    def remove_pid_file(self):
        """Remove the PID file."""
        pid_path = self.config_dir / ".sync.pid"
        if pid_path.exists():
            pid_path.unlink()

    def is_running(self) -> bool:
        """Check if the sync daemon is running."""
        pid_path = self.config_dir / ".sync.pid"
        if not pid_path.exists():
            return False
        try:
            pid = int(pid_path.read_text().strip())
            # Check if process is alive
            os.kill(pid, 0)
            return True
        except (ValueError, OSError):
            # PID file is stale
            return False

    def status(self) -> dict:
        """Get the current sync status.

        Returns:
            Dict with running status and configuration.
        """
        return {
            "running": self.is_running(),
            "interval_minutes": self.interval_minutes,
            "config_dir": str(self.config_dir),
        }

    def stop(self) -> bool:
        """Stop a running sync daemon.

        Returns:
            True if daemon was stopped, False if not running.
        """
        pid_path = self.config_dir / ".sync.pid"
        if not pid_path.exists():
            return False
        try:
            pid = int(pid_path.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            self.remove_pid_file()
            return True
        except (ValueError, OSError):
            self.remove_pid_file()
            return False
