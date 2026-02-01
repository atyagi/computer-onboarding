# Tasks: macOS Configuration Sync CLI

**Input**: Design documents from `/specs/001-macos-config-sync/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: REQUIRED per constitution (Test-First Development is NON-NEGOTIABLE)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4)
- Paths follow plan.md: `src/macsetup/`, `tests/`, `bin/`

---

## Phase 1: Setup (Project Infrastructure)

**Purpose**: Initialize Python project with uv, create package structure

- [x] T001 Create `.python-version` file with Python 3.14
- [x] T002 Create `pyproject.toml` with project metadata and dependencies (PyYAML, jsonschema, pytest, ruff, bats)
- [x] T003 Run `uv sync` to generate `uv.lock` and install dependencies
- [x] T004 [P] Create package structure: `src/macsetup/__init__.py`, `src/macsetup/__main__.py`
- [x] T005 [P] Create test directories: `tests/unit/`, `tests/integration/`, `tests/contract/`, `tests/bats/`
- [x] T006 [P] Create `schemas/` directory and copy `config.schema.json` from contracts
- [x] T007 [P] Configure ruff in `pyproject.toml` (linting + formatting)
- [x] T008 Create `bin/macsetup` bash wrapper script with shebang and `uv run` invocation

---

## Phase 2: Foundational (Core Models & CLI Framework)

**Purpose**: Shared infrastructure ALL user stories depend on - MUST complete before stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundation

- [x] T009 [P] Unit test for Configuration model in `tests/unit/test_models.py`
- [x] T010 [P] Unit test for Metadata model in `tests/unit/test_models.py`
- [x] T011 [P] Unit test for Profile model in `tests/unit/test_models.py`
- [x] T012 [P] Contract test for config schema validation in `tests/contract/test_config_schema.py`

### Implementation for Foundation

- [x] T013 [P] Create Configuration dataclass in `src/macsetup/models/config.py`
- [x] T014 [P] Create Metadata dataclass in `src/macsetup/models/config.py`
- [x] T015 [P] Create Profile dataclass in `src/macsetup/models/config.py`
- [x] T016 [P] Create Applications, HomebrewApps, MacApp, ManualApp dataclasses in `src/macsetup/models/config.py`
- [x] T017 [P] Create Dotfile dataclass in `src/macsetup/models/config.py`
- [x] T018 [P] Create Preference dataclass in `src/macsetup/models/config.py`
- [x] T019 Create schema validation module in `src/macsetup/models/schema.py` (load JSON schema, validate configs)
- [x] T020 Create YAML config loader/saver in `src/macsetup/models/config.py` (parse YAML to dataclasses)
- [x] T021 Create CLI framework with argparse in `src/macsetup/cli.py` (main parser, subcommands skeleton, global options)
- [x] T022 [P] Create base adapter interface in `src/macsetup/adapters/__init__.py`
- [x] T023 Implement `--help`, `--version`, `--config-dir`, `--json`, `--quiet`, `--verbose` global options in `src/macsetup/cli.py`
- [x] T024 [P] Bats test for bash wrapper in `tests/bats/test_wrapper.bats`

**Checkpoint**: Foundation ready - CLI runs with `--help`, models load/save YAML configs

---

## Phase 3: User Story 1 - Initial Machine Setup (Priority: P1) 🎯 MVP

**Goal**: Run `macsetup setup` to install all apps, dotfiles, and preferences from config

**Independent Test**: Run setup on fresh macOS (or VM) and verify all items installed

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T025 [P] [US1] Unit test for SetupState model in `tests/unit/test_models.py`
- [x] T026 [P] [US1] Unit test for FailedItem model in `tests/unit/test_models.py`
- [x] T027 [P] [US1] Unit test for homebrew adapter (mocked) in `tests/unit/test_adapters.py`
- [x] T028 [P] [US1] Unit test for mas adapter (mocked) in `tests/unit/test_adapters.py`
- [x] T029 [P] [US1] Unit test for defaults adapter (mocked) in `tests/unit/test_adapters.py`
- [x] T030 [P] [US1] Unit test for dotfiles adapter (mocked) in `tests/unit/test_adapters.py`
- [x] T031 [P] [US1] Unit test for setup service in `tests/unit/test_setup.py`
- [ ] T032 [US1] Integration test for setup command in `tests/integration/test_setup.py`

### Implementation for User Story 1

- [x] T033 [P] [US1] Create SetupState dataclass in `src/macsetup/models/config.py`
- [x] T034 [P] [US1] Create FailedItem dataclass in `src/macsetup/models/config.py`
- [x] T035 [P] [US1] Implement homebrew adapter in `src/macsetup/adapters/homebrew.py` (tap, install formula, install cask, check installed)
- [x] T036 [P] [US1] Implement mas adapter in `src/macsetup/adapters/mas.py` (install, list installed, check signed in)
- [x] T037 [P] [US1] Implement defaults adapter in `src/macsetup/adapters/defaults.py` (read, write, import domain)
- [x] T038 [P] [US1] Implement dotfiles adapter in `src/macsetup/adapters/dotfiles.py` (symlink, copy, check exists)
- [x] T039 [US1] Implement setup service in `src/macsetup/services/setup.py` (orchestrate adapters, track state, handle failures)
- [x] T040 [US1] Add idempotency check to setup service (skip already-installed items)
- [x] T041 [US1] Add resume capability using SetupState in `src/macsetup/services/setup.py`
- [x] T042 [US1] Add progress indicator for setup operations in `src/macsetup/services/setup.py`
- [x] T043 [US1] Add SIGINT handling for graceful interruption in `src/macsetup/services/setup.py`
- [x] T044 [US1] Wire setup command to CLI in `src/macsetup/cli.py` (--profile, --resume, --force, --no-dotfiles, --no-preferences)
- [x] T045 [US1] Add JSON output support for setup command in `src/macsetup/cli.py`
- [x] T046 [US1] Add error messages with remediation suggestions for common failures

**Checkpoint**: `macsetup setup` works - installs apps, dotfiles, preferences from config.yaml

---

## Phase 4: User Story 2 - Configuration Capture (Priority: P2)

**Goal**: Run `macsetup capture` to snapshot current machine state to config file

**Independent Test**: Run capture and verify config.yaml accurately reflects installed apps/dotfiles/prefs

### Tests for User Story 2

- [ ] T047 [P] [US2] Unit test for capture homebrew (mocked) in `tests/unit/test_capture.py`
- [ ] T048 [P] [US2] Unit test for capture mas (mocked) in `tests/unit/test_capture.py`
- [ ] T049 [P] [US2] Unit test for capture dotfiles (mocked) in `tests/unit/test_capture.py`
- [ ] T050 [P] [US2] Unit test for capture preferences (mocked) in `tests/unit/test_capture.py`
- [ ] T051 [P] [US2] Unit test for capture service in `tests/unit/test_capture.py`
- [ ] T052 [US2] Integration test for capture command in `tests/integration/test_capture.py`

### Implementation for User Story 2

- [ ] T053 [P] [US2] Add list_formulas, list_casks, list_taps to homebrew adapter in `src/macsetup/adapters/homebrew.py`
- [ ] T054 [P] [US2] Add list_apps to mas adapter in `src/macsetup/adapters/mas.py`
- [ ] T055 [P] [US2] Add export_domain to defaults adapter in `src/macsetup/adapters/defaults.py`
- [ ] T056 [P] [US2] Add copy_to_config, list_tracked to dotfiles adapter in `src/macsetup/adapters/dotfiles.py`
- [ ] T057 [US2] Implement capture service in `src/macsetup/services/capture.py` (orchestrate adapters, build config)
- [ ] T058 [US2] Add metadata population (hostname, macOS version, timestamp) to capture service
- [ ] T059 [US2] Wire capture command to CLI in `src/macsetup/cli.py` (--profile, --dotfiles, --preferences, --skip-*)
- [ ] T060 [US2] Add JSON output support for capture command
- [ ] T061 [US2] Create dotfiles storage directory structure in config-dir

**Checkpoint**: `macsetup capture` works - creates config.yaml with apps, dotfiles, preferences

---

## Phase 5: User Story 3 - Ongoing Configuration Sync (Priority: P3)

**Goal**: Run `macsetup sync start` to automatically capture changes periodically

**Independent Test**: Install new app, wait for sync interval, verify config updated

### Tests for User Story 3

- [ ] T062 [P] [US3] Unit test for sync service (mocked) in `tests/unit/test_sync.py`
- [ ] T063 [P] [US3] Unit test for file watcher in `tests/unit/test_sync.py`
- [ ] T064 [US3] Integration test for sync daemon in `tests/integration/test_sync.py`

### Implementation for User Story 3

- [ ] T065 [US3] Implement sync service in `src/macsetup/services/sync.py` (periodic capture, file watching)
- [ ] T066 [US3] Add daemon mode with interval scheduling in `src/macsetup/services/sync.py`
- [ ] T067 [US3] Add dotfile change watcher using filesystem events in `src/macsetup/services/sync.py`
- [ ] T068 [US3] Add PID file management for daemon in `src/macsetup/services/sync.py`
- [ ] T069 [US3] Wire sync subcommands to CLI in `src/macsetup/cli.py` (start, stop, status, now)
- [ ] T070 [US3] Add --interval and --watch options for sync start
- [ ] T071 [US3] Add SIGHUP handling (daemon continues) in sync service

**Checkpoint**: `macsetup sync start/stop/status` works - daemon captures changes automatically

---

## Phase 6: User Story 4 - Preview and Selective Apply (Priority: P4)

**Goal**: Run `macsetup preview` to see what would change; use profiles for different contexts

**Independent Test**: Run preview, verify matches config; run setup with --exclude, verify items skipped

### Tests for User Story 4

- [ ] T072 [P] [US4] Unit test for preview service in `tests/unit/test_preview.py`
- [ ] T073 [P] [US4] Unit test for profile inheritance in `tests/unit/test_models.py`
- [ ] T074 [P] [US4] Unit test for diff calculation in `tests/unit/test_preview.py`
- [ ] T075 [US4] Integration test for preview command in `tests/integration/test_preview.py`

### Implementation for User Story 4

- [ ] T076 [US4] Implement preview service in `src/macsetup/services/preview.py` (list what would be installed)
- [ ] T077 [US4] Add diff mode to preview service (compare config vs current state)
- [ ] T078 [US4] Implement profile inheritance resolution in `src/macsetup/models/config.py`
- [ ] T079 [US4] Wire preview command to CLI in `src/macsetup/cli.py` (--profile, --diff)
- [ ] T080 [US4] Add --include/--exclude to setup command in `src/macsetup/cli.py`
- [ ] T081 [US4] Wire profile subcommands to CLI in `src/macsetup/cli.py` (list, show, create, delete, diff)
- [ ] T082 [US4] Add JSON output support for preview and profile commands
- [ ] T083 [US4] Implement validate command in `src/macsetup/cli.py` (--strict option)

**Checkpoint**: `macsetup preview` and `macsetup profile` commands work; selective setup works

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, edge cases, hardening

- [ ] T084 [P] Add --help text for all commands and options in `src/macsetup/cli.py`
- [ ] T085 [P] Create README.md with quickstart instructions at repository root
- [ ] T086 [P] Add Homebrew bootstrap (install if missing) in setup service
- [ ] T087 [P] Add mas-cli bootstrap (install via brew if missing) in setup service
- [ ] T088 Add macOS version compatibility check and warning in `src/macsetup/cli.py`
- [ ] T089 Add manual app listing at end of setup (apps requiring manual intervention)
- [ ] T090 Add network error handling with retry for setup operations
- [ ] T091 [P] Add comprehensive error messages for all exit codes
- [ ] T092 Run full test suite and fix any failures
- [ ] T093 Run quickstart.md validation (manual test of documented workflow)
- [ ] T094 Performance validation: verify <500ms for local operations, <100MB memory

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Phase 2 completion
  - Stories can proceed in priority order (P1 → P2 → P3 → P4)
  - Or in parallel if team capacity allows
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US1 (Setup) | Phase 2 only | Phase 2 complete |
| US2 (Capture) | Phase 2 only | Phase 2 complete |
| US3 (Sync) | Phase 2 + US2 (reuses capture) | Phase 4 complete |
| US4 (Preview) | Phase 2 + US1 (reuses adapters) | Phase 3 complete |

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Adapters before services (adapters are mocked in tests)
3. Services before CLI wiring
4. Core functionality before options/flags
5. Verify tests pass before moving to next story

### Parallel Opportunities by Phase

**Phase 1**: T004, T005, T006, T007 can run in parallel
**Phase 2**: T009-T012 (tests), T013-T018 (models), T022, T024 can run in parallel
**Phase 3 (US1)**: T025-T032 (tests), T033-T038 (adapters) can run in parallel
**Phase 4 (US2)**: T047-T052 (tests), T053-T056 (adapters) can run in parallel
**Phase 5 (US3)**: T062-T063 (tests) can run in parallel
**Phase 6 (US4)**: T072-T074 (tests) can run in parallel
**Phase 7**: T084-T087, T091 can run in parallel

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# Launch all US1 tests in parallel:
Task: "[US1] Unit test for SetupState model"
Task: "[US1] Unit test for FailedItem model"
Task: "[US1] Unit test for homebrew adapter (mocked)"
Task: "[US1] Unit test for mas adapter (mocked)"
Task: "[US1] Unit test for defaults adapter (mocked)"
Task: "[US1] Unit test for dotfiles adapter (mocked)"
Task: "[US1] Unit test for setup service"

# After tests written and failing, launch adapters in parallel:
Task: "[US1] Implement homebrew adapter"
Task: "[US1] Implement mas adapter"
Task: "[US1] Implement defaults adapter"
Task: "[US1] Implement dotfiles adapter"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T024)
3. Complete Phase 3: User Story 1 (T025-T046)
4. **STOP and VALIDATE**: Run `macsetup setup` on test config
5. Deploy/demo - core value proposition achieved!

### Incremental Delivery

1. MVP: Setup + Foundational + US1 → `macsetup setup` works
2. +US2: Add capture → `macsetup capture` works → can now capture AND setup
3. +US3: Add sync → `macsetup sync` works → automated background sync
4. +US4: Add preview/profiles → full feature set complete

### Task Counts by Story

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Setup | 8 | 4 |
| Foundational | 16 | 11 |
| US1 (Setup) | 22 | 10 |
| US2 (Capture) | 15 | 8 |
| US3 (Sync) | 10 | 2 |
| US4 (Preview) | 12 | 4 |
| Polish | 11 | 5 |
| **Total** | **94** | **44** |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story (US1, US2, US3, US4)
- Constitution requires TDD - all tests MUST fail before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Each story adds user value without breaking previous stories
