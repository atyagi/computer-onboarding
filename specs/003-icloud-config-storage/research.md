# Research: iCloud Config Storage

**Feature Branch**: `003-icloud-config-storage`
**Date**: 2026-02-15

## 1. iCloud Drive Path Resolution

**Decision**: Use `~/Library/Mobile Documents/com~apple~CloudDocs/` as the standard iCloud Drive path.

**Rationale**: This has been the canonical path since iCloud Drive's introduction and remains correct through macOS Sequoia. The `~/Library/CloudStorage/` path is for third-party cloud providers (Dropbox, OneDrive, Google Drive) that use Apple's FileProvider framework — not for iCloud Drive itself.

**Alternatives considered**:
- `~/Library/CloudStorage/iCloud Drive/` — Incorrect; this is an alias on some systems, not the actual data location.
- Using `NSFileManager.ubiquityIdentityToken` via PyObjC — Overkill; directory existence check is sufficient and avoids adding a native dependency.

**Python path construction**:
```python
Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
```

**App subdirectory**: The macsetup config will live at `com~apple~CloudDocs/macsetup/` (not in an app container, since macsetup is not a sandboxed app).

## 2. iCloud Drive Availability Detection

**Decision**: Check directory existence as the primary detection method.

**Rationale**: `Path.is_dir()` on the iCloud Drive path is the simplest, most reliable check. The directory only exists when iCloud Drive is enabled. Reading plists (MobileMeAccounts.plist) is fragile across macOS versions and adds unnecessary complexity.

**Alternatives considered**:
- Parsing `~/Library/Preferences/MobileMeAccounts.plist` for `MOBILE_DOCUMENTS` service — More authoritative but fragile across OS versions; plist structure is undocumented.
- Checking `com.apple.bird` defaults domain — Only relevant for optimize-storage setting, not availability.
- PyObjC / `NSFileManager` APIs — Adds a heavyweight dependency for a simple check.

## 3. File Eviction Detection

**Decision**: Use the `SF_DATALESS` flag (`0x40000000`) on `stat.st_flags` as the primary detection method, with a `st_blocks == 0 && st_size > 0` heuristic as fallback.

**Rationale**: macOS Sonoma+ uses APFS dataless files for eviction. Key behaviors:
- `os.path.exists()` returns `True` for evicted files
- `stat.st_size` reports the **original** file size (not zero)
- `stat.st_blocks` is `0` for evicted files
- `stat.st_flags & SF_DATALESS` is the canonical check
- **Reading an evicted file triggers automatic download** — the OS transparently downloads before returning data, blocking the read call
- `stat.SF_DATALESS` is available in Python 3.13+ (the project uses Python 3.14)

**Pre-Sonoma eviction** used `.filename.ext.icloud` placeholder files. Since the project targets Python 3.14 (which implies modern macOS), the dataless approach is primary, but checking for `.icloud` placeholders is a reasonable fallback.

**Alternatives considered**:
- Always triggering materialization (just read the file) — Risky; could block indefinitely on slow networks with no user feedback.
- Using `brctl download` to pre-materialize — Good for explicit download but requires subprocess call; should be used when eviction is detected and user wants to proceed.

## 4. Conflict File Detection

**Decision**: Detect iCloud conflict files using the `{basename} {N}.{ext}` naming pattern where N >= 2.

**Rationale**: iCloud creates conflict copies with a numeric suffix (e.g., `config 2.yaml`). This pattern is simple to detect with a regex. The `NSFileVersion` API (for data-scope conflicts) requires PyObjC and is overkill for a CLI tool.

**Caveat**: This naming pattern is also used by Finder for manual copies. No metadata distinguishes iCloud conflicts from Finder copies. For config files with specific names (`config.yaml`), false positives are unlikely.

**Alternatives considered**:
- `NSFileVersion` API via PyObjC — Authoritative but adds a native dependency.
- Ignoring conflicts entirely — Too risky; a stale conflict file could confuse users.

## 5. Config Directory Pointer Mechanism

**Decision**: Use a plain text pointer file at `~/.config/macsetup/config-dir` containing the absolute path to the active config directory.

**Rationale**: The existing `get_config_dir()` function in `cli.py` is the single resolution point for all commands. Adding pointer file reading here makes all existing commands iCloud-aware with zero changes to services or adapters. The resolution order becomes:

1. `--config-dir` CLI flag (highest precedence)
2. `MACSETUP_CONFIG_DIR` environment variable
3. Pointer file at `~/.config/macsetup/config-dir`
4. Default `~/.config/macsetup`

**Alternatives considered**:
- Symlink from `~/.config/macsetup` to iCloud directory — Fragile; symlinks to iCloud can cause sync issues. Also makes it impossible to store the pointer alongside other local metadata.
- Global preferences file (JSON/YAML) — Overcomplicated for storing a single path.
- Environment variable only — Doesn't persist across shell sessions without modifying shell config.

## 6. Impact Analysis on Existing Code

**Decision**: Modify only `get_config_dir()` in `cli.py` and add the `init` command. No changes to services or adapters.

**Rationale**: The codebase already has clean separation — all services receive `config_dir: Path` as a constructor parameter from the resolved CLI value. The following files need no changes:
- `src/macsetup/services/capture.py`
- `src/macsetup/services/setup.py`
- `src/macsetup/services/sync.py`
- `src/macsetup/services/preview.py`
- `src/macsetup/adapters/dotfiles.py`
- `src/macsetup/models/config.py`

**Files that need changes**:
- `src/macsetup/cli.py` — Modify `get_config_dir()`, add `cmd_init()` and parser setup
- `tests/unit/test_cli.py` — Add tests for pointer resolution and init command

**New files**:
- `src/macsetup/adapters/icloud.py` — iCloud Drive detection, eviction checking, conflict detection
- `src/macsetup/services/init.py` — Init command business logic (iCloud setup, migration, revert)
- `tests/unit/test_icloud.py` — Tests for iCloud adapter
- `tests/unit/test_init.py` — Tests for init service
