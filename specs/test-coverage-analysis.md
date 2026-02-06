# Test Coverage Analysis

**Date**: 2026-02-06
**Overall coverage**: 68% (293 of 911 statements missed)
**Tests**: 110 passing, 0 failing

## Coverage by Module

| Module | Stmts | Miss | Cover | Priority |
|--------|-------|------|-------|----------|
| `adapters/dotfiles.py` | 91 | 66 | **27%** | HIGH |
| `adapters/mas.py` | 56 | 34 | **39%** | HIGH |
| `adapters/defaults.py` | 93 | 54 | **42%** | HIGH |
| `adapters/homebrew.py` | 93 | 52 | **44%** | HIGH |
| `models/schema.py` | 25 | 14 | **44%** | MEDIUM |
| `services/setup.py` | 208 | 40 | 81% | MEDIUM |
| `cli.py` | 153 | 15 | 90% | LOW |
| `models/config.py` | 175 | 13 | 93% | LOW |
| `__main__.py` | 3 | 3 | 0% | LOW |

## Gap 1: Adapter Error Handling (HIGH priority)

All four adapters have the same problem: only the happy path is tested. Every adapter
method has error-handling branches with remediation messages that are completely untested.

### dotfiles.py (27% — worst in codebase)

**Untested methods:**
- `is_symlink_valid()` — entire method (lines 123-138)
- `copy_to_config()` — entire method (lines 140-179)

**Untested error paths in `symlink()`:**
- Source file doesn't exist → returns failure
- Target already exists with backup=True → renames existing file
- Target already exists with backup=False → deletes existing file
- Target is an existing symlink → unlinks before re-creating
- PermissionError, FileNotFoundError, generic Exception branches

**Untested error paths in `copy()`:**
- Source file doesn't exist → returns failure
- Target exists with backup → renames
- Target exists without backup → deletes
- PermissionError, FileNotFoundError, generic Exception branches

### homebrew.py (44%)

**Untested methods:**
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

### mas.py (39%)

**Untested methods:**
- `list_installed()` — entire method (lines 66-90), including the line-parsing logic

**Untested error remediation in `install()`:**
- "not signed in", "not found", "already installed", "purchased" branches

**Untested edge cases:**
- `is_installed()` when exception occurs → returns False
- `is_signed_in()` when "Not signed in" is in output → returns False
- `is_signed_in()` when exception occurs → returns False

### defaults.py (42%)

**Untested methods:**
- `delete()` — entire method (lines 107-129)
- `export_domain()` — entire method (lines 154-175)

**Untested `write()` type-mapping paths:**
- `value_type="int"` → `-int` flag
- `value_type="float"` → `-float` flag
- `value_type="string"` → `-string` flag
- `value_type="array"` → `-array` flag
- Auto-detect when `value_type=None` (bool, int, float, str inference)
- CalledProcessError remediation (domain not found, type mismatch, generic)

**Untested `read()` paths:**
- `key=None` (read entire domain)
- Exception handling → returns None

## Gap 2: Schema Validation Module (MEDIUM priority)

`models/schema.py` at 44% — The contract tests in `tests/contract/test_config_schema.py`
validate against the JSON schema directly using jsonschema, but they never exercise the
Python wrapper functions in `schema.py`:

- `validate_config()` — returns list of error strings (untested)
- `is_valid()` — boolean convenience check (untested)
- `validate_config_strict()` — raises `ConfigValidationError` (untested)
- `ConfigValidationError` — custom exception with error list (untested)
- `load_schema()` — loads schema from package resources (untested)

These are the functions that actual application code would call. If they break, the
contract tests would still pass.

## Gap 3: Setup Service State Management (MEDIUM priority)

The resume/state-persistence feature in `services/setup.py` has zero direct coverage:

- `_load_state()` — loads `.state.json` for resume (lines 97-121, 0% covered)
- `_save_state()` — saves state to disk (only hit indirectly through failure paths)
- `_clear_state()` — removes state file on success (line 148-152, not covered)
- `run(resume=True)` — the resume code path (line 194-195, not covered)
- Interruption handling — setting `_interrupted = True` and saving state (lines 226-230)
- `completed_with_errors` status path (lines 236-238)
- General exception handler in `run()` (lines 243-247)

This is the mechanism that lets users resume a partially-completed setup after Ctrl+C.
It's entirely untested.

## Gap 4: Config Serialization Round-Trip (LOW-MEDIUM priority)

`models/config.py` is at 93%, but the missed lines are all in the serialization
direction (model → dict → YAML):

- `_metadata_to_dict()` — timezone handling (lines 244-247)
- `_homebrew_to_dict()` — empty-result handling
- `_applications_to_dict()` — manual app serialization
- `_dotfiles_to_list()` — mode/template serialization
- `_preferences_to_list()` — optional field serialization
- `_profile_to_dict()` — assembling profile dict
- `config_to_dict()` — full config serialization
- `save_config()` — writing YAML to disk (lines 371-374)

There is no round-trip test that verifies `load_config(path)` produces a Configuration
that, when passed through `save_config()`, produces equivalent YAML.

## Gap 5: CLI Placeholder Commands (LOW priority)

The `cmd_capture`, `cmd_preview`, `cmd_sync`, `cmd_profile`, and `cmd_validate`
functions are stubs returning 0. They're untested, but since they're placeholders,
this is low priority until they're implemented.

## Recommendations (ordered by impact)

### 1. Add adapter error-path tests

This is the highest-impact area. These adapters interact with external tools and error
handling is critical for user experience (remediation messages). Suggested test cases:

```
test_install_tap_returns_error_on_calledprocesserror
test_install_tap_remediation_for_already_tapped
test_install_tap_remediation_for_invalid_tap
test_install_formula_remediation_for_not_found
test_install_cask_remediation_for_sha256_mismatch
test_symlink_returns_error_when_source_missing
test_symlink_backs_up_existing_file
test_symlink_replaces_existing_symlink
test_copy_returns_error_when_source_missing
test_copy_backs_up_existing_file
test_is_symlink_valid_returns_true_for_valid_link
test_is_symlink_valid_returns_false_for_non_symlink
test_copy_to_config_copies_file_to_config_dir
test_copy_to_config_resolves_symlink_source
test_list_installed_parses_mas_output
test_is_signed_in_returns_false_when_not_signed_in
test_delete_preference
test_export_domain
test_write_preference_with_int_type
test_write_preference_with_auto_detect
test_list_formulas
test_list_casks
test_list_taps
test_is_tap_installed
```

### 2. Add schema.py unit tests

Test the Python validation wrapper functions directly:

```
test_validate_config_returns_empty_list_for_valid_config
test_validate_config_returns_errors_for_invalid_config
test_is_valid_returns_true_for_valid_config
test_is_valid_returns_false_for_invalid_config
test_validate_config_strict_raises_on_invalid
test_validate_config_strict_passes_on_valid
test_config_validation_error_contains_error_list
test_load_schema_returns_dict_with_properties
```

### 3. Add setup service state management tests

```
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

### 4. Add config serialization round-trip test

```
test_load_and_save_config_round_trip
test_config_to_dict_includes_all_fields
test_save_config_creates_parent_directories
test_metadata_to_dict_handles_timezone
```

### 5. Refactor setup service tests to reduce nesting

The current `test_setup.py` unit tests use 8+ levels of nested `with patch.object()`
context managers. This makes tests hard to read, maintain, and extend. Consider using
`@patch.object` decorators or a pytest fixture that pre-patches all adapters, reducing
each test to the specific mock behavior being verified.
