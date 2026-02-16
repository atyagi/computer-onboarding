"""iCloud Drive adapter for macsetup.

Standalone class (NOT extending Adapter — iCloud is a filesystem path, not a CLI tool).
Provides iCloud Drive detection, path resolution, eviction checking, and conflict detection.
"""

import os
import re
from pathlib import Path

# Standard iCloud Drive path on macOS
ICLOUD_DRIVE_PATH = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"

# Macsetup subdirectory within iCloud Drive
ICLOUD_MACSETUP_DIR = ICLOUD_DRIVE_PATH / "macsetup"

# SF_DATALESS flag for evicted iCloud files (macOS Sonoma+)
SF_DATALESS = 0x40000000

# Regex for iCloud conflict files: "basename N.ext" where N >= 2
_CONFLICT_PATTERN = re.compile(r"^(.+)\s+(\d+)(\.\w+)$")


class ICloudAdapter:
    """Adapter for iCloud Drive filesystem operations."""

    def get_icloud_drive_path(self) -> Path:
        """Return the standard iCloud Drive path on macOS."""
        return ICLOUD_DRIVE_PATH

    def is_icloud_available(self) -> bool:
        """Check if iCloud Drive is available (directory exists and is a directory)."""
        return ICLOUD_DRIVE_PATH.is_dir()

    def is_file_evicted(self, path: Path) -> bool:
        """Check if a file has been evicted (cloud-only) by iCloud.

        Uses SF_DATALESS flag as primary check, with st_blocks==0 heuristic as fallback.

        Args:
            path: Path to the file to check.

        Returns:
            True if the file is evicted (cloud-only), False otherwise.
        """
        try:
            st = os.stat(path)
        except OSError:
            return False

        # Primary: SF_DATALESS flag (macOS Sonoma+ / APFS dataless files)
        flags = getattr(st, "st_flags", 0)
        if flags & SF_DATALESS:
            return True

        # Fallback heuristic: st_blocks == 0 but st_size > 0
        blocks = getattr(st, "st_blocks", -1)
        return bool(blocks == 0 and st.st_size > 0)

    def find_conflict_files(self, directory: Path) -> list[Path]:
        """Find iCloud conflict files in a directory.

        iCloud creates conflict copies with pattern: "{basename} {N}.{ext}" where N >= 2.

        Args:
            directory: Directory to scan for conflict files.

        Returns:
            List of conflict file paths.
        """
        conflicts = []
        if not directory.is_dir():
            return conflicts

        for item in directory.iterdir():
            if not item.is_file():
                continue
            match = _CONFLICT_PATTERN.match(item.name)
            if match:
                num = int(match.group(2))
                if num >= 2:
                    conflicts.append(item)

        return sorted(conflicts)
