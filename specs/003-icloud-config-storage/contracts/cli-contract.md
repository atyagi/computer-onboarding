# CLI Contract: init command

**Feature Branch**: `003-icloud-config-storage`
**Date**: 2026-02-15

## Command: `macsetup init`

Initialize or change the storage backend for macsetup configuration.

### Usage

```
macsetup init --icloud [--force] [--quiet] [--json]
macsetup init --local [--quiet] [--json]
macsetup init --status [--json]
```

### Subcommand: `init --icloud`

Set up iCloud Drive as the config storage location.

**Flags**:
- `--force`: Overwrite existing iCloud config if both local and iCloud configs exist (conflict resolution)
- `--quiet`: Suppress non-essential output
- `--json`: Output in JSON format

**Behavior matrix**:

| Local config exists | iCloud config exists | --force | Result |
|---------------------|---------------------|---------|--------|
| No | No | N/A | Create empty iCloud dir, write pointer |
| Yes | No | N/A | Move local to iCloud, write pointer |
| No | Yes | N/A | Write pointer (use existing iCloud config) |
| Yes | Yes | No | Error (conflict), exit code 2 |
| Yes | Yes | Yes | Overwrite iCloud with local, delete local, write pointer |

**Exit codes**:
- `0`: Success
- `1`: iCloud Drive not available
- `2`: Conflict detected (both local and iCloud configs exist)

**Human output** (success, migration):
```
Migrating configuration to iCloud Drive...
  Moving config.yaml
  Moving dotfiles/ (6 files)
  Creating pointer file

Configuration moved to ~/Library/Mobile Documents/com~apple~CloudDocs/macsetup/
All macsetup commands will now use iCloud storage.
```

**Human output** (success, fresh):
```
Initialized iCloud storage at ~/Library/Mobile Documents/com~apple~CloudDocs/macsetup/
All macsetup commands will now use iCloud storage.
```

**Human output** (success, existing iCloud config detected):
```
Found existing configuration in iCloud Drive.
  Profile: default (12 formulas, 8 casks, 6 dotfiles)

All macsetup commands will now use iCloud storage.
```

**Human output** (error, iCloud not available):
```
Error: iCloud Drive is not available.

Remediation:
  1. Open System Settings > [Your Name] > iCloud
  2. Enable iCloud Drive
  3. Re-run: macsetup init --icloud
```

**Human output** (error, conflict):
```
Error: Configuration exists in both local storage and iCloud Drive.

  Local:  ~/.config/macsetup/config.yaml (captured 2026-02-14)
  iCloud: ~/Library/Mobile Documents/com~apple~CloudDocs/macsetup/config.yaml (captured 2026-02-10)

To overwrite the iCloud config with your local config:
  macsetup init --icloud --force

To keep the iCloud config (discard local):
  rm ~/.config/macsetup/config.yaml && macsetup init --icloud
```

**JSON output** (success):
```json
{
  "success": true,
  "storage": "icloud",
  "config_dir": "/Users/jane/Library/Mobile Documents/com~apple~CloudDocs/macsetup",
  "migrated": true,
  "files_moved": 7
}
```

**JSON output** (error):
```json
{
  "success": false,
  "error": "icloud_not_available",
  "message": "iCloud Drive is not available"
}
```

### Subcommand: `init --local`

Revert to local storage, copying config from iCloud back to default location.

**Flags**:
- `--quiet`: Suppress non-essential output
- `--json`: Output in JSON format

**Behavior**:
- Copy config from iCloud to `~/.config/macsetup/`
- Remove the pointer file
- Do NOT delete the iCloud copy (user may still want it synced to other machines)

**Exit codes**:
- `0`: Success
- `1`: Not currently using iCloud storage (no pointer file)

**Human output** (success):
```
Copying configuration from iCloud to local storage...
  Copying config.yaml
  Copying dotfiles/ (6 files)
  Removing pointer file

Configuration restored to ~/.config/macsetup/
All macsetup commands will now use local storage.

Note: Your iCloud copy was not deleted. To remove it:
  rm -rf "~/Library/Mobile Documents/com~apple~CloudDocs/macsetup"
```

**JSON output** (success):
```json
{
  "success": true,
  "storage": "local",
  "config_dir": "/Users/jane/.config/macsetup",
  "files_copied": 7
}
```

### Subcommand: `init --status`

Show current storage configuration.

**Exit codes**:
- `0`: Always (informational — even when iCloud is unavailable or pointer is broken). Scripts should check the JSON `icloud_available` and `storage` fields to detect degraded states.

**Human output**:
```
Storage: icloud
Config directory: ~/Library/Mobile Documents/com~apple~CloudDocs/macsetup
Pointer file: ~/.config/macsetup/config-dir
iCloud Drive: available
```

Or:
```
Storage: local (default)
Config directory: ~/.config/macsetup
Pointer file: not set
```

**JSON output**:
```json
{
  "storage": "icloud",
  "config_dir": "/Users/jane/Library/Mobile Documents/com~apple~CloudDocs/macsetup",
  "pointer_file": "/Users/jane/.config/macsetup/config-dir",
  "icloud_available": true
}
```

## Modified behavior: `get_config_dir()`

The existing config directory resolution function gains pointer file awareness.

**New resolution order**:
```
1. --config-dir CLI flag        → return specified path
2. MACSETUP_CONFIG_DIR env var  → return env var path
3. Read ~/.config/macsetup/config-dir → if exists and valid, return contents
4. Return ~/.config/macsetup    → default
```

**Pointer file validation**:
- File must contain a single line with an absolute path
- Path must exist as a directory
- If pointer file exists but path is invalid/unreachable → error with remediation

**Error output** (pointer to unreachable path):
```
Error: Configuration directory is not accessible: ~/Library/Mobile Documents/com~apple~CloudDocs/macsetup

The config directory pointer (~/.config/macsetup/config-dir) references a path
that does not exist or is not accessible.

This may happen if:
  - iCloud Drive is not enabled on this machine
  - You are not signed into iCloud
  - iCloud Drive has not finished syncing

To fix:
  - Enable iCloud Drive: System Settings > [Your Name] > iCloud
  - Override temporarily: macsetup --config-dir /path/to/config <command>
  - Revert to local storage: macsetup init --local
```
