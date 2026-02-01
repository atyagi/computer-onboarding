# Feature Specification: macOS Configuration Sync CLI

**Feature Branch**: `001-macos-config-sync`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description: "CLI tool to automate macOS setup for myself whenever I get a new computer, which should include configuration syncing as I continue using my current machine"

## User Scenarios & Testing

### User Story 1 - Initial Machine Setup (Priority: P1)

As a user with a new Mac, I want to run a single command that installs all my essential applications and applies my preferred configurations, so that I can start working productively within minutes instead of hours.

**Why this priority**: This is the core value proposition—reducing new machine setup from hours to minutes. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by running the setup command on a fresh macOS installation (or VM) and verifying all specified applications are installed and configurations applied.

**Acceptance Scenarios**:

1. **Given** a fresh macOS installation with no custom software, **When** I run the setup command, **Then** all applications defined in my configuration are installed and ready to use.
2. **Given** a fresh macOS installation, **When** I run the setup command, **Then** all my dotfiles and system preferences are applied correctly.
3. **Given** a setup in progress, **When** an installation fails for one application, **Then** the tool continues with remaining items and reports the failure at the end.
4. **Given** a partially configured machine, **When** I run the setup command, **Then** already-installed applications are skipped and only missing items are installed.

---

### User Story 2 - Configuration Capture (Priority: P2)

As a user on my current Mac, I want to capture and save my current configurations and installed applications, so that I have an up-to-date snapshot ready for my next machine.

**Why this priority**: Without capturing current state, there's nothing to restore. This enables the P1 story but can be developed and tested independently.

**Independent Test**: Can be tested by running the capture command and verifying the output file accurately reflects installed applications and configurations.

**Acceptance Scenarios**:

1. **Given** a configured Mac with applications installed, **When** I run the capture command, **Then** a configuration file is created listing all tracked applications.
2. **Given** custom dotfiles exist (e.g., shell config, git config), **When** I run the capture command, **Then** those dotfiles are included in the configuration.
3. **Given** macOS system preferences have been customized, **When** I run the capture command, **Then** relevant preferences are captured in the configuration.

---

### User Story 3 - Ongoing Configuration Sync (Priority: P3)

As a user who regularly installs new tools or changes configurations, I want the tool to periodically sync my current state, so that my configuration is always up-to-date without manual intervention.

**Why this priority**: Adds convenience but not essential for core functionality. Users can manually run capture when needed.

**Independent Test**: Can be tested by making configuration changes, waiting for sync interval, and verifying changes are captured.

**Acceptance Scenarios**:

1. **Given** sync is enabled, **When** I install a new application via supported package managers, **Then** the configuration is automatically updated within the sync interval.
2. **Given** sync is enabled, **When** I modify a tracked dotfile, **Then** the change is captured in the configuration.
3. **Given** sync is running, **When** I want to disable it temporarily, **Then** I can pause and resume syncing.

---

### User Story 4 - Configuration Preview and Selective Apply (Priority: P4)

As a user setting up a new machine, I want to preview what will be installed and selectively exclude items, so that I can customize the setup for different contexts (e.g., work vs personal machine).

**Why this priority**: Nice-to-have refinement that improves user experience but isn't blocking for core functionality.

**Independent Test**: Can be tested by running preview command and verifying output matches configuration, then running selective setup and verifying only chosen items are installed.

**Acceptance Scenarios**:

1. **Given** a configuration file exists, **When** I run the preview command, **Then** I see a list of all applications and configurations that would be applied.
2. **Given** I'm running setup, **When** I specify exclusions, **Then** those items are skipped during installation.
3. **Given** I have multiple configuration profiles, **When** I run setup with a profile flag, **Then** only that profile's items are applied.

---

### Edge Cases

- What happens when the configuration file doesn't exist on a new machine? Tool guides user to pull from backup location or start fresh.
- How does the system handle applications that require manual intervention (e.g., license keys, login)? Mark as "manual step required" and list at end.
- What happens when running on an unsupported macOS version? Warn user and offer to proceed with potential issues.
- How does the tool handle conflicting configurations? Newer timestamp wins, with option to review conflicts.
- What happens during setup if network connectivity is lost? Pause, retry with exponential backoff, resume where left off.

## Requirements

### Functional Requirements

- **FR-001**: System MUST install applications from standard macOS package managers (Homebrew, Mac App Store)
- **FR-002**: System MUST capture and restore dotfiles from the user's home directory
- **FR-003**: System MUST capture and restore select macOS system preferences
- **FR-004**: System MUST provide idempotent operations (running setup multiple times produces same result)
- **FR-005**: System MUST continue processing after individual item failures and report all failures at completion
- **FR-006**: System MUST support a "dry run" mode showing what would be changed without making changes
- **FR-007**: System MUST store configuration in a human-readable, version-controllable format
- **FR-008**: System MUST support selective installation (include/exclude specific items)
- **FR-009**: System MUST provide clear progress indication during long-running operations
- **FR-010**: System MUST work offline for configuration capture (network only needed for installation)
- **FR-011**: System MUST support configuration profiles for different machine contexts (e.g., work, personal)
- **FR-012**: System MUST validate configuration file integrity before applying changes

### Key Entities

- **Configuration**: The complete snapshot of a user's machine state including applications, dotfiles, and preferences. Contains metadata (capture date, source machine, macOS version) and lists of items.
- **Application**: A software package to be installed. Includes name, installation source (Homebrew, Mac App Store, direct download), and optional version constraints.
- **Dotfile**: A configuration file from the user's home directory. Includes path and content.
- **Preference**: A macOS system preference setting. Includes domain, key, and value.
- **Profile**: A named subset of the configuration for context-specific setups (e.g., "work" profile excludes personal apps).

## Assumptions

- User has administrator access on both source and target machines
- Homebrew is the primary package manager (will be installed if missing)
- Git is available or will be installed for configuration version control
- Configuration storage location is user-specified (local directory, Git repo, or cloud storage)
- Mac App Store applications require user to be signed into their Apple ID
- The tool runs on macOS 12 (Monterey) or later

## Success Criteria

### Measurable Outcomes

- **SC-001**: User can complete full machine setup (50+ applications, all dotfiles) in under 30 minutes of hands-on time
- **SC-002**: Configuration capture completes in under 2 minutes for typical setups (100 applications, 20 dotfiles)
- **SC-003**: 95% of captured configurations can be restored without manual intervention
- **SC-004**: User can identify and resolve setup failures within 5 minutes using provided error messages
- **SC-005**: Setup process can be interrupted and resumed without starting over
- **SC-006**: User can customize setup for different machine contexts in under 5 minutes
