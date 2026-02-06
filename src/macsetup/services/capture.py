"""Capture service for macsetup."""

import platform
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from macsetup import __version__
from macsetup.adapters.defaults import DefaultsAdapter
from macsetup.adapters.dotfiles import DotfilesAdapter
from macsetup.adapters.homebrew import HomebrewAdapter
from macsetup.adapters.mas import MasAdapter
from macsetup.models.config import (
    Applications,
    Configuration,
    Dotfile,
    HomebrewApps,
    MacApp,
    Metadata,
    Preference,
    Profile,
)


class CaptureService:
    """Service for capturing current machine configuration."""

    def __init__(
        self,
        config_dir: Path,
        profile: str = "default",
        dotfiles: list[str] | None = None,
        preference_domains: list[str] | None = None,
        skip_apps: bool = False,
        skip_dotfiles: bool = False,
        skip_preferences: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ):
        self.config_dir = config_dir
        self.profile_name = profile
        self.dotfile_paths = dotfiles or []
        self.preference_domains = preference_domains or []
        self.skip_apps = skip_apps
        self.skip_dotfiles = skip_dotfiles
        self.skip_preferences = skip_preferences
        self.progress_callback = progress_callback

        self.homebrew = HomebrewAdapter()
        self.mas = MasAdapter()
        self.defaults = DefaultsAdapter()
        self.dotfiles_adapter = DotfilesAdapter()

    def _report_progress(self, message: str, current: int, total: int):
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(message, current, total)

    def _capture_homebrew(self) -> HomebrewApps | None:
        """Capture Homebrew packages."""
        if not self.homebrew.is_available():
            return None

        self._report_progress("Capturing Homebrew packages", 1, 3)
        taps = self.homebrew.list_taps()
        formulas = self.homebrew.list_formulas()
        casks = self.homebrew.list_casks()

        if not taps and not formulas and not casks:
            return None

        return HomebrewApps(taps=taps, formulas=formulas, casks=casks)

    def _capture_mas(self) -> list[MacApp]:
        """Capture Mac App Store apps."""
        if not self.mas.is_available():
            return []

        self._report_progress("Capturing Mac App Store apps", 2, 3)
        installed = self.mas.list_installed()
        return [MacApp(id=app_id, name=name) for app_id, name in installed]

    def _capture_dotfiles(self) -> list[Dotfile]:
        """Capture specified dotfiles."""
        if self.skip_dotfiles or not self.dotfile_paths:
            return []

        captured = []
        home = Path.home()

        for i, dotfile_path in enumerate(self.dotfile_paths):
            self._report_progress(f"Capturing {dotfile_path}", i + 1, len(self.dotfile_paths))
            source = home / dotfile_path
            if not source.exists():
                continue

            result = self.dotfiles_adapter.copy_to_config(source, self.config_dir, dotfile_path)
            if result.success:
                captured.append(Dotfile(path=dotfile_path))

        return captured

    def _capture_preferences(self) -> list[Preference]:
        """Capture specified preference domains."""
        if self.skip_preferences or not self.preference_domains:
            return []

        captured = []

        for i, domain in enumerate(self.preference_domains):
            self._report_progress(f"Capturing {domain}", i + 1, len(self.preference_domains))
            value = self.defaults.read(domain)
            if value is not None:
                captured.append(Preference(domain=domain))

        return captured

    def _build_metadata(self) -> Metadata:
        """Build metadata for the capture."""
        mac_ver = platform.mac_ver()
        return Metadata(
            captured_at=datetime.now(UTC),
            source_machine=platform.node(),
            macos_version=mac_ver[0] or "unknown",
            tool_version=__version__,
        )

    def capture(self) -> Configuration:
        """Capture the current machine configuration.

        Returns:
            A Configuration object representing the current state.
        """
        # Capture applications
        homebrew = None
        mas_apps: list[MacApp] = []

        if not self.skip_apps:
            homebrew = self._capture_homebrew()
            mas_apps = self._capture_mas()

        applications = Applications(
            homebrew=homebrew,
            mas=mas_apps,
        )

        # Capture dotfiles
        dotfiles = self._capture_dotfiles()

        # Capture preferences
        preferences = self._capture_preferences()

        # Build profile
        profile = Profile(
            name=self.profile_name,
            applications=applications,
            dotfiles=dotfiles,
            preferences=preferences,
        )

        # Build configuration
        metadata = self._build_metadata()

        return Configuration(
            version="1.0",
            metadata=metadata,
            profiles={self.profile_name: profile},
        )
