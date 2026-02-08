# Test Coverage Analysis

**Date**: 2026-02-08
**Based on**: Latest `main` (commit 1dc33f2)
**Overall coverage**: 75% (362 of 1469 statements missed)
**Tests**: 201 passing, **4 failing**

## Coverage by Module

| Module | Stmts | Miss | Cover | Priority |
|--------|-------|------|-------|----------|
| `adapters/dotfiles.py` | 91 | 66 | **27%** | HIGH |
| `adapters/defaults.py` | 93 | 54 | **42%** | HIGH |
| `adapters/homebrew.py` | 93 | 53 | **43%** | HIGH |
| `models/schema.py` | 25 | 14 | **44%** | HIGH |
| `adapters/mas.py` | 56 | 31 | **45%** | HIGH |
| `services/setup.py` | 244 | 58 | **76%** | HIGH |
| `services/preview.py` | 73 | 13 | 82% | MEDIUM |
| `services/sync.py` | 76 | 12 | 84% | MEDIUM |
| `cli.py` | 444 | 49 | 89% | MEDIUM |
| `models/config.py` | 175 | 6 | 97% | LOW |
| `services/capture.py` | 82 | 1 | 99% | LOW |
| `__main__.py` | 3 | 3 | 0% | LOW |

---

## CRITICAL: 4 Existing Tests Are Broken

Three unit tests in `test_setup.py` and one in `test_sync.py` are failing on the
latest main. These should be fixed immediately before adding new tests.

### Broken: `test_setup_service_installs_taps` and `test_setup_service_installs_casks`

**Root cause:** `SetupService.run()` now calls `_bootstrap_homebrew()` (line 272)
before reaching the mocked adapter methods. `_bootstrap_homebrew()` calls
`subprocess.run(["brew", ...])` directly (line 219), which fails on CI/Linux with
`FileNotFoundError: No such file or directory: 'brew'`. The resulting exception is
caught by the general handler (line 314), which short-circuits before `install_tap`
or `install_cask` is ever called.

**Fix:** These tests need to also mock `_bootstrap_homebrew` (and `_bootstrap_mas`)
or mock `subprocess.run` to prevent the real bootstrap from executing.

### Broken: `test_setup_service_returns_manual_apps`

**Root cause:** Same bootstrap issue — the exception causes `run()` to bail out at
line 314 before reaching the manual apps collection at line 293-294, so
`result.manual_apps` is empty.

### Broken: `test_watcher_reset_clears_changes`

**Root cause:** The test writes to a file twice in rapid succession:
```python
watched_file.write_text("original")   # __init__ calls reset(), records mtime
watched_file.write_text("modified")   # may get same mtime (1-second granularity)
assert watcher.has_changes() is True  # FAILS: mtime unchanged
```

On filesystems with 1-second mtime resolution (common on Linux ext4), both writes
happen within the same second, so `os.path.getmtime()` returns the same value.

**Fix:** Add a `time.sleep(0.05)` before the second write, or use `os.utime()` to
force a different mtime.

---

## Gap 1: Adapter Error Handling (HIGH priority — 27-45% coverage)

All four adapters have the same problem: only the happy path is tested. Every adapter
method has error-handling branches with remediation messages that are completely untested.

### dotfiles.py (27% — worst in codebase)

**Untested methods:**
- `get_tool_name()` (line 18)
- `is_symlink_valid()` — entire method (lines 123-138)
- `copy_to_config()` — entire method (lines 140-179)

**Untested error paths in `symlink()`:**
- Source file doesn't exist → returns failure
- Target already exists with `backup=True` → renames existing file
- Target already exists with `backup=False` → deletes existing file
- Target is an existing symlink → unlinks before re-creating
- `PermissionError`, `FileNotFoundError`, generic `Exception` branches

**Untested error paths in `copy()`:**
- Source file doesn't exist → returns failure
- Target exists with backup → renames
- Target exists without backup → deletes
- `PermissionError`, `FileNotFoundError`, generic `Exception` branches

### homebrew.py (43%)

**Untested methods:**
- `get_tool_name()` (line 22)
- `is_tap_installed()` — lines 88-94
- `list_formulas()` — lines 112-118
- `list_casks()` — lines 120-126
- `list_taps()` — lines 128-134

**Untested error remediation in `install_tap()`:**
- "already tapped" error message
- "invalid tap" / "not found" error message
- Generic error fallback

**Untested error remediation in `install_formula()`:**
- "already installed", "no available formula", "permission denied" branches

**Untested error remediation in `install_cask()`:**
- "already installed", "no available cask", "permission denied", "sha256 mismatch" branches

