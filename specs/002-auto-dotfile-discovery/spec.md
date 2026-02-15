# Feature Specification: Automatic Dotfile Discovery

**Feature Branch**: `002-auto-dotfile-discovery`
**Created**: 2026-02-12
**Status**: Implemented
**Input**: User description: "I'd like to have this feature automatically find common dotfiles and keep track of them the same way as the homebrew and mac app store apps"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Dotfile Detection During Capture (Priority: P1)

A user runs `macsetup capture` without specifying any `--dotfiles` flag. The system automatically scans the user's home directory for well-known dotfiles (shell configs, git configs, editor configs, etc.) and includes every one it finds in the captured configuration — just like how Homebrew formulas and Mac App Store apps are discovered automatically without the user listing them.

**Why this priority**: This is the core value of the feature. Currently, users must manually enumerate every dotfile path, which is error-prone and requires them to know where every config file lives. Automatic discovery removes this burden and brings dotfiles to parity with the Homebrew and MAS capture experience.

**Independent Test**: Can be fully tested by running `macsetup capture` on a machine with common dotfiles present and verifying that the resulting config.yaml includes discovered dotfiles without any `--dotfiles` flag.

**Acceptance Scenarios**:

1. **Given** a user's home directory contains `.zshrc`, `.gitconfig`, and `.config/starship.toml`, **When** the user runs `macsetup capture`, **Then** all three files appear in the captured configuration's dotfiles list.
2. **Given** a user's home directory has no dotfiles from the known list, **When** the user runs `macsetup capture`, **Then** the dotfiles section is empty and no errors are reported.
3. **Given** a user's home directory contains `.zshrc` and `.bashrc`, **When** the user runs `macsetup capture`, **Then** both are captured (the system does not assume only one shell config is relevant).

---

### User Story 2 - Combining Auto-Discovery with Explicit Dotfiles (Priority: P2)

A user runs `macsetup capture --dotfiles ".my-custom-rc,.work/settings"` and the system discovers all well-known dotfiles automatically **plus** includes the user-specified custom paths. The result is a union of auto-discovered and explicitly specified dotfiles with no duplicates.

**Why this priority**: Power users will have custom/non-standard dotfiles that no built-in list could predict. They need to augment automatic discovery with their own paths, just as they might add a custom Homebrew tap.

**Independent Test**: Can be tested by running capture with `--dotfiles` pointing to a custom file and verifying both auto-discovered and custom dotfiles appear in the output.

**Acceptance Scenarios**:

1. **Given** a home directory contains `.zshrc` and a custom file `.my-custom-rc`, **When** the user runs `macsetup capture --dotfiles ".my-custom-rc"`, **Then** the captured config includes both `.zshrc` (auto-discovered) and `.my-custom-rc` (explicitly specified).
2. **Given** a user specifies `--dotfiles ".zshrc"` and `.zshrc` is also auto-discovered, **When** capture runs, **Then** `.zshrc` appears only once in the output (no duplicates).

---

### User Story 3 - Reviewing Discovered Dotfiles Before Capture (Priority: P3)

A user wants to see which dotfiles would be captured before committing. They run `macsetup capture` in verbose mode and the system lists all auto-discovered dotfiles alongside any explicit ones, allowing the user to review. They can then re-run with `--exclude-dotfiles` or `--skip-dotfiles` to adjust.

**Why this priority**: Transparency builds trust. Users who are new to the tool or cautious about what gets captured need visibility into what the auto-discovery found before it copies files.

**Independent Test**: Can be tested by running capture with a dry-run/verbose flag and verifying the output lists discovered dotfiles without actually copying them.

**Acceptance Scenarios**:

1. **Given** a home directory with multiple well-known dotfiles, **When** the user runs `macsetup capture` in verbose mode, **Then** the output lists each discovered dotfile as it is found (e.g., "Discovered: .zshrc", "Discovered: .gitconfig").
2. **Given** a user runs `macsetup capture --skip-dotfiles`, **When** capture completes, **Then** no dotfile discovery or capture occurs.

---

### User Story 4 - Excluding Specific Dotfiles from Discovery (Priority: P3)

A user wants automatic discovery but needs to exclude certain sensitive or irrelevant files. They can specify exclusions so that auto-discovery skips those paths.

**Why this priority**: Some dotfiles may contain secrets or be machine-specific (e.g., `.ssh/config` with host-specific entries). Users need a way to opt out of specific files while still benefiting from auto-discovery.

**Acceptance Scenarios**:

1. **Given** a home directory with `.zshrc` and `.ssh/config`, **When** the user runs `macsetup capture --exclude-dotfiles ".ssh/config"`, **Then** `.zshrc` is captured but `.ssh/config` is not.

---

### Edge Cases

- What happens when a dotfile from the known list is a symlink pointing to a file outside the home directory? The system should resolve and capture the target content (existing behavior in the dotfiles adapter).
- What happens when a dotfile from the known list is a directory (e.g., `.config/nvim/`)? The system should skip directories and only capture individual files.
- What happens when a dotfile exists but is not readable (permission denied)? The system should skip it, log a warning, and continue capturing other files.
- What happens when the known dotfiles list itself needs updating? The list should be maintainable as data (not hardcoded in logic) so users or contributors can extend it.
- What happens when a dotfile is extremely large (e.g., a `.zsh_history` with millions of lines)? The system should have a sensible size limit and skip files that exceed it, with a warning.
- What happens when a user runs capture without `--include-sensitive` but has `.ssh/config` on disk? The file is silently skipped (not captured, no warning) because sensitive paths are opt-in by design.

