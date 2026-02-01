# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

macOS Configuration Sync CLI - A tool to capture, store, and restore macOS machine configurations including Homebrew/App Store applications, dotfiles, and system preferences.

## Active Technologies

- **Language**: Python 3.14 with bash wrapper scripts
- **Package Manager**: uv (Python version + dependency management)
- **Dependencies**: PyYAML (config parsing), jsonschema (validation), argparse (CLI - stdlib)
- **Testing**: pytest (Python), bats (bash scripts)
- **Storage**: YAML configuration files

## Project Structure

```text
src/macsetup/           # Python package
  cli.py                # CLI entry point
  models/               # Data models (config.py, schema.py)
  services/             # Business logic (capture, setup, sync, preview)
  adapters/             # External tool wrappers (homebrew, mas, defaults, dotfiles)
bin/macsetup            # Bash wrapper script
tests/
  unit/                 # Unit tests with mocked dependencies
  integration/          # Tests against real brew/mas/defaults
  contract/             # Schema validation tests
  bats/                 # Bash script tests
specs/                  # Feature specifications and design docs
```

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run a single test file
uv run pytest tests/unit/test_capture.py

# Run bash tests
bats tests/bats/

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Add a dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>
```

## Constitution Principles (Non-Negotiable)

1. **Test-First Development**: Tests MUST be written before implementation
2. **Simplicity First**: Prefer simplest solution, YAGNI, minimize dependencies
3. **Unix Philosophy**: One command does one thing, support JSON output, proper exit codes
4. **Error Handling Excellence**: Helpful errors with remediation suggestions
5. **Documentation Required**: --help for all commands
6. **Project Boundary**: NEVER edit files outside of this direct repository (i.e. "../")

## Performance Constraints

- CLI commands respond within 500ms for local operations
- Memory usage under 100MB
- All operations cancellable via Ctrl+C

<!-- MANUAL ADDITIONS START -->
<!-- Add project-specific notes here that should persist across updates -->
<!-- MANUAL ADDITIONS END -->
