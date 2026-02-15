# Tasks: Automatic Dotfile Discovery

**Input**: Design documents from `/specs/002-auto-dotfile-discovery/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: TDD is mandated by the project constitution (Principle I). Tests are written before implementation in each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: No new project initialization needed — project already exists. This phase verifies existing tests pass before making changes.

- [x] T001 Verify all existing tests pass by running `uv run pytest` and `uv run ruff check .`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the dotfile registry data model that ALL user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundation

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T002 Write registry data integrity tests in tests/unit/test_registry.py: verify KNOWN_DOTFILES contains all required paths from FR-011 and FR-013, all paths are unique, no path starts with `/` or contains `..`, all entries have non-empty category, sensitive entries have `sensitive=True`, default entries have `sensitive=False`

### Implementation for Foundation

- [x] T003 Create DotfileRegistryEntry dataclass and KNOWN_DOTFILES list in src/macsetup/models/registry.py per data-model.md: fields are `path` (str), `category` (str), `sensitive` (bool, default False). Populate with all ~35 entries from research.md (shell, git, editor, terminal, dev-tools as default; ssh, cloud, security, secrets as sensitive)
- [x] T004 Run `uv run pytest tests/unit/test_registry.py` to verify T002 tests pass with T003 implementation

**Checkpoint**: Registry exists, is tested, and contains all required dotfile paths. Foundation ready.

---

## Phase 3: User Story 1 - Automatic Dotfile Detection During Capture (Priority: P1) MVP

**Goal**: Running `macsetup capture` with no `--dotfiles` flag automatically discovers and captures all well-known default dotfiles present on the machine.

**Independent Test**: Run `macsetup capture` on a machine with common dotfiles and verify the resulting config.yaml includes discovered dotfiles without any `--dotfiles` flag.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T005 [P] [US1] Write unit tests for `DotfilesAdapter.discover_dotfiles()` in tests/unit/test_adapters.py: test discovery finds files that exist, skips files that don't exist (FR-004), skips directories (FR-006), skips unreadable files with warning (FR-005), skips files over 1 MB with warning (FR-007), returns list of Dotfile objects, only returns default (non-sensitive) entries when include_sensitive=False
- [x] T006 [P] [US1] Write unit tests for auto-discovery integration in tests/unit/test_capture.py: test that `CaptureService.capture()` calls discovery and includes discovered dotfiles in output, test that `--skip-dotfiles` disables discovery (FR-009), test that empty discovery (no dotfiles found) produces empty list without errors

### Implementation for User Story 1

- [x] T007 [US1] Implement `discover_dotfiles(home: Path, exclude: list[str], include_sensitive: bool) -> list[Dotfile]` method in src/macsetup/adapters/dotfiles.py: iterate KNOWN_DOTFILES registry, filter by sensitive flag, check `Path.exists()` for each, skip directories (`Path.is_file()` or `Path.is_symlink()`), skip unreadable files (catch `PermissionError`), skip files > 1,048,576 bytes (`Path.stat().st_size`), return list of `Dotfile(path=entry.path)` for each found file
- [x] T008 [US1] Modify `CaptureService._capture_dotfiles()` in src/macsetup/services/capture.py to call `self.dotfiles_adapter.discover_dotfiles()` automatically when `skip_dotfiles` is False, passing `home=Path.home()`, `exclude=[]`, `include_sensitive=False`. Use discovered dotfiles as the base list instead of only `self.dotfile_paths`
- [x] T009 [US1] Run `uv run pytest tests/unit/test_adapters.py tests/unit/test_capture.py` to verify all US1 tests pass

**Checkpoint**: `macsetup capture` now auto-discovers dotfiles. US1 acceptance scenarios are met.

---

## Phase 4: User Story 2 - Combining Auto-Discovery with Explicit Dotfiles (Priority: P2)

**Goal**: User-specified `--dotfiles` paths are merged with auto-discovered paths, producing a de-duplicated list.

**Independent Test**: Run `macsetup capture --dotfiles ".my-custom-rc"` and verify both auto-discovered and custom dotfiles appear, with no duplicates.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [US2] Write unit tests for merge and de-duplication in tests/unit/test_capture.py: test that user-specified dotfiles are added to discovered list (FR-003), test that duplicate paths (same path in both discovered and user-specified) appear only once, test that user-specified paths for non-existent files are still attempted (existing behavior preserved)

### Implementation for User Story 2

- [x] T011 [US2] Update `CaptureService._capture_dotfiles()` in src/macsetup/services/capture.py to merge `discovered_dotfiles + self.dotfile_paths` with de-duplication by path. Build a `seen_paths` set, iterate discovered first then user-specified, skip any path already in `seen_paths`
- [x] T012 [US2] Run `uv run pytest tests/unit/test_capture.py` to verify all US2 tests pass alongside existing US1 tests

**Checkpoint**: Auto-discovery and explicit `--dotfiles` work together. US2 acceptance scenarios are met.

---

## Phase 5: User Story 3 - Reviewing Discovered Dotfiles Before Capture (Priority: P3)

**Goal**: Discovered dotfiles are reported via progress callback during capture, consistent with Homebrew/MAS progress output.

**Independent Test**: Run `macsetup capture` (non-quiet, non-json) and verify output lists each discovered dotfile with "Discovered" prefix.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T013 [US3] Write unit tests for discovery progress reporting in tests/unit/test_capture.py: test that progress callback is called for each discovered dotfile with "Discovered" message (FR-010), test that warning messages are reported for skipped files (oversized, unreadable), test that `--skip-dotfiles` produces no discovery progress output

### Implementation for User Story 3

- [x] T014 [US3] Update `CaptureService._capture_dotfiles()` in src/macsetup/services/capture.py to call `self._report_progress()` with "Discovered {path}" for each auto-discovered dotfile, and "[!] Skipped {path} ({reason})" for files skipped due to size or permission issues. Pass warning information from `discover_dotfiles()` return value (extend return type or add a warnings list)
- [x] T015 [US3] Run `uv run pytest tests/unit/test_capture.py` to verify all US3 tests pass alongside US1 and US2 tests

**Checkpoint**: Users see discovery progress in output. US3 acceptance scenarios are met.

---

## Phase 6: User Story 4 - Excluding Specific Dotfiles and Sensitive Opt-In (Priority: P3)

**Goal**: Users can exclude specific dotfiles via `--exclude-dotfiles` and opt in to sensitive dotfiles via `--include-sensitive`.

**Independent Test**: Run `macsetup capture --exclude-dotfiles ".vimrc"` and verify `.vimrc` is not captured. Run `macsetup capture --include-sensitive` and verify sensitive dotfiles are discovered.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T016 [P] [US4] Write unit tests for `--exclude-dotfiles` flag parsing in tests/unit/test_cli.py: test that `--exclude-dotfiles ".vimrc,.tmux.conf"` parses to a list of paths, test that exclusion list is passed through to CaptureService
- [x] T017 [P] [US4] Write unit tests for `--include-sensitive` flag parsing in tests/unit/test_cli.py: test that `--include-sensitive` is a boolean flag, test that it defaults to False, test that the flag value is passed through to CaptureService
- [x] T018 [P] [US4] Write unit tests for exclusion and sensitive filtering in tests/unit/test_adapters.py: test that `discover_dotfiles(exclude=[".vimrc"])` skips `.vimrc` even if present on disk, test that `discover_dotfiles(include_sensitive=True)` includes sensitive entries, test that `discover_dotfiles(include_sensitive=False)` excludes sensitive entries, test that `--exclude-dotfiles` does not affect user-specified `--dotfiles` entries

### Implementation for User Story 4

- [x] T019 [US4] Add `--exclude-dotfiles` and `--include-sensitive` flags to capture subparser in src/macsetup/cli.py: `--exclude-dotfiles` takes comma-separated PATHS metavar, `--include-sensitive` is `store_true` boolean. Parse exclusion list in `cmd_capture()` and pass both values to CaptureService constructor
- [x] T020 [US4] Add `exclude_dotfiles: list[str]` and `include_sensitive: bool` parameters to `CaptureService.__init__()` in src/macsetup/services/capture.py, defaulting to `[]` and `False`. Pass them through to `self.dotfiles_adapter.discover_dotfiles()` call
- [x] T021 [US4] Run `uv run pytest tests/unit/test_cli.py tests/unit/test_adapters.py tests/unit/test_capture.py` to verify all US4 tests pass alongside all previous tests

**Checkpoint**: Users can exclude dotfiles and opt into sensitive ones. US4 acceptance scenarios are met.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, linting, and full test suite verification.

- [x] T022 Run full test suite `uv run pytest` to verify all tests pass across all user stories
- [x] T023 Run `uv run ruff check .` and `uv run ruff format --check .` to verify linting and formatting pass with zero warnings
- [x] T024 Verify `macsetup capture --help` documents `--exclude-dotfiles` and `--include-sensitive` flags
- [x] T025 Run quickstart.md validation: manually verify each command example in specs/002-auto-dotfile-discovery/quickstart.md produces expected behavior
- [x] T026 Verify SC-003 performance: confirm auto-discovery of ~35 registry entries completes within 500ms by timing `discover_dotfiles()` against a real home directory (the implementation performs ~35 `stat()` calls which is well under the threshold)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify existing tests pass
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (registry must exist)
- **US2 (Phase 4)**: Depends on Phase 3 (discovery must work before merge logic)
- **US3 (Phase 5)**: Depends on Phase 3 (discovery must work before progress reporting)
- **US4 (Phase 6)**: Depends on Phase 3 (discovery must work before exclusion filtering)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational phase — no other story dependencies
- **US2 (P2)**: Depends on US1 (merge extends discovery)
- **US3 (P3)**: Depends on US1 (progress reporting extends discovery); can run in parallel with US2
- **US4 (P3)**: Depends on US1 (exclusion filters discovery); can run in parallel with US2 and US3

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Implementation makes tests pass with minimal code
- Verify tests pass before moving to next phase

### Parallel Opportunities

- T005, T006 can run in parallel (different test files)
- T016, T017, T018 can run in parallel (different test concerns/files)
- US3 and US4 can run in parallel after US1 completes (independent concerns)

---

## Parallel Example: User Story 1

```bash
# Launch US1 tests in parallel (different files):
Task: "Write discover_dotfiles() tests in tests/unit/test_adapters.py"
Task: "Write auto-discovery integration tests in tests/unit/test_capture.py"

