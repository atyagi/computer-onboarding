"""Homebrew adapter for macsetup."""

import os
import shutil
import subprocess

from macsetup.adapters import Adapter, AdapterResult


class HomebrewAdapter(Adapter):
    """Adapter for Homebrew package manager."""

    def __init__(self):
        self._brew_path = None

    def is_available(self) -> bool:
        """Check if brew command is available."""
        return shutil.which("brew") is not None

    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return "Homebrew"

    def _run_brew(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a brew command."""
        env = os.environ.copy()
        # Disable auto-update for speed during setup
        env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
        return subprocess.run(
            ["brew", *args],
            capture_output=True,
            text=True,
            check=check,
            env=env,
        )

    def install_tap(self, tap: str) -> AdapterResult:
        """Tap a Homebrew repository."""
        try:
            self._run_brew(["tap", tap])
            return AdapterResult(success=True, message=f"Tapped {tap}")
        except subprocess.CalledProcessError as e:
            return AdapterResult(success=False, error=e.stderr.strip())

    def install_formula(self, formula: str) -> AdapterResult:
        """Install a Homebrew formula."""
        try:
            self._run_brew(["install", formula])
            return AdapterResult(success=True, message=f"Installed {formula}")
        except subprocess.CalledProcessError as e:
            return AdapterResult(success=False, error=e.stderr.strip())

    def install_cask(self, cask: str) -> AdapterResult:
        """Install a Homebrew cask."""
        try:
            self._run_brew(["install", "--cask", cask])
            return AdapterResult(success=True, message=f"Installed {cask}")
        except subprocess.CalledProcessError as e:
            return AdapterResult(success=False, error=e.stderr.strip())

    def is_tap_installed(self, tap: str) -> bool:
        """Check if a tap is already tapped."""
        try:
            result = self._run_brew(["tap"], check=False)
            return tap in result.stdout.split("\n")
        except Exception:
            return False

    def is_formula_installed(self, formula: str) -> bool:
        """Check if a formula is already installed."""
        try:
            result = self._run_brew(["list", "--formula"], check=False)
            return formula in result.stdout.split("\n")
        except Exception:
            return False

    def is_cask_installed(self, cask: str) -> bool:
        """Check if a cask is already installed."""
        try:
            result = self._run_brew(["list", "--cask"], check=False)
            return cask in result.stdout.split("\n")
        except Exception:
            return False

    def list_formulas(self) -> list[str]:
        """List all installed formulas."""
        try:
            result = self._run_brew(["list", "--formula", "-1"], check=False)
            return [f for f in result.stdout.strip().split("\n") if f]
        except Exception:
            return []

    def list_casks(self) -> list[str]:
        """List all installed casks."""
        try:
            result = self._run_brew(["list", "--cask", "-1"], check=False)
            return [c for c in result.stdout.strip().split("\n") if c]
        except Exception:
            return []

    def list_taps(self) -> list[str]:
        """List all tapped repositories."""
        try:
            result = self._run_brew(["tap"], check=False)
            return [t for t in result.stdout.strip().split("\n") if t]
        except Exception:
            return []
