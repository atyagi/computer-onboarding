"""Setup service for macsetup."""

import json
import signal
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from macsetup.adapters.defaults import DefaultsAdapter
from macsetup.adapters.dotfiles import DotfilesAdapter
from macsetup.adapters.homebrew import HomebrewAdapter
from macsetup.adapters.mas import MasAdapter
from macsetup.models.config import (
    Configuration,
    FailedItem,
    ManualApp,
    Profile,
    SetupState,
)


@dataclass
class SetupResult:
    """Result of a setup operation."""

    success: bool
    completed_count: int = 0
    failed_count: int = 0
    completed_items: list[str] = field(default_factory=list)
    failed_items: list[FailedItem] = field(default_factory=list)
    manual_apps: list[ManualApp] = field(default_factory=list)
    interrupted: bool = False


class SetupService:
    """Service for setting up a machine from configuration."""

    def __init__(
        self,
        config: Configuration,
        config_dir: Path,
        profile: str = "default",
        force: bool = False,
        skip_dotfiles: bool = False,
        skip_preferences: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ):
        """Initialize the setup service.

        Args:
            config: The configuration to apply.
            config_dir: The configuration directory.
            profile: The profile to use.
            force: If True, reinstall already-installed items.
            skip_dotfiles: If True, skip dotfile setup.
            skip_preferences: If True, skip preference setup.
            progress_callback: Optional callback for progress updates.
        """
        self.config = config
        self.config_dir = config_dir
        self.profile_name = profile
        self.force = force
        self.skip_dotfiles = skip_dotfiles
        self.skip_preferences = skip_preferences
        self.progress_callback = progress_callback

        # Initialize adapters
        self.homebrew = HomebrewAdapter()
        self.mas = MasAdapter()
        self.defaults = DefaultsAdapter()
        self.dotfiles = DotfilesAdapter()

        # State tracking
        self._state: SetupState | None = None
        self._interrupted = False

        # Setup signal handling
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful interruption."""

        def handle_sigint(signum, frame):
            self._interrupted = True
            print("\nInterrupted. Saving state...")

        signal.signal(signal.SIGINT, handle_sigint)
        signal.signal(signal.SIGTERM, handle_sigint)

    def _get_profile(self) -> Profile:
        """Get the active profile."""
        if self.profile_name not in self.config.profiles:
            raise ValueError(f"Profile '{self.profile_name}' not found")
        return self.config.profiles[self.profile_name]

    def _load_state(self) -> SetupState | None:
        """Load existing setup state for resume."""
        state_path = self.config_dir / ".state.json"
        if not state_path.exists():
            return None
        try:
            with open(state_path) as f:
                data = json.load(f)
            return SetupState(
                started_at=datetime.fromisoformat(data["started_at"]),
                profile=data["profile"],
                completed_items=data.get("completed_items", []),
                failed_items=[
                    FailedItem(
                        type=item["type"],
                        identifier=item["identifier"],
                        error=item["error"],
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                    )
                    for item in data.get("failed_items", [])
                ],
                status=data.get("status", "in_progress"),
            )
        except Exception:
            return None

    def _save_state(self, state: SetupState):
        """Save setup state for resume."""
        state_path = self.config_dir / ".state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(
                {
                    "started_at": state.started_at.isoformat(),
                    "profile": state.profile,
                    "completed_items": state.completed_items,
                    "failed_items": [
                        {
                            "type": item.type,
                            "identifier": item.identifier,
                            "error": item.error,
                            "timestamp": item.timestamp.isoformat(),
                        }
                        for item in state.failed_items
                    ],
                    "status": state.status,
                },
                f,
                indent=2,
            )

    def _clear_state(self):
        """Clear setup state on successful completion."""
        state_path = self.config_dir / ".state.json"
        if state_path.exists():
            state_path.unlink()

    def _is_completed(self, item_id: str) -> bool:
        """Check if an item was already completed in a previous run."""
        if self._state is None:
            return False
        return item_id in self._state.completed_items

    def _mark_completed(self, item_id: str):
        """Mark an item as completed."""
        if self._state is not None:
            self._state.completed_items.append(item_id)

    def _mark_failed(self, item_type: str, identifier: str, error: str):
        """Mark an item as failed."""
        if self._state is not None:
            self._state.failed_items.append(
                FailedItem(
                    type=item_type,
                    identifier=identifier,
                    error=error,
                    timestamp=datetime.now(UTC),
                )
            )

    def _report_progress(self, message: str, current: int, total: int):
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(message, current, total)

    def run(self, resume: bool = False) -> SetupResult:
        """Run the setup process.

        Args:
            resume: If True, resume from a previous incomplete run.

        Returns:
            SetupResult with the outcome.
        """
        profile = self._get_profile()

        # Initialize or load state
        if resume:
            self._state = self._load_state()
        if self._state is None:
            self._state = SetupState(
                started_at=datetime.now(UTC),
                profile=self.profile_name,
            )

        result = SetupResult(success=True, manual_apps=[])

        try:
            # Install Homebrew packages
            if self.homebrew.is_available() and profile.applications:
                self._install_homebrew(profile, result)

            # Install Mac App Store apps
            if self.mas.is_available() and profile.applications:
                self._install_mas_apps(profile, result)

            # Setup dotfiles
            if not self.skip_dotfiles and profile.dotfiles:
                self._setup_dotfiles(profile, result)

            # Apply preferences
            if not self.skip_preferences and profile.preferences:
                self._apply_preferences(profile, result)

            # Collect manual apps
            if profile.applications and profile.applications.manual:
                result.manual_apps = list(profile.applications.manual)

            # Check if interrupted
            if self._interrupted:
                result.success = False
                result.interrupted = True
                self._state.status = "in_progress"
                self._save_state(self._state)
            else:
                # Mark as complete
                if result.failed_count == 0:
                    self._state.status = "completed"
                    self._clear_state()
                else:
                    self._state.status = "completed_with_errors"
                    self._save_state(self._state)

            result.completed_items = list(self._state.completed_items)
            result.failed_items = list(self._state.failed_items)

        except Exception as e:
            result.success = False
            self._mark_failed("setup", "general", str(e))
            result.failed_items = list(self._state.failed_items)
            self._save_state(self._state)

        return result

    def _install_homebrew(self, profile: Profile, result: SetupResult):
        """Install Homebrew packages."""
        if profile.applications is None or profile.applications.homebrew is None:
            return

        homebrew = profile.applications.homebrew

        # Install taps
        for i, tap in enumerate(homebrew.taps):
            if self._interrupted:
                return
            item_id = f"tap:{tap}"
            if not self.force and (
                self._is_completed(item_id) or self.homebrew.is_tap_installed(tap)
            ):
                continue
            self._report_progress(f"Tapping {tap}", i + 1, len(homebrew.taps))
            tap_result = self.homebrew.install_tap(tap)
            if tap_result.success:
                self._mark_completed(item_id)
                result.completed_count += 1
            else:
                self._mark_failed("tap", tap, tap_result.error or "Unknown error")
                result.failed_count += 1

        # Install formulas
        for i, formula in enumerate(homebrew.formulas):
            if self._interrupted:
                return
            item_id = f"formula:{formula}"
            if not self.force and (
                self._is_completed(item_id) or self.homebrew.is_formula_installed(formula)
            ):
                continue
            self._report_progress(f"Installing {formula}", i + 1, len(homebrew.formulas))
            formula_result = self.homebrew.install_formula(formula)
            if formula_result.success:
                self._mark_completed(item_id)
                result.completed_count += 1
            else:
                self._mark_failed("formula", formula, formula_result.error or "Unknown error")
                result.failed_count += 1

        # Install casks
        for i, cask in enumerate(homebrew.casks):
            if self._interrupted:
                return
            item_id = f"cask:{cask}"
            if not self.force and (
                self._is_completed(item_id) or self.homebrew.is_cask_installed(cask)
            ):
                continue
            self._report_progress(f"Installing {cask}", i + 1, len(homebrew.casks))
            cask_result = self.homebrew.install_cask(cask)
            if cask_result.success:
                self._mark_completed(item_id)
                result.completed_count += 1
            else:
                self._mark_failed("cask", cask, cask_result.error or "Unknown error")
                result.failed_count += 1

    def _install_mas_apps(self, profile: Profile, result: SetupResult):
        """Install Mac App Store apps."""
        if profile.applications is None or not profile.applications.mas:
            return

        for i, app in enumerate(profile.applications.mas):
            if self._interrupted:
                return
            item_id = f"mas:{app.id}"
            if not self.force and (
                self._is_completed(item_id) or self.mas.is_installed(app.id)
            ):
                continue
            self._report_progress(f"Installing {app.name}", i + 1, len(profile.applications.mas))
            mas_result = self.mas.install(app.id)
            if mas_result.success:
                self._mark_completed(item_id)
                result.completed_count += 1
            else:
                self._mark_failed("mas", str(app.id), mas_result.error or "Unknown error")
                result.failed_count += 1

    def _setup_dotfiles(self, profile: Profile, result: SetupResult):
        """Setup dotfiles."""
        dotfiles_dir = self.config_dir / "dotfiles"
        home_dir = Path.home()

        for i, dotfile in enumerate(profile.dotfiles):
            if self._interrupted:
                return
            item_id = f"dotfile:{dotfile.path}"
            if not self.force and self._is_completed(item_id):
                continue

            source = dotfiles_dir / dotfile.path
            target = home_dir / dotfile.path

            self._report_progress(f"Setting up {dotfile.path}", i + 1, len(profile.dotfiles))

            if dotfile.mode == "copy":
                dotfile_result = self.dotfiles.copy(source, target)
            else:
                dotfile_result = self.dotfiles.symlink(source, target)

            if dotfile_result.success:
                self._mark_completed(item_id)
                result.completed_count += 1
            else:
                self._mark_failed("dotfile", dotfile.path, dotfile_result.error or "Unknown error")
                result.failed_count += 1

    def _apply_preferences(self, profile: Profile, result: SetupResult):
        """Apply system preferences."""
        for i, pref in enumerate(profile.preferences):
            if self._interrupted:
                return
            if pref.key is None or pref.value is None:
                continue
            item_id = f"preference:{pref.domain}:{pref.key}"
            if not self.force and self._is_completed(item_id):
                continue

            self._report_progress(
                f"Setting {pref.domain} {pref.key}", i + 1, len(profile.preferences)
            )

            pref_result = self.defaults.write(pref.domain, pref.key, pref.value, pref.type)
            if pref_result.success:
                self._mark_completed(item_id)
                result.completed_count += 1
            else:
                self._mark_failed(
                    "preference",
                    f"{pref.domain}:{pref.key}",
                    pref_result.error or "Unknown error",
                )
                result.failed_count += 1
