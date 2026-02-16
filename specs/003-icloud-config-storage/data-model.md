# Data Model: iCloud Config Storage

**Feature Branch**: `003-icloud-config-storage`
**Date**: 2026-02-15

## Entities

### Config Directory Pointer

A plain text file that redirects macsetup to an alternate config directory.

**Location**: `~/.config/macsetup/config-dir` (fixed, never changes)

**Format**: Single line containing an absolute path, no trailing newline required.

**Example content**:
```
/Users/jane/Library/Mobile Documents/com~apple~CloudDocs/macsetup
```

**Validation rules**:
- Path must be absolute (starts with `/`)
- Path must exist and be a directory
- Path must be readable and writable
- If path is unreachable, commands fail with error (FR-012)
- File is optional — absence means use default `~/.config/macsetup`

**Lifecycle**:
| State | Trigger | Result |
|-------|---------|--------|
| Absent | Fresh install / default | Commands use `~/.config/macsetup` |
| Created | `macsetup init --icloud` | Commands use iCloud path |
| Removed | `macsetup init --local` | Commands revert to default |
| Overwritten | `macsetup init --icloud` (re-run) | Points to (possibly different) iCloud path |

### iCloud Config Directory

The macsetup configuration directory located within iCloud Drive. Identical in structure to the local config directory.

**Location**: `~/Library/Mobile Documents/com~apple~CloudDocs/macsetup/`

**Structure** (mirrors local config dir):
```
macsetup/
├── config.yaml          # Main configuration file
├── dotfiles/            # Captured dotfile copies
│   ├── .zshrc
│   ├── .gitconfig
│   └── .config/
│       └── ...
├── .state.json          # Setup resume state (if setup was interrupted)
└── .sync.pid            # Sync daemon PID file (if sync is running)
```

**Validation rules**:
- Must be inside a valid iCloud Drive path
- `config.yaml` presence indicates an existing configuration
- Empty directory (no `config.yaml`) indicates fresh initialization

### iCloud Drive Status

Not a persisted entity — a runtime detection result used during `init` and for eviction warnings.

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| available | bool | iCloud Drive directory exists |
| path | Path | Resolved iCloud Drive root path |

## Resolution Order

The config directory resolution chain, from highest to lowest precedence:

```
1. --config-dir CLI flag        → Use specified path directly
2. MACSETUP_CONFIG_DIR env var  → Use env var path directly
3. ~/.config/macsetup/config-dir pointer file → Read path from file
4. ~/.config/macsetup (default) → Use default path
```

Steps 1 and 2 bypass the pointer file entirely. This ensures users always have an escape hatch.

## State Transitions

### Init --icloud (with existing local config)

```
Before:
  ~/.config/macsetup/config.yaml        EXISTS
  ~/.config/macsetup/dotfiles/          EXISTS
  ~/.config/macsetup/config-dir         ABSENT
  iCloud Drive macsetup/                ABSENT

After:
  ~/.config/macsetup/config.yaml        DELETED (moved)
  ~/.config/macsetup/dotfiles/          DELETED (moved)
  ~/.config/macsetup/config-dir         CREATED (points to iCloud)
  iCloud Drive macsetup/config.yaml     CREATED (from local)
  iCloud Drive macsetup/dotfiles/       CREATED (from local)
```

### Init --icloud (fresh, no existing config)

```
Before:
  ~/.config/macsetup/                   MAY NOT EXIST
  iCloud Drive macsetup/                ABSENT

After:
  ~/.config/macsetup/config-dir         CREATED (points to iCloud)
  iCloud Drive macsetup/                CREATED (empty dir)
```

### Init --icloud (existing iCloud config from another machine)

```
Before:
  ~/.config/macsetup/                   MAY NOT EXIST
  iCloud Drive macsetup/config.yaml     EXISTS (synced)

After:
  ~/.config/macsetup/config-dir         CREATED (points to iCloud)
  iCloud Drive macsetup/config.yaml     UNCHANGED
```

### Init --local (revert from iCloud)

```
Before:
  ~/.config/macsetup/config-dir         EXISTS (points to iCloud)
  iCloud Drive macsetup/config.yaml     EXISTS

After:
  ~/.config/macsetup/config-dir         DELETED
  ~/.config/macsetup/config.yaml        CREATED (copied from iCloud)
  ~/.config/macsetup/dotfiles/          CREATED (copied from iCloud)
  iCloud Drive macsetup/                UNCHANGED (not deleted)
```

### Conflict: Both local and iCloud configs exist

```
Before:
  ~/.config/macsetup/config.yaml        EXISTS
  iCloud Drive macsetup/config.yaml     EXISTS

Action: macsetup init --icloud
Result: ERROR — conflict detected. User must choose:
  - Use --force to overwrite iCloud config with local
  - Manually resolve (delete one config)
```

### Conflict resolution: --force (overwrite iCloud with local)

```
Before:
  ~/.config/macsetup/config.yaml        EXISTS
  ~/.config/macsetup/dotfiles/          EXISTS
  iCloud Drive macsetup/config.yaml     EXISTS

After (macsetup init --icloud --force):
  ~/.config/macsetup/config.yaml        DELETED (moved)
  ~/.config/macsetup/dotfiles/          DELETED (moved)
  ~/.config/macsetup/config-dir         CREATED (points to iCloud)
  iCloud Drive macsetup/config.yaml     OVERWRITTEN (from local)
  iCloud Drive macsetup/dotfiles/       OVERWRITTEN (from local)
```
