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
            error = e.stderr.strip()
            if "already tapped" in error.lower():
                error += f"\nRemediation: Tap {tap} is already installed, no action needed."
            elif "invalid tap" in error.lower() or "not found" in error.lower():
                error += (
                    "\nRemediation: Verify the tap name is correct. Format should be 'user/repo'."
                )
            else:
                error += f"\nRemediation: Run 'brew tap {tap}' manually to see detailed error."
            return AdapterResult(success=False, error=error)

    def install_formula(self, formula: str) -> AdapterResult:
        """Install a Homebrew formula."""
        try:
            self._run_brew(["install", formula])
            return AdapterResult(success=True, message=f"Installed {formula}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "already installed" in error.lower():
                error += f"\nRemediation: Formula {formula} is already installed, no action needed."
            elif "no available formula" in error.lower() or "not found" in error.lower():
                error += f"\nRemediation: Verify the formula name is correct. Search with 'brew search {formula}'."
            elif "permission denied" in error.lower():
                error += "\nRemediation: Check Homebrew directory permissions. Run 'brew doctor' for diagnostics."
            else:
                error += (
                    f"\nRemediation: Run 'brew install {formula}' manually to see detailed error."
                )
            return AdapterResult(success=False, error=error)

    def install_cask(self, cask: str) -> AdapterResult:
        """Install a Homebrew cask."""
        try:
            self._run_brew(["install", "--cask", cask])
            return AdapterResult(success=True, message=f"Installed {cask}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "already installed" in error.lower():
                error += f"\nRemediation: Cask {cask} is already installed, no action needed."
            elif "no available cask" in error.lower() or "not found" in error.lower():
                error += f"\nRemediation: Verify the cask name is correct. Search with 'brew search --cask {cask}'."
            elif "permission denied" in error.lower():
                error += "\nRemediation: Cask installation may require admin privileges. Check system permissions."
            elif "sha256 mismatch" in error.lower():
                error += (
                    "\nRemediation: Download may be corrupted. Run 'brew cleanup' and try again."
                )
            else:
                error += f"\nRemediation: Run 'brew install --cask {cask}' manually to see detailed error."
            return AdapterResult(success=False, error=error)

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
