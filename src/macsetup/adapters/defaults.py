"""macOS defaults adapter for macsetup."""

import subprocess
from typing import Any

from macsetup.adapters import Adapter, AdapterResult


class DefaultsAdapter(Adapter):
    """Adapter for macOS defaults command."""

    def is_available(self) -> bool:
        """Check if defaults command is available (always true on macOS)."""
        return True

    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return "defaults"

    def _run_defaults(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a defaults command."""
        return subprocess.run(
            ["defaults", *args],
            capture_output=True,
            text=True,
            check=check,
        )

    def read(self, domain: str, key: str | None = None) -> str | None:
        """Read a preference value.

        Args:
            domain: The preference domain (e.g., "com.apple.dock").
            key: The specific key to read (None for entire domain).

        Returns:
            The value as a string, or None if not found.
        """
        try:
            args = ["read", domain]
            if key:
                args.append(key)
            result = self._run_defaults(args, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def write(
        self, domain: str, key: str, value: Any, value_type: str | None = None
    ) -> AdapterResult:
        """Write a preference value.

        Args:
            domain: The preference domain.
            key: The preference key.
            value: The value to write.
            value_type: Optional type hint (string, int, float, bool, array, dict).

        Returns:
            AdapterResult indicating success or failure.
        """
        try:
            args = ["write", domain, key]

            # Map Python values to defaults command arguments
            if value_type == "bool":
                args.extend(["-bool", "true" if value else "false"])
            elif value_type == "int":
                args.extend(["-int", str(value)])
            elif value_type == "float":
                args.extend(["-float", str(value)])
            elif value_type == "string":
                args.extend(["-string", str(value)])
            elif value_type == "array":
                args.extend(["-array", *[str(v) for v in value]])
            elif value_type == "dict":
                # Dict needs special handling - use plistlib for complex cases
                dict_args = []
                for k, v in value.items():
                    dict_args.extend([str(k), str(v)])
                args.extend(["-dict", *dict_args])
            else:
                # Auto-detect type
                if isinstance(value, bool):
                    args.extend(["-bool", "true" if value else "false"])
                elif isinstance(value, int):
                    args.extend(["-int", str(value)])
                elif isinstance(value, float):
                    args.extend(["-float", str(value)])
                else:
                    args.extend(["-string", str(value)])

            self._run_defaults(args)
            return AdapterResult(success=True, message=f"Set {domain} {key}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "does not exist" in error.lower():
                error += f"\nRemediation: Domain {domain} may not be a valid preference domain. Check with 'defaults domains'."
            elif "type" in error.lower():
                error += f"\nRemediation: Value type mismatch for {key}. Try specifying value_type explicitly."
            else:
                error += f"\nRemediation: Run 'defaults write {domain} {key}' manually to see detailed error."
            return AdapterResult(success=False, error=error)

    def delete(self, domain: str, key: str | None = None) -> AdapterResult:
        """Delete a preference value or entire domain.

        Args:
            domain: The preference domain.
            key: The specific key to delete (None for entire domain).

        Returns:
            AdapterResult indicating success or failure.
        """
        try:
            args = ["delete", domain]
            if key:
                args.append(key)
            self._run_defaults(args, check=False)
            return AdapterResult(success=True, message=f"Deleted {domain} {key or ''}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "does not exist" in error.lower():
                error += (
                    f"\nRemediation: Key {key} or domain {domain} does not exist, no action needed."
                )
            else:
                error += f"\nRemediation: Run 'defaults delete {domain} {key or ''}' manually to see detailed error."
            return AdapterResult(success=False, error=error)

    def import_domain(self, domain: str, plist_path: str) -> AdapterResult:
        """Import preferences from a plist file.

        Args:
            domain: The preference domain.
            plist_path: Path to the plist file.

        Returns:
            AdapterResult indicating success or failure.
        """
        try:
            self._run_defaults(["import", domain, plist_path])
            return AdapterResult(success=True, message=f"Imported {domain} from {plist_path}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "no such file" in error.lower() or "not found" in error.lower():
                error += f"\nRemediation: Plist file not found at {plist_path}. Verify the path is correct."
            elif "malformed" in error.lower() or "parse" in error.lower():
                error += f"\nRemediation: Plist file at {plist_path} is malformed. Validate with 'plutil {plist_path}'."
            else:
                error += f"\nRemediation: Run 'defaults import {domain} {plist_path}' manually to see detailed error."
            return AdapterResult(success=False, error=error)

    def export_domain(self, domain: str, plist_path: str) -> AdapterResult:
        """Export preferences to a plist file.

        Args:
            domain: The preference domain.
            plist_path: Path to save the plist file.

        Returns:
            AdapterResult indicating success or failure.
        """
        try:
            self._run_defaults(["export", domain, plist_path])
            return AdapterResult(success=True, message=f"Exported {domain} to {plist_path}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "does not exist" in error.lower():
                error += f"\nRemediation: Domain {domain} does not exist. Check available domains with 'defaults domains'."
            elif "permission denied" in error.lower():
                error += (
                    f"\nRemediation: Cannot write to {plist_path}. Check directory permissions."
                )
            else:
                error += f"\nRemediation: Run 'defaults export {domain} {plist_path}' manually to see detailed error."
            return AdapterResult(success=False, error=error)
