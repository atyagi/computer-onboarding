# Feature Specification: iCloud Config Storage

**Feature Branch**: `003-icloud-config-storage`
**Created**: 2026-02-15
**Status**: Draft
**Input**: User description: "I want to be able to store the config file in an iCloud directory so that it's automatically synced when I log into iCloud on a new computer"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initialize Config Storage in iCloud (Priority: P1)

A user wants their macsetup configuration (config.yaml and captured dotfiles) to live in iCloud Drive so it syncs automatically across their Apple devices. They run a command to initialize or migrate their config directory to an iCloud location. Once set, all subsequent `macsetup` commands (capture, setup, preview, etc.) read from and write to the iCloud-backed directory without the user needing to pass `--config-dir` each time.

**Why this priority**: This is the core value of the feature. Without a persistent, easy way to point macsetup at iCloud, users would need to pass `--config-dir` or set an environment variable on every machine — defeating the purpose of automatic sync.

**Independent Test**: Can be fully tested by running the initialization command and verifying that config files are created in the iCloud Drive directory and that subsequent commands use that location by default.

**Acceptance Scenarios**:

1. **Given** iCloud Drive is available on the machine, **When** the user runs `macsetup init --icloud`, **Then** the config directory is created inside iCloud Drive and a local pointer is stored so future commands use the iCloud location automatically.
2. **Given** the user has already initialized with iCloud, **When** they run `macsetup capture` (no flags), **Then** the captured configuration is written to the iCloud-backed directory.
3. **Given** iCloud Drive is not available (user not signed in or iCloud Drive disabled), **When** the user runs `macsetup init --icloud`, **Then** the command fails with a clear error message explaining that iCloud Drive is required and how to enable it.

---

### User Story 2 - Migrate Existing Config to iCloud (Priority: P2)

A user has already captured their configuration to the default local directory (`~/.config/macsetup`). They now want to move it to iCloud so it syncs. They run a migration command that moves their existing config and dotfiles to the iCloud location and updates the local pointer.

**Why this priority**: Existing users should not have to re-capture their entire configuration. A smooth migration path preserves their current setup and makes adoption frictionless.

**Independent Test**: Can be tested by creating a config in the default location, running the migration command, and verifying that files now exist in iCloud and the default location redirects to iCloud.

**Acceptance Scenarios**:

1. **Given** a configuration exists at `~/.config/macsetup`, **When** the user runs `macsetup init --icloud`, **Then** the existing configuration is moved to the iCloud directory and a local pointer is created.
2. **Given** a configuration exists at `~/.config/macsetup` and a configuration already exists in the iCloud directory, **When** the user runs `macsetup init --icloud`, **Then** the command warns about the conflict and asks the user to choose which config to keep (or use `--force` to overwrite).
3. **Given** the migration completes successfully, **When** the user runs `macsetup preview`, **Then** it reads from the iCloud location and shows the correct configuration.

---

### User Story 3 - Restore Config on a New Mac via iCloud (Priority: P2)

A user sets up a new Mac, signs into iCloud, and iCloud Drive syncs their files. They install macsetup and run `macsetup init --icloud`. The tool detects the existing configuration in iCloud Drive and begins using it — no recapture needed. They can then run `macsetup setup` to restore their full environment.

**Why this priority**: This is the payoff of the entire feature — zero-effort config availability on a new machine. Without this, the user would need to manually transfer config files.

**Independent Test**: Can be tested by placing a valid config in the expected iCloud directory, running init, and verifying that macsetup recognizes and uses the existing config.

**Acceptance Scenarios**:

1. **Given** a valid macsetup configuration exists in iCloud Drive (synced from another machine), **When** the user runs `macsetup init --icloud` on a new Mac, **Then** the tool detects the existing config and sets up the local pointer to use it.
2. **Given** the iCloud config is detected, **When** the user runs `macsetup setup`, **Then** all applications, dotfiles, and preferences from the synced config are applied.

---

### User Story 4 - Revert to Local Storage (Priority: P3)

A user who previously set up iCloud storage wants to switch back to local-only storage. They run a command that copies the config from iCloud back to the default local directory and removes the iCloud pointer.

**Why this priority**: Users should never feel locked into iCloud. Providing an exit path builds trust and handles cases where iCloud becomes unavailable or undesirable.

**Independent Test**: Can be tested by initializing iCloud storage, then reverting and verifying config lives locally and iCloud pointer is removed.

**Acceptance Scenarios**:

1. **Given** macsetup is configured to use iCloud storage, **When** the user runs `macsetup init --local`, **Then** the configuration is copied to the default local directory and the iCloud pointer is removed.
2. **Given** the user has reverted to local storage, **When** they run `macsetup capture`, **Then** the config is written to `~/.config/macsetup` (the default local directory).

---

### Edge Cases

