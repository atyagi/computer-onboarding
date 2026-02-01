"""Mac App Store adapter for macsetup."""

import shutil
import subprocess

from macsetup.adapters import Adapter, AdapterResult


class MasAdapter(Adapter):
    """Adapter for Mac App Store CLI (mas)."""

    def is_available(self) -> bool:
        """Check if mas command is available."""
        return shutil.which("mas") is not None

    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return "Mac App Store CLI"

    def _run_mas(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a mas command."""
        return subprocess.run(
            ["mas", *args],
            capture_output=True,
            text=True,
            check=check,
        )

    def install(self, app_id: int) -> AdapterResult:
        """Install an app from the Mac App Store."""
        try:
            self._run_mas(["install", str(app_id)])
            return AdapterResult(success=True, message=f"Installed app {app_id}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "not signed in" in error.lower():
                error += "\nRemediation: Sign into the Mac App Store first: open /System/Applications/App\\ Store.app"
            elif "not found" in error.lower() or "no results" in error.lower():
                error += f"\nRemediation: Verify app ID {app_id} is correct. Search for apps with 'mas search <name>'."
            elif "already installed" in error.lower():
                error += f"\nRemediation: App {app_id} is already installed, no action needed."
            elif "purchased" in error.lower():
                error += f"\nRemediation: App {app_id} must be purchased or downloaded from App Store first."
            else:
                error += f"\nRemediation: Run 'mas install {app_id}' manually to see detailed error."
            return AdapterResult(success=False, error=error)

    def is_installed(self, app_id: int) -> bool:
        """Check if an app is already installed."""
        try:
            result = self._run_mas(["list"], check=False)
            # mas list format: "497799835  Xcode (15.0)"
            return any(line.strip().startswith(str(app_id)) for line in result.stdout.split("\n"))
        except Exception:
            return False

    def is_signed_in(self) -> bool:
        """Check if user is signed into the App Store."""
        try:
            result = self._run_mas(["account"], check=False)
            # Returns email if signed in, "Not signed in" otherwise
            return result.returncode == 0 and "Not signed in" not in result.stdout
        except Exception:
            return False

    def list_installed(self) -> list[tuple[int, str]]:
        """List all installed apps from the Mac App Store.

        Returns:
            List of tuples (app_id, app_name).
        """
        apps = []
        try:
            result = self._run_mas(["list"], check=False)
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                # Format: "497799835  Xcode (15.0)"
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    try:
                        app_id = int(parts[0])
                        # Extract name (everything before the version in parens)
                        name = parts[1].rsplit("(", 1)[0].strip()
                        apps.append((app_id, name))
                    except ValueError:
                        continue
        except Exception:
            pass
        return apps
