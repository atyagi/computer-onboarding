# Implementation Plan: iCloud Config Storage

**Branch**: `003-icloud-config-storage` | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-icloud-config-storage/spec.md`

## Summary

Enable macsetup to store its configuration directory in iCloud Drive for automatic sync across machines. A new `macsetup init` command handles iCloud setup, migration, and revert. The existing `get_config_dir()` function gains pointer file awareness so all existing commands transparently work with iCloud-backed storage. No changes to services or adapters are required — the feature is localized to config directory resolution and the new init command.

## Technical Context

**Language/Version**: Python 3.14 with bash wrapper scripts
**Primary Dependencies**: PyYAML, jsonschema, argparse (stdlib) — no new dependencies needed
**Storage**: YAML configuration files, plain text pointer file
**Testing**: pytest (Python), bats (bash scripts)
**Target Platform**: macOS (iCloud Drive integration)
**Project Type**: Single project (CLI tool)
**Performance Goals**: CLI commands respond within 500ms for local operations
**Constraints**: <500ms local operations, <100MB memory, Ctrl+C cancellable
**Scale/Scope**: Single-user CLI tool, config files typically <1MB total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | All new code (adapter, service, CLI) will have tests written first |
| II. Simplicity First | PASS | No new dependencies; pointer file is simplest persistence mechanism; single function change makes all commands iCloud-aware |
| III. Unix Philosophy | PASS | `init` does one thing (configure storage backend); supports `--json` output; meaningful exit codes (0/1/2) |
| IV. Error Handling Excellence | PASS | iCloud unavailable, conflict, eviction — all produce errors with remediation steps |
| V. Documentation Required | PASS | `init --help` will cover all options; existing `--help` unchanged |
| VI. Phased Pull Requests | PASS | Implementation will proceed through discrete phases with independent PRs |

**Post-Phase 1 re-check**: PASS — Design adds 2 new files (adapter + service) following existing patterns. No abstractions beyond what's needed. Pointer file mechanism is the simplest approach that satisfies requirements.

## Project Structure

### Documentation (this feature)

```text
specs/003-icloud-config-storage/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: iCloud Drive research findings
├── data-model.md        # Phase 1: Entity definitions and state transitions
├── quickstart.md        # Phase 1: Development quick reference
├── contracts/
│   └── cli-contract.md  # Phase 1: init command CLI contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/macsetup/
├── cli.py                    # MODIFIED: get_config_dir() + cmd_init() + parser
├── adapters/
│   ├── icloud.py             # NEW: iCloud Drive detection, eviction, conflicts
│   └── (existing adapters unchanged)
├── services/
│   ├── init.py               # NEW: init command business logic
│   └── (existing services unchanged)
└── models/
    └── (unchanged)

tests/
├── unit/
│   ├── test_cli.py           # MODIFIED: pointer resolution tests, init command tests
│   ├── test_icloud.py        # NEW: iCloud adapter unit tests
│   └── test_init.py          # NEW: init service unit tests
└── (integration/, contract/, bats/ unchanged)
```

**Structure Decision**: Follows existing single-project layout. New adapter (`icloud.py`) and service (`init.py`) follow the established pattern of one adapter/service per domain concern. No structural changes to the project.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
