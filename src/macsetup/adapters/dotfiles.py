"""Dotfiles adapter for macsetup."""

import shutil
from pathlib import Path

from macsetup.adapters import Adapter, AdapterResult


class DotfilesAdapter(Adapter):
    """Adapter for dotfile operations."""

    def is_available(self) -> bool:
        """Dotfiles adapter is always available."""
        return True

    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return "dotfiles"

    def symlink(self, source: Path, target: Path, backup: bool = True) -> AdapterResult:
        """Create a symlink from target to source.

        Args:
            source: The source file (in config directory).
            target: The target location (e.g., ~/.zshrc).
            backup: If True, backup existing file before replacing.

        Returns:
            AdapterResult indicating success or failure.
        """
        try:
            # Ensure source exists
            if not source.exists():
                return AdapterResult(success=False, error=f"Source file does not exist: {source}")

            # Ensure target parent directory exists
            target.parent.mkdir(parents=True, exist_ok=True)

            # Handle existing file at target
            if target.exists() or target.is_symlink():
                if backup:
                    backup_path = target.with_suffix(target.suffix + ".backup")
                    if target.is_symlink():
                        target.unlink()
                    else:
                        target.rename(backup_path)
                else:
                    if target.is_symlink():
                        target.unlink()
                    else:
                        target.unlink()

            # Create symlink
            target.symlink_to(source)
            return AdapterResult(success=True, message=f"Symlinked {target} -> {source}")
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    def copy(self, source: Path, target: Path, backup: bool = True) -> AdapterResult:
        """Copy a file from source to target.

        Args:
            source: The source file (in config directory).
            target: The target location (e.g., ~/.zshrc).
            backup: If True, backup existing file before replacing.

        Returns:
            AdapterResult indicating success or failure.
        """
        try:
            # Ensure source exists
            if not source.exists():
                return AdapterResult(success=False, error=f"Source file does not exist: {source}")

            # Ensure target parent directory exists
            target.parent.mkdir(parents=True, exist_ok=True)

            # Handle existing file at target
            if target.exists():
                if backup:
                    backup_path = target.with_suffix(target.suffix + ".backup")
                    target.rename(backup_path)
                else:
                    target.unlink()

            # Copy file
            shutil.copy2(source, target)
            return AdapterResult(success=True, message=f"Copied {source} to {target}")
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    def exists(self, path: Path) -> bool:
        """Check if a file exists.

        Args:
            path: The path to check.

        Returns:
            True if the file exists, False otherwise.
        """
        return path.exists()

    def is_symlink_valid(self, target: Path, expected_source: Path) -> bool:
        """Check if a symlink points to the expected source.

        Args:
            target: The symlink path.
            expected_source: The expected source path.

        Returns:
            True if the symlink is valid and points to expected_source.
        """
        if not target.is_symlink():
            return False
        try:
            return target.resolve() == expected_source.resolve()
        except Exception:
            return False

    def copy_to_config(
        self, source: Path, config_dir: Path, relative_path: str
    ) -> AdapterResult:
        """Copy a dotfile from home to config directory.

        Args:
            source: The source file (e.g., ~/.zshrc).
            config_dir: The config directory root.
            relative_path: The relative path within the dotfiles directory.

        Returns:
            AdapterResult indicating success or failure.
        """
        try:
            target = config_dir / "dotfiles" / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)

            if source.is_symlink():
                # If it's already a symlink, resolve it first
                source = source.resolve()

            if not source.exists():
                return AdapterResult(
                    success=False, error=f"Source file does not exist: {source}"
                )

            shutil.copy2(source, target)
            return AdapterResult(success=True, message=f"Copied {source} to {target}")
        except Exception as e:
            return AdapterResult(success=False, error=str(e))
