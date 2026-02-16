# Tasks: iCloud Config Storage

**Input**: Design documents from `/specs/003-icloud-config-storage/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli-contract.md

**Tests**: Included per Constitution Principle I (Test-First Development is non-negotiable).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create new module files and establish test scaffolding

- [ ] T001 [P] Create iCloud adapter module at src/macsetup/adapters/icloud.py with ICloudAdapter class skeleton extending Adapter base class (is_available, get_tool_name methods)
- [ ] T002 [P] Create init service module at src/macsetup/services/init.py with InitService class skeleton
- [ ] T003 [P] Create test file at tests/unit/test_icloud.py with test class scaffolding for ICloudAdapter
- [ ] T004 [P] Create test file at tests/unit/test_init.py with test class scaffolding for InitService

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: iCloud detection and pointer file resolution — MUST complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] Write tests for iCloud Drive path resolution and availability detection in tests/unit/test_icloud.py: test get_icloud_drive_path() returns correct Path, test is_icloud_available() returns True when dir exists, test is_icloud_available() returns False when dir absent
- [ ] T006 [P] Write tests for pointer file reading in tests/unit/test_cli.py: test get_config_dir() reads pointer file when present, test get_config_dir() returns default when pointer absent, test get_config_dir() CLI flag overrides pointer, test get_config_dir() env var overrides pointer, test get_config_dir() errors when pointer references nonexistent path

### Implementation for Foundational

- [ ] T007 [P] Implement get_icloud_drive_path() and is_icloud_available() in src/macsetup/adapters/icloud.py using Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" with is_dir() check per research.md
- [ ] T008 Implement pointer file reading in get_config_dir() in src/macsetup/cli.py: read ~/.config/macsetup/config-dir, validate path is absolute and exists, return path if valid; maintain precedence order: CLI flag > env var > pointer > default per data-model.md resolution order
- [ ] T009 Implement ConfigDirError for unreachable pointer path in src/macsetup/cli.py with error message and remediation suggestions per contracts/cli-contract.md error output format. Wire a ConfigDirError catch in main() so that when get_config_dir() raises, the error is formatted per the contract's "pointer to unreachable path" output and exits with code 1. Note: the init command must be exempted from this check (see T016).

**Checkpoint**: Pointer file resolution works, iCloud detection works. All existing commands still function normally (no pointer file = no behavior change).

---

## Phase 3: User Story 1 - Initialize Config Storage in iCloud (Priority: P1) MVP

**Goal**: User runs `macsetup init --icloud` on a fresh machine (no existing local config) and all subsequent commands use the iCloud location automatically.

**Independent Test**: Run `macsetup init --icloud`, verify pointer file is created, verify `macsetup init --status` shows iCloud storage.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Write tests for InitService.init_icloud() fresh case in tests/unit/test_init.py: test creates iCloud macsetup dir, test writes pointer file, test errors when iCloud unavailable with remediation message
- [ ] T011 [P] [US1] Write tests for InitService.status() in tests/unit/test_init.py: test returns "local" when no pointer file, test returns "icloud" with path when pointer exists
- [ ] T012 [P] [US1] Write tests for cmd_init in tests/unit/test_cli.py: test --icloud flag routes to InitService.init_icloud(), test --status flag routes to InitService.status(), test --json flag produces JSON output, test --quiet suppresses output, test exit code 1 when iCloud unavailable

### Implementation for User Story 1

- [ ] T013 [US1] Implement pointer file write and delete utilities in src/macsetup/cli.py (co-located with pointer file reading in get_config_dir): write_pointer_file(pointer_path, target_dir) writes absolute path to file, delete_pointer_file(pointer_path) removes pointer file. These are NOT iCloud-specific — the pointer mechanism is general config directory indirection — so they belong alongside the read logic, not in the iCloud adapter.
- [ ] T014 [US1] Implement InitService.init_icloud() for fresh case in src/macsetup/services/init.py: check iCloud available via ICloudAdapter, create iCloud macsetup dir, write pointer file, return result with storage type and path
- [ ] T015 [US1] Implement InitService.status() in src/macsetup/services/init.py: check if pointer file exists, read current storage location, check iCloud availability, return status dict per contracts/cli-contract.md JSON format
- [ ] T016 [US1] Implement cmd_init() handler in src/macsetup/cli.py: dispatch to InitService based on flags, format human/JSON output per contracts/cli-contract.md, set exit codes (0=success, 1=iCloud unavailable, 2=conflict). IMPORTANT: Update main() to bypass config dir validation (ConfigDirError) when the command is "init" — init must work before a config dir or pointer file exists, and init --status should not fail if the pointer references a missing path. The init command handles its own path resolution via InitService.
- [ ] T017 [US1] Add init subcommand parser to create_parser() in src/macsetup/cli.py: --icloud flag, --local flag, --status flag, --force flag, --quiet/--json global flags, --help text per contracts/cli-contract.md usage section

**Checkpoint**: `macsetup init --icloud` works on a fresh machine (no existing config). `macsetup init --status` reports current storage. All existing commands transparently use iCloud when pointer is set.

---

## Phase 4: User Story 2 - Migrate Existing Config to iCloud (Priority: P2)

**Goal**: User with existing local config runs `macsetup init --icloud` and their config is moved to iCloud automatically.

**Independent Test**: Create a config locally, run `macsetup init --icloud`, verify files moved to iCloud, local files deleted, pointer file created.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US2] Write tests for InitService.init_icloud() migration case in tests/unit/test_init.py: test moves config.yaml to iCloud dir, test moves dotfiles/ directory tree to iCloud dir, test deletes local files after copy, test preserves file contents during migration, test pointer file is written after move
- [ ] T019 [P] [US2] Write tests for conflict detection in tests/unit/test_init.py: test errors when both local and iCloud config.yaml exist (no --force), test --force overwrites iCloud config with local, test error message includes both config paths and timestamps per contracts/cli-contract.md conflict output

### Implementation for User Story 2

- [ ] T020 [US2] Implement migration logic in InitService.init_icloud() in src/macsetup/services/init.py: detect existing local config (config.yaml in default dir), copy config.yaml and dotfiles/ to iCloud dir using shutil, delete local originals after successful copy, write pointer file
- [ ] T021 [US2] Implement conflict detection in InitService.init_icloud() in src/macsetup/services/init.py: check if iCloud macsetup/config.yaml already exists, check if local config.yaml exists, if both exist and no --force: return error with exit code 2, if --force: overwrite iCloud with local then delete local
- [ ] T022 [US2] Update cmd_init() in src/macsetup/cli.py to handle migration and conflict output: display file-by-file progress during migration, display conflict error with remediation per contracts/cli-contract.md, set exit code 2 for conflict

**Checkpoint**: Existing users can migrate to iCloud with a single command. Conflicts are detected and reported clearly.

---

## Phase 5: User Story 3 - Restore Config on a New Mac via iCloud (Priority: P2)

**Goal**: User sets up a new Mac, signs into iCloud, and runs `macsetup init --icloud` to detect and use the existing iCloud config.

**Independent Test**: Place a valid config.yaml in the iCloud macsetup dir, run `macsetup init --icloud`, verify pointer is set and `macsetup preview` reads from iCloud.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US3] Write tests for InitService.init_icloud() existing iCloud config case in tests/unit/test_init.py: test detects existing config.yaml in iCloud dir, test writes pointer file without moving/copying anything, test returns success with storage type "icloud", test reports existing config summary (profile name)
- [ ] T024 [P] [US3] Write tests for end-to-end flow in tests/unit/test_init.py: test init_icloud with existing iCloud config then get_config_dir resolves to iCloud path

### Implementation for User Story 3

- [ ] T025 [US3] Add existing iCloud config detection to InitService.init_icloud() in src/macsetup/services/init.py: when no local config exists but iCloud macsetup/config.yaml exists, write pointer file to use existing iCloud config, load config to report summary (profile name, counts)
- [ ] T026 [US3] Update cmd_init() output in src/macsetup/cli.py for existing iCloud config case: display "Found existing configuration in iCloud Drive" message with config summary per contracts/cli-contract.md

**Checkpoint**: New Mac users can connect to their synced config with one command. Full restore flow works: init --icloud → setup.

---

## Phase 6: User Story 4 - Revert to Local Storage (Priority: P3)

**Goal**: User reverts from iCloud back to local storage with `macsetup init --local`.

**Independent Test**: Init iCloud storage, run `macsetup init --local`, verify config copied to local, pointer removed, iCloud copy untouched.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T027 [P] [US4] Write tests for InitService.init_local() in tests/unit/test_init.py: test copies config.yaml from iCloud to default local dir, test copies dotfiles/ from iCloud to default local dir, test deletes pointer file, test does NOT delete iCloud copy, test errors when not currently using iCloud (no pointer file)
- [ ] T028 [P] [US4] Write tests for cmd_init --local in tests/unit/test_cli.py: test --local flag routes to InitService.init_local(), test human output matches contracts/cli-contract.md, test JSON output format, test exit code 1 when no pointer file exists

### Implementation for User Story 4

- [ ] T029 [US4] Implement InitService.init_local() in src/macsetup/services/init.py: read pointer file to find current iCloud path, copy config.yaml and dotfiles/ from iCloud to default local dir, delete pointer file, return result with files_copied count, error if no pointer file exists
- [ ] T030 [US4] Wire cmd_init --local in src/macsetup/cli.py: route --local flag to InitService.init_local(), display file-by-file copy progress, show note about iCloud copy not being deleted per contracts/cli-contract.md

**Checkpoint**: Users can freely switch between iCloud and local storage without data loss.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, eviction/conflict detection, documentation

- [ ] T031 [P] Write tests for file eviction detection in tests/unit/test_icloud.py: test is_file_evicted() returns True when SF_DATALESS flag set, test is_file_evicted() returns False for local files, test fallback heuristic (st_blocks==0, st_size>0)
- [ ] T032 [P] Write tests for conflict file detection in tests/unit/test_icloud.py: test find_conflict_files() detects "config 2.yaml" pattern, test find_conflict_files() ignores non-conflict files
- [ ] T033 [P] Implement is_file_evicted() in src/macsetup/adapters/icloud.py using stat.SF_DATALESS (0x40000000) flag check with st_blocks==0 heuristic fallback per research.md
- [ ] T034 [P] Implement find_conflict_files() in src/macsetup/adapters/icloud.py using regex pattern `{basename} {N}.{ext}` where N >= 2 per research.md
- [ ] T035 Add eviction warning to get_config_dir() in src/macsetup/cli.py: when pointer references iCloud path, check config.yaml for eviction, warn user if files are cloud-only with suggestion to wait for sync
- [ ] T036 Add conflict file warning to cmd_init() in src/macsetup/cli.py: after successful init, scan iCloud macsetup dir for conflict files, warn user if any detected
- [ ] T037 Verify --help output for init command covers all options and matches contracts/cli-contract.md usage section
- [ ] T038 Run full test suite and verify all existing tests still pass (no regressions from get_config_dir changes)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP delivery point
- **US2 (Phase 4)**: Depends on Phase 3 (extends init_icloud with migration)
- **US3 (Phase 5)**: Depends on Phase 3 (extends init_icloud with detection)
- **US4 (Phase 6)**: Depends on Phase 2 + T013 from Phase 3 (init_local needs pointer file write/delete utilities)
- **Polish (Phase 7)**: Depends on Phases 3-6 being complete

### User Story Dependencies

- **US1 (P1)**: Foundational → US1 (core init flow, MVP)
- **US2 (P2)**: US1 → US2 (migration extends fresh init)
- **US3 (P2)**: US1 → US3 (existing config detection extends fresh init)
- **US4 (P3)**: Foundational + T013 → US4 (revert needs pointer write/delete utilities from T013)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Adapter/utility methods before service logic
- Service logic before CLI wiring
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1: All 4 setup tasks (T001-T004) can run in parallel
- Phase 2: Test tasks T005-T006 can run in parallel; implementations T007-T008 can run in parallel
- Phase 3: Test tasks T010-T012 can run in parallel
- Phase 4: Test tasks T018-T019 can run in parallel
- Phase 5: Test tasks T023-T024 can run in parallel
- Phase 6: Test tasks T027-T028 can run in parallel
- Phase 7: Tasks T031-T034 can all run in parallel (different methods in same file, but independent)
- **US4 can run in parallel with US2/US3** after T013 (pointer utilities) from Phase 3 is complete — US4 depends on Foundational + T013, not the full US1

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together:
Task: "Write tests for InitService.init_icloud() fresh case in tests/unit/test_init.py"
Task: "Write tests for InitService.status() in tests/unit/test_init.py"
Task: "Write tests for cmd_init in tests/unit/test_cli.py"

# After tests written, launch parallel adapter + service work:
Task: "Implement pointer file write/delete in src/macsetup/adapters/icloud.py"
# (then sequentially)
Task: "Implement InitService.init_icloud() in src/macsetup/services/init.py"
Task: "Implement cmd_init() in src/macsetup/cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (create module files)
2. Complete Phase 2: Foundational (iCloud detection + pointer resolution)
3. Complete Phase 3: User Story 1 (fresh init + status)
4. **STOP and VALIDATE**: `macsetup init --icloud` works, `init --status` works, all existing commands unaffected
5. Deploy/PR if ready

### Incremental Delivery

1. Setup + Foundational → Pointer resolution works, iCloud detected
2. Add US1 → Fresh init works → **PR 1** (MVP)
3. Add US2 → Migration works → **PR 2**
4. Add US3 → Existing config detected → **PR 3** (can combine with US2 if small)
5. Add US4 → Revert works → **PR 4**
6. Polish → Eviction/conflict warnings → **PR 5**

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD is mandatory per Constitution Principle I: write tests first, verify they fail, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The iCloud adapter (icloud.py) uses only stdlib modules (os, stat, shutil, pathlib) — no new dependencies