### mas.py (45%)

**Untested methods:**
- `get_tool_name()` (line 18)
- `list_installed()` — entire method (lines 66-90), including line-parsing logic

**Untested error remediation in `install()`:**
- "not signed in", "not found", "already installed", "purchased" branches

**Untested edge cases:**
- `is_installed()` when exception occurs → returns False
- `is_signed_in()` when "Not signed in" is in output → returns False
- `is_signed_in()` when exception occurs → returns False

### defaults.py (42%)

**Untested methods:**
- `get_tool_name()` (line 18)
- `delete()` — entire method (lines 107-129)
- `export_domain()` — entire method (lines 154-175)

**Untested `write()` type-mapping paths:**
- `value_type="int"` → `-int` flag
- `value_type="float"` → `-float` flag
- `value_type="string"` → `-string` flag
- `value_type="array"` → `-array` flag
- Auto-detect when `value_type=None` (bool, int, float, str inference)
- `CalledProcessError` remediation (domain not found, type mismatch, generic)

**Untested `read()` paths:**
- `key=None` (read entire domain)
- Exception handling → returns None

### Suggested test cases for adapters

```
# homebrew
test_install_tap_returns_error_on_calledprocesserror
test_install_tap_remediation_for_already_tapped
test_install_tap_remediation_for_invalid_tap
test_install_formula_remediation_for_not_found
test_install_cask_remediation_for_sha256_mismatch
test_is_tap_installed
test_list_formulas
test_list_casks
test_list_taps

# dotfiles
test_symlink_returns_error_when_source_missing
test_symlink_backs_up_existing_file
test_symlink_replaces_existing_symlink
test_copy_returns_error_when_source_missing
test_copy_backs_up_existing_file
test_is_symlink_valid_returns_true_for_valid_link
test_is_symlink_valid_returns_false_for_non_symlink
test_copy_to_config_copies_file_to_config_dir
test_copy_to_config_resolves_symlink_source

# mas
test_install_remediation_for_not_signed_in
test_list_installed_parses_mas_output
test_is_signed_in_returns_false_when_not_signed_in

# defaults
test_delete_preference
test_export_domain
test_write_preference_with_int_type
test_write_preference_with_float_type
test_write_preference_with_string_type
test_write_preference_with_array_type
test_write_preference_with_auto_detect
test_read_entire_domain
test_write_remediation_for_domain_not_found
```

---

## Gap 2: Schema Validation Module (HIGH priority — 44% coverage)

`models/schema.py` at 44%. The contract tests in `tests/contract/test_config_schema.py`
validate against the JSON schema directly using jsonschema, but never exercise the
Python wrapper functions in `schema.py`:

- `load_schema()` — loads schema from package resources (untested)
- `validate_config()` — returns list of error strings (untested)
- `is_valid()` — boolean convenience check (untested)
- `validate_config_strict()` — raises `ConfigValidationError` (untested)
- `ConfigValidationError` — custom exception with error list (untested)

These are the functions that `cmd_validate` and other application code actually call.
If they break, the contract tests would still pass.

### Suggested test cases

```
test_load_schema_returns_dict_with_properties
test_validate_config_returns_empty_list_for_valid_config
test_validate_config_returns_errors_for_invalid_config
test_is_valid_returns_true_for_valid_config
test_is_valid_returns_false_for_invalid_config
test_validate_config_strict_raises_on_invalid
test_validate_config_strict_passes_on_valid
test_config_validation_error_contains_error_list
```

---

## Gap 3: Setup Service — Bootstrap & State Management (HIGH priority — 76%)

`services/setup.py` dropped from 81% to 76% due to new untested code.

### Untested: Homebrew/MAS bootstrap (lines 209-245)

- `_bootstrap_homebrew()` — runs Homebrew installer script if brew not found
- `_bootstrap_mas()` — installs mas-cli via Homebrew if not found
- `check_macos_version()` — version compatibility check

These are called early in `run()` and affect every subsequent operation. The fact that
they are untested is the direct cause of the 3 broken unit tests.

### Untested: State persistence for resume (lines 102-157)

- `_load_state()` — loads `.state.json` for resume (0% covered)
- `_save_state()` — saves state to disk (only hit indirectly via failure)
- `_clear_state()` — removes state file on success (not covered)
- `run(resume=True)` — the resume code path (not covered)

### Untested: Interruption and error handling

- Interruption handling — `_interrupted = True` and saving state (lines 297-301)
- `completed_with_errors` status path (lines 307-309)
- General exception handler in `run()` (lines 314-318)

### Suggested test cases