- What happens when iCloud Drive is still syncing (files not yet downloaded)? The system should detect placeholder/evicted files and wait or warn the user that sync is in progress.
- What happens when two machines run `macsetup capture` concurrently and iCloud creates a conflict file? The system should detect iCloud conflict files and warn the user.
- What happens when the iCloud Drive path varies across macOS versions? The system should resolve the iCloud Drive path dynamically rather than hardcoding it.
- What happens when the user's iCloud storage is full? The system should report the write failure clearly rather than silently failing.
- What happens when config files in iCloud are evicted (offloaded to cloud-only)? The system should detect this and attempt to trigger a download or warn the user.
- What happens when iCloud Drive becomes unavailable after init (user signs out, disk unmounted, network issues)? All commands fail with a clear error and remediation suggestions; no silent fallback to local storage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support storing the configuration directory inside iCloud Drive at a well-known path (e.g., `~/Library/Mobile Documents/com~apple~CloudDocs/macsetup/`).
- **FR-002**: System MUST provide a command (`macsetup init --icloud`) that initializes the iCloud config directory and creates a local pointer file so that subsequent commands use the iCloud location automatically.
- **FR-003**: System MUST store the active config directory location in a local pointer file at `~/.config/macsetup/config-dir` (a plain text file containing the path). This file is always read first to resolve the actual config directory.
- **FR-004**: System MUST detect whether iCloud Drive is available before attempting to use it, and report a clear error with remediation steps if it is not.
- **FR-005**: System MUST migrate existing configuration from the default local directory to iCloud when `init --icloud` is run and a local config already exists. Migration is a move operation: files are copied to iCloud and then deleted from the local directory. No local backup is retained.
- **FR-006**: System MUST detect and warn about conflicts when both a local config and an iCloud config already exist during initialization.
- **FR-007**: System MUST provide a revert path (`macsetup init --local`) that copies config back from iCloud to the default local directory and removes the iCloud pointer.
- **FR-008**: System MUST detect iCloud file eviction (cloud-only files not yet downloaded) and provide a meaningful warning rather than reading empty or placeholder data.
- **FR-009**: All existing commands (capture, setup, preview, sync, validate) MUST work transparently with the iCloud-backed config directory — no command changes required beyond `init`.
- **FR-010**: The `--config-dir` CLI flag and `MACSETUP_CONFIG_DIR` environment variable MUST continue to work and take precedence over the iCloud pointer when specified.
- **FR-011**: System MUST resolve the iCloud Drive path dynamically using the standard macOS iCloud Drive location rather than hardcoding a path.
- **FR-012**: When the config directory pointer references an iCloud path that is unavailable (unmounted, user signed out, path missing), commands MUST fail with a clear error message and remediation suggestions (e.g., use `--config-dir` to override or `macsetup init --local` to revert). The system MUST NOT silently fall back to the default local directory.

### Key Entities

- **Config Directory Pointer**: A small local file (`~/.config/macsetup/config-dir`) that stores the absolute path to the active configuration directory. When this file exists, all macsetup commands resolve their config directory from it. When absent, the default `~/.config/macsetup` is used.
- **iCloud Config Directory**: The macsetup configuration directory located within iCloud Drive (e.g., `~/Library/Mobile Documents/com~apple~CloudDocs/macsetup/`). Contains config.yaml and the dotfiles/ directory, identical in structure to the local config directory.

## Assumptions

- iCloud Drive on macOS uses the standard path `~/Library/Mobile Documents/com~apple~CloudDocs/`. The system will resolve this path dynamically but assumes this convention holds across supported macOS versions.
- iCloud Drive handles file sync transparently at the filesystem level. The tool does not need to implement its own sync protocol — it simply reads and writes files and relies on iCloud to propagate changes.
- Conflict resolution for simultaneous edits on multiple machines is out of scope for the initial release. The system will detect iCloud conflict files and warn the user, but will not attempt automatic merging.
- The local pointer file approach is chosen over a global config/preferences file to keep the mechanism simple and discoverable. The pointer file is always at a known location regardless of where the actual config lives.
- The `macsetup init` command is a new subcommand. It does not conflict with existing commands.
- File eviction detection (iCloud offloading files to cloud-only) will use macOS extended attributes or file size heuristics to determine if a file needs to be downloaded before reading.

## Clarifications

### Session 2026-02-15

- Q: During migration, should local files be moved (deleted after copy) or preserved as a backup? → A: Move — delete local files after copying to iCloud. No local backup is retained.
- Q: Should the system warn about sensitive dotfiles (SSH, AWS) being uploaded to iCloud during init? → A: No warning. The user already opted in to capturing sensitive files; it is their choice to store them in iCloud.
- Q: What should happen when iCloud Drive becomes unavailable after init (signed out, unmounted)? → A: Fail with a clear error and remediation suggestions (use `--config-dir` or `init --local`). No silent fallback to local storage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can set up iCloud config storage with a single command (`macsetup init --icloud`) and have all subsequent commands automatically use the iCloud location.
- **SC-002**: A user setting up a new Mac can access their full configuration within 5 minutes of signing into iCloud and installing macsetup (excluding iCloud sync time).
- **SC-003**: Existing users can migrate their local config to iCloud without losing any data or needing to re-run capture.
- **SC-004**: Users can revert from iCloud to local storage at any time without data loss.
- **SC-005**: All existing macsetup commands work identically regardless of whether config is stored locally or in iCloud — no behavioral differences beyond storage location.
