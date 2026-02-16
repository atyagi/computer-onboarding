"""Init service for macsetup — handles iCloud setup, migration, and revert."""

import shutil
from pathlib import Path

from macsetup.adapters.icloud import ICloudAdapter
from macsetup.cli import delete_pointer_file, write_pointer_file


class InitService:
    """Business logic for the init command."""

    def __init__(
        self,
        icloud_adapter: ICloudAdapter | None = None,
        default_config_dir: Path | None = None,
        pointer_path: Path | None = None,
    ):
        self.icloud = icloud_adapter or ICloudAdapter()
        self.default_config_dir = default_config_dir or (Path.home() / ".config" / "macsetup")
        self.pointer_path = pointer_path or (self.default_config_dir / "config-dir")

    def init_icloud(self, force: bool = False) -> dict:
        """Initialize iCloud Drive as the config storage location.

        Handles three cases:
        1. Fresh init (no local config, no iCloud config)
        2. Migration (local config exists, no iCloud config)
        3. Conflict (both local and iCloud configs exist)

        Args:
            force: If True, overwrite existing iCloud config on conflict.

        Returns:
            Dict with success status, storage type, config_dir, etc.
        """
        if not self.icloud.is_icloud_available():
            return {
                "success": False,
                "error": "icloud_not_available",
                "message": "iCloud Drive is not available",
            }

        icloud_drive = self.icloud.get_icloud_drive_path()
        icloud_macsetup = icloud_drive / "macsetup"

        local_config = self.default_config_dir / "config.yaml"
        icloud_config = icloud_macsetup / "config.yaml"
        has_local = local_config.is_file()
        has_icloud = icloud_config.is_file()

        # Conflict detection
        if has_local and has_icloud and not force:
            return {
                "success": False,
                "error": "conflict",
                "message": "Configuration exists in both local storage and iCloud Drive.",
                "local_path": str(local_config),
                "icloud_path": str(icloud_config),
            }

        # Create iCloud macsetup directory
        icloud_macsetup.mkdir(parents=True, exist_ok=True)

        # Migration: move local config to iCloud
        if has_local:
            try:
                files_moved = self._migrate_to_icloud(icloud_macsetup)
            except (OSError, shutil.Error) as e:
                failed_path = getattr(e, "filename", str(self.default_config_dir))
                return {
                    "success": False,
                    "error": "write_failure",
                    "message": "iCloud Drive may be full or read-only",
                    "path": str(failed_path),
                }

            write_pointer_file(self.pointer_path, icloud_macsetup)
            return {
                "success": True,
                "storage": "icloud",
                "config_dir": str(icloud_macsetup),
                "migrated": True,
                "files_moved": files_moved,
            }

        # Existing iCloud config detected (US3 - new Mac scenario)
        if has_icloud:
            write_pointer_file(self.pointer_path, icloud_macsetup)
            return {
                "success": True,
                "storage": "icloud",
                "config_dir": str(icloud_macsetup),
                "migrated": False,
                "files_moved": 0,
                "existing_config": True,
            }

        # Fresh init — no config anywhere
        write_pointer_file(self.pointer_path, icloud_macsetup)
        return {
            "success": True,
            "storage": "icloud",
            "config_dir": str(icloud_macsetup),
            "migrated": False,
            "files_moved": 0,
        }

    def _migrate_to_icloud(self, icloud_macsetup: Path) -> int:
        """Copy local config files to iCloud and delete local originals.

        Args:
            icloud_macsetup: Target iCloud macsetup directory.

        Returns:
            Number of files moved.
        """
        files_moved = 0

        # Copy config.yaml
        local_config = self.default_config_dir / "config.yaml"
        if local_config.is_file():
            shutil.copy2(local_config, icloud_macsetup / "config.yaml")
            files_moved += 1

        # Copy dotfiles directory
        local_dotfiles = self.default_config_dir / "dotfiles"
        if local_dotfiles.is_dir():
            target_dotfiles = icloud_macsetup / "dotfiles"
            if target_dotfiles.exists():
                shutil.rmtree(target_dotfiles)
            shutil.copytree(local_dotfiles, target_dotfiles)
            files_moved += sum(1 for _ in local_dotfiles.rglob("*") if _.is_file())

        # Delete local originals
        if local_config.is_file():
            local_config.unlink()
        if local_dotfiles.is_dir():
            shutil.rmtree(local_dotfiles)

        return files_moved

    def init_local(self) -> dict:
        """Revert to local storage, copying config from iCloud.

        Returns:
            Dict with success status, storage type, config_dir, etc.
        """
        if not self.pointer_path.is_file():
            return {
                "success": False,
                "error": "not_using_icloud",
                "message": "Not currently using iCloud storage (no pointer file)",
            }

        icloud_dir = Path(self.pointer_path.read_text().strip())

        # Copy config from iCloud to local
        files_copied = 0

        icloud_config = icloud_dir / "config.yaml"
        if icloud_config.is_file():
            self.default_config_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(icloud_config, self.default_config_dir / "config.yaml")
            files_copied += 1

        icloud_dotfiles = icloud_dir / "dotfiles"
        if icloud_dotfiles.is_dir():
            target_dotfiles = self.default_config_dir / "dotfiles"
            if target_dotfiles.exists():
                shutil.rmtree(target_dotfiles)
            shutil.copytree(icloud_dotfiles, target_dotfiles)
            files_copied += sum(1 for _ in icloud_dotfiles.rglob("*") if _.is_file())

        # Delete pointer file (do NOT delete iCloud copy)
        delete_pointer_file(self.pointer_path)

        return {
            "success": True,
            "storage": "local",
            "config_dir": str(self.default_config_dir),
            "files_copied": files_copied,
            "icloud_dir": str(icloud_dir),
        }

    def status(self) -> dict:
        """Get current storage configuration status.

        Returns:
            Dict with storage type, config_dir, pointer_file, icloud_available.
        """
        icloud_available = self.icloud.is_icloud_available()

        if self.pointer_path.is_file():
            target = self.pointer_path.read_text().strip()
            return {
                "storage": "icloud",
                "config_dir": target,
                "pointer_file": str(self.pointer_path),
                "icloud_available": icloud_available,
            }

        return {
            "storage": "local",
            "config_dir": str(self.default_config_dir),
            "pointer_file": "not set",
            "icloud_available": icloud_available,
        }