```
# Bootstrap
test_bootstrap_homebrew_skips_when_already_available
test_bootstrap_homebrew_attempts_install_when_unavailable
test_bootstrap_homebrew_returns_false_on_failure
test_bootstrap_mas_skips_when_already_available
test_bootstrap_mas_installs_via_homebrew
test_bootstrap_mas_returns_false_without_homebrew
test_check_macos_version_returns_none_on_linux
test_check_macos_version_warns_on_old_version

# State management
test_save_and_load_state_round_trip
test_load_state_returns_none_when_no_file
test_load_state_returns_none_on_corrupt_json
test_clear_state_removes_file
test_run_with_resume_loads_existing_state
test_interrupted_setup_saves_state
test_completed_with_errors_saves_state
test_successful_setup_clears_state
test_general_exception_saves_state
```

---

## Gap 4: Preview Service — Diff & Inheritance Edge Cases (MEDIUM — 82%)

`services/preview.py` has untested code in:

- `_get_installed_taps()` (lines 90-92) — calls `homebrew.list_taps()`
- `_get_installed_formulas()` (lines 96-98) — calls `homebrew.list_formulas()`
- `_get_installed_casks()` (lines 102-104) — calls `homebrew.list_casks()`
- `_get_installed_mas()` (lines 108-110) — calls `mas.list_installed()`
- Profile inheritance merge logic edge cases (what happens when parent has items but
  child has `None` vs empty list)

### Suggested test cases

```
test_diff_with_no_installed_items
test_diff_with_all_items_installed
test_inheritance_child_overrides_parent_applications
test_inheritance_child_inherits_parent_dotfiles
test_preview_profile_not_found_raises
```

---

## Gap 5: Sync Service — File Watcher & Daemon Lifecycle (MEDIUM — 84%)

`services/sync.py` has untested code in:

- `SyncService.stop()` with actual SIGTERM sending (lines 128-135)
- `FileWatcher.has_changes()` for file deletion detection (lines 39-41)
- `FileWatcher.has_changes()` for new file detection (lines 35-37)

### Suggested test cases

```
test_watcher_detects_file_deletion
test_watcher_detects_new_file_creation
test_stop_removes_pid_file_on_stale_process
test_stop_returns_false_when_not_running
```

---

## Gap 6: CLI Command Paths (MEDIUM — 89%)

`cli.py` grew from 153 to 444 statements with the new command implementations.
49 statements are uncovered, mainly:

- `cmd_capture` — JSON output path, verbose output details (lines 143-154)
- `cmd_preview` — diff mode output formatting (lines 227-265)
- `cmd_sync` — `start` subcommand when already running (lines 322-341)
- `cmd_profile` — `show`, `diff`, `create`/`delete` subcommands (lines 389-451)
- `cmd_validate` — YAML parse error path, strict mode (lines 473-501)
- macOS version check in `main()` (lines 398-404)

The integration tests cover many of these paths but some output-formatting branches
are missed.

---

## Gap 7: Config Serialization (LOW — 97%)

`models/config.py` improved from 93% to 97% (new capture service exercises the
serialization paths), but 6 lines remain uncovered:

- `_parse_applications()` when data is `None` (line 165)
- `_metadata_to_dict()` timezone edge case (line 247)
- `_applications_to_dict()` with no homebrew/mas/manual (lines 273, 287, 301, 303)

---

## Summary of Recommendations (ordered by impact)

### Priority 1: Fix the 4 broken tests

These tests regressed when bootstrap logic was added to `SetupService.run()` and are
failing on main. Fix immediately.

### Priority 2: Add adapter error-path tests (Gap 1)

The four adapters represent the largest coverage gap by line count (204 of 362 missed
lines). These are the system boundary where errors are most likely and where
remediation messages are critical for user experience.

### Priority 3: Add schema.py wrapper tests (Gap 2)

The schema validation wrappers are used by `cmd_validate` and other code. Zero coverage
despite being a critical data validation layer.

### Priority 4: Add setup bootstrap + state management tests (Gap 3)

The bootstrap methods are the root cause of the 3 broken tests and are exercised every
time `run()` is called. State management enables the resume feature and is completely
untested.

### Priority 5: Refactor setup service tests to reduce nesting

The current `test_setup.py` uses 8+ levels of nested `with patch.object()`. This makes
tests brittle, hard to read, and difficult to extend. Consider a pytest fixture that
pre-patches all adapters — each test then only overrides the specific mock behavior it
needs.

### Priority 6: Fill remaining gaps in preview, sync, and CLI (Gaps 4-6)

These modules have reasonable coverage already (82-89%) but have specific untested
branches that should be addressed for completeness.