# Then implement sequentially (adapter before service):
Task: "Implement discover_dotfiles() in src/macsetup/adapters/dotfiles.py"
Task: "Integrate discovery into CaptureService in src/macsetup/services/capture.py"
```

## Parallel Example: User Story 4

```bash
# Launch US4 tests in parallel (different files/concerns):
Task: "Write --exclude-dotfiles flag tests in tests/unit/test_cli.py"
Task: "Write --include-sensitive flag tests in tests/unit/test_cli.py"
Task: "Write exclusion/sensitive filtering tests in tests/unit/test_adapters.py"

# Then implement sequentially (CLI before service wiring):
Task: "Add flags to CLI parser in src/macsetup/cli.py"
Task: "Wire flags through CaptureService in src/macsetup/services/capture.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing tests)
2. Complete Phase 2: Foundational (registry data model)
3. Complete Phase 3: User Story 1 (core auto-discovery)
4. **STOP and VALIDATE**: Test US1 independently — `macsetup capture` discovers dotfiles with no flags

### Incremental Delivery (One PR Per Phase)

1. Phase 1 → Setup verification (PR 1: "Phase 1: Verify existing tests pass")
2. Phase 2 → Foundation ready (PR 2: "Phase 2: Foundational dotfile registry data model")
3. Phase 3 (US1) → Core discovery works (PR 3: "Phase 3: Automatic dotfile detection during capture")
4. Phase 4 (US2) → Merge with explicit dotfiles (PR 4: "Phase 4: Combine auto-discovery with explicit dotfiles")
5. Phase 5 (US3) → Progress reporting (PR 5: "Phase 5: Discovery progress reporting")
6. Phase 6 (US4) → Exclusion and sensitive opt-in (PR 6: "Phase 6: Exclude dotfiles and sensitive opt-in")
7. Phase 7 → Polish and validation (PR 7: "Phase 7: Polish and cross-cutting validation")

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- TDD is mandatory: write tests → verify they fail → implement → verify they pass
- Commit after each phase completes
- Stop at any checkpoint to validate story independently