## Clarifications

### Session 2026-02-12

- Q: Should the registry handle security-sensitive dotfile paths (`.ssh/config`, `.aws/credentials`, etc.) differently from safe configs? → A: Include sensitive paths in the registry but mark them "opt-in only" (excluded by default). Provide a single CLI flag to include all sensitive dotfiles at once.
- Q: Should auto-discovery be always on by default, or should there be a way to disable it while still allowing explicit `--dotfiles`? → A: Auto-discovery is always on by default. `--skip-dotfiles` is the only way to disable all dotfile capture (matches Homebrew/MAS pattern). No separate `--no-auto-discover` flag.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a curated registry of well-known dotfile paths (relative to `$HOME`) that are commonly used on macOS, organized by category (shell, git, editor, terminal, etc.). Each entry MUST be classified as either "default" (included in auto-discovery) or "sensitive" (excluded from auto-discovery unless explicitly opted in).
- **FR-002**: During capture, the system MUST automatically scan for and detect the presence of all dotfiles in the known registry without requiring the user to specify them.
- **FR-003**: The system MUST merge auto-discovered dotfiles with any user-specified `--dotfiles` paths, producing a de-duplicated list.
- **FR-004**: The system MUST skip dotfiles from the registry that do not exist on the current machine (no errors for missing files).
- **FR-005**: The system MUST skip files that are unreadable (permissions issues) and report a warning rather than failing the entire capture.
- **FR-006**: The system MUST skip directories encountered during discovery; only regular files and symlinks to files are captured.
- **FR-007**: The system MUST skip files that exceed a reasonable size threshold (default: 1 MB) to avoid capturing history files or binary data, with a warning message.
- **FR-008**: Users MUST be able to exclude specific dotfile paths from auto-discovery via a CLI flag (`--exclude-dotfiles`).
- **FR-009**: The `--skip-dotfiles` flag MUST continue to disable all dotfile capture, including auto-discovery.
- **FR-010**: The system MUST report discovered dotfiles during capture progress (consistent with existing Homebrew/MAS progress reporting).
- **FR-011**: The known dotfile registry MUST include at minimum: shell configs (`.bashrc`, `.bash_profile`, `.zshrc`, `.zshenv`, `.zprofile`), git (`.gitconfig`, `.gitignore_global`), editor configs (`.vimrc`, `.config/nvim/init.vim`, `.config/nvim/init.lua`), terminal (`.config/starship.toml`, `.tmux.conf`), and tool configs (`.config/gh/config.yml`, `.npmrc`, `.gemrc`).
- **FR-012**: Users MUST be able to include all sensitive dotfiles in auto-discovery via a single CLI flag (`--include-sensitive`). When this flag is set, sensitive registry entries are discovered alongside default entries.
- **FR-013**: Sensitive dotfile paths in the registry MUST include at minimum: `.ssh/config`, `.aws/credentials`, `.aws/config`, `.gnupg/` files, `.netrc`, and `.env`.

### Key Entities

- **Dotfile Registry**: A structured collection of known dotfile paths organized by category. Each entry includes the path relative to `$HOME` and its category label. This registry is the data source for auto-discovery.
- **Discovered Dotfile**: A dotfile that was found on disk via the registry scan. It carries the same attributes as the existing `Dotfile` entity (path, mode, template flag) and is indistinguishable from manually-specified dotfiles once captured.

## Assumptions

- Auto-discovery is always enabled during capture. There is no flag to disable auto-discovery while keeping explicit `--dotfiles`. Users who want no dotfiles at all use `--skip-dotfiles`. This is a deliberate behavior change: previously, omitting `--dotfiles` meant zero dotfiles captured; now it means all known dotfiles are discovered automatically.
- The known dotfile registry will be bundled with the tool and updated through normal release cycles. It does not need to be user-editable at runtime (beyond the `--dotfiles`, `--exclude-dotfiles`, and `--include-sensitive` flags).
- The default mode for auto-discovered dotfiles is `symlink` (consistent with the existing `Dotfile` model default).
- Template processing (`template: true`) will not be automatically applied to discovered dotfiles; it remains a manual opt-in per dotfile.
- The size threshold for skipping large files defaults to 1 MB and is not configurable via CLI in the initial release.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can capture their dotfile configuration with zero manual path specification — running `macsetup capture` with no flags discovers and captures all common dotfiles present on the machine.
- **SC-002**: The capture experience for dotfiles is consistent with Homebrew and MAS: the user does not need to enumerate individual items for the system to find them.
- **SC-003**: On a typical macOS developer machine, the auto-discovery completes within 500ms (consistent with the project's performance constraint for local operations).
- **SC-004**: Users retain full control: they can add custom dotfiles, exclude specific ones, or skip dotfile capture entirely.
- **SC-005**: No dotfile is silently captured without being reported in the capture output — every discovered file is visible in verbose/progress output.
