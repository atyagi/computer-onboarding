# Implementation Plan: macOS Configuration Sync CLI

**Branch**: `001-macos-config-sync` | **Date**: 2026-01-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-macos-config-sync/spec.md`

## Summary

A CLI tool that captures, stores, and restores macOS machine configurations including Homebrew/App Store applications, dotfiles, and system preferences. Enables rapid new machine setup and ongoing configuration synchronization using a human-readable YAML format stored in Git.

## Technical Context

**Language/Version**: Python 3.13 with bash wrapper scripts
**Package Manager**: uv (dependency management and Python version management)
**Primary Dependencies**: PyYAML (config parsing), jsonschema (validation), argparse (CLI - stdlib)
**Storage**: YAML files in user-specified directory (Git repo recommended)
**Testing**: pytest (Python), bats (bash scripts)
**Target Platform**: macOS 12 (Monterey) and later
**Project Type**: Single project (CLI tool)
**Performance Goals**: <500ms for local operations (per constitution), capture <2 min, setup <30 min hands-on
**Constraints**: <100MB memory (per constitution), offline-capable for capture, network required for install
**Scale/Scope**: Single user, 50-200 applications, 10-50 dotfiles, ~50 preference domains

**External Tools**: Homebrew (brew), Mac App Store CLI (mas), defaults (macOS built-in)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PLANNED | TDD workflow: tests before implementation |
| II. Simplicity First | ✅ PLANNED | Single CLI, minimal dependencies, YAML storage |
| III. Unix Philosophy | ✅ PLANNED | Composable commands, JSON output flag, proper exit codes |
| IV. Error Handling Excellence | ✅ PLANNED | Contextual errors with remediation suggestions |
| V. Documentation Required | ✅ PLANNED | --help for all commands, README quickstart |
| Security Standards | ✅ PLANNED | Input validation, path traversal prevention, no secrets in code |
| Performance Standards | ✅ PLANNED | <500ms local ops, <100MB memory, progress indicators, SIGINT handling |

**Gate Status**: ✅ PASS - All principles can be satisfied by design

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
pyproject.toml                # Project metadata and dependencies (uv/PEP 621)
uv.lock                       # Locked dependencies for reproducibility
.python-version               # Python 3.13 (used by uv)

src/
├── macsetup/                 # Python package
│   ├── __init__.py
│   ├── __main__.py          # Entry point for `python -m macsetup`
│   ├── cli.py               # argparse CLI definition
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration dataclasses
│   │   └── schema.py        # JSON schema definitions
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── capture.py       # Configuration capture
│   │   ├── setup.py         # Configuration restore
│   │   ├── sync.py          # Background sync daemon
│   │   └── preview.py       # Dry-run preview
│   └── adapters/            # External tool interfaces
│       ├── __init__.py
│       ├── homebrew.py      # brew CLI wrapper
│       ├── mas.py           # mas CLI wrapper
│       ├── defaults.py      # defaults CLI wrapper
│       └── dotfiles.py      # Dotfile operations

bin/
└── macsetup                  # Bash wrapper script

tests/
├── unit/                     # Unit tests (mocked dependencies)
│   ├── test_models.py
│   ├── test_capture.py
│   └── test_setup.py
├── integration/              # Integration tests (real tool calls)
│   └── test_adapters.py
├── contract/                 # Schema validation tests
│   └── test_config_schema.py
└── bats/                     # Bash script tests
    └── test_wrapper.bats

schemas/
└── config.schema.json        # JSON Schema for config validation
```

**Structure Decision**: Single project structure with Python package under `src/macsetup/` following Python packaging conventions. Bash wrapper in `bin/` for native shell experience. Tests organized by type (unit/integration/contract/bats).

## Complexity Tracking

> No violations. Design adheres to all constitution principles.

## Generated Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Research | `specs/001-macos-config-sync/research.md` | Technology decisions and rationale |
| Data Model | `specs/001-macos-config-sync/data-model.md` | Entity definitions and relationships |
| CLI Contract | `specs/001-macos-config-sync/contracts/cli-interface.md` | Command interface specification |
| Config Schema | `specs/001-macos-config-sync/contracts/config.schema.json` | JSON Schema for validation |
| Quickstart | `specs/001-macos-config-sync/quickstart.md` | User-facing getting started guide |
| Agent Context | `CLAUDE.md` | Updated with project technologies |

## Next Steps

Run `/speckit.tasks` to generate implementation tasks from this plan.
