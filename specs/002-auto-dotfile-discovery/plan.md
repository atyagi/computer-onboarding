# Implementation Plan: Automatic Dotfile Discovery

**Branch**: `002-auto-dotfile-discovery` | **Date**: 2026-02-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-auto-dotfile-discovery/spec.md`

## Summary

Add automatic discovery of well-known dotfiles during `macsetup capture`, bringing dotfile capture to parity with Homebrew and Mac App Store (which already auto-detect installed items). The system will maintain a curated registry of common dotfile paths, scan for their presence at capture time, and merge discovered files with any user-specified paths. Sensitive dotfiles (e.g., `.ssh/config`, `.aws/credentials`) are included in the registry but excluded by default unless the user passes `--include-sensitive`.

## Technical Context

**Language/Version**: Python 3.14 with bash wrapper scripts
**Primary Dependencies**: PyYAML, jsonschema, argparse (stdlib) — no new dependencies needed
**Storage**: YAML configuration files
**Testing**: pytest (Python), bats (bash scripts)
**Target Platform**: macOS (Darwin)
**Project Type**: Single CLI application
**Performance Goals**: Auto-discovery completes within 500ms for local filesystem scanning
**Constraints**: <500ms CLI response, <100MB memory, all operations cancellable via Ctrl+C
**Scale/Scope**: Registry of ~30-40 well-known dotfile paths; scanning ~30-40 `Path.exists()` checks against `$HOME`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | All new code will follow TDD (red/green/refactor) |
| II. Simplicity First | PASS | Registry is a simple list of dataclass entries; discovery is a loop of `Path.exists()` checks. No new dependencies. |
| III. Unix Philosophy | PASS | Discovery integrates into existing `capture` command; JSON output supported; proper exit codes maintained |
| IV. Error Handling Excellence | PASS | Warnings for unreadable/oversized files with remediation suggestions; graceful skip-and-continue |
| V. Documentation Required | PASS | `--help` will document new flags (`--exclude-dotfiles`, `--include-sensitive`); `--dotfiles` help text already says "Additional" |
| VI. Phased Pull Requests | PASS | One PR per phase: Phase 1 (setup) → Phase 2 (foundation) → Phase 3 (US1 discovery) → Phase 4 (US2 merge) → Phase 5 (US3 progress) → Phase 6 (US4 exclusion/sensitive) → Phase 7 (polish) |
| Security Standards | PASS | Sensitive dotfiles excluded by default; path validation already exists; no new external commands |
| Performance Standards | PASS | ~30-40 `stat()` calls is well under 500ms; progress reporting maintained |

All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/002-auto-dotfile-discovery/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-interface.md # CLI contract changes
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/macsetup/
├── adapters/
│   └── dotfiles.py         # MODIFY: add discover_dotfiles() method
├── models/
│   ├── config.py            # EXISTING: Dotfile dataclass (no changes needed)
│   └── registry.py          # NEW: DotfileRegistryEntry dataclass + KNOWN_DOTFILES data
├── services/
│   └── capture.py           # MODIFY: integrate auto-discovery into _capture_dotfiles()
├── schemas/
│   └── config.schema.json   # EXISTING: no changes needed (Dotfile schema unchanged)
└── cli.py                   # MODIFY: add --exclude-dotfiles and --include-sensitive flags

tests/
├── unit/
│   ├── test_registry.py     # NEW: registry data integrity tests
│   ├── test_adapters.py     # MODIFY: add discover_dotfiles() tests
│   ├── test_capture.py      # MODIFY: add auto-discovery integration tests
│   └── test_cli.py          # MODIFY: add new flag parsing tests
└── contract/
    └── test_config_schema.py # EXISTING: no changes needed
```

**Structure Decision**: Single project layout (matches existing). One new file (`models/registry.py`) for the dotfile registry data. All other changes modify existing files. No new dependencies.
