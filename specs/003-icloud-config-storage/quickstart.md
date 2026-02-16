# Quickstart: iCloud Config Storage

**Feature Branch**: `003-icloud-config-storage`

## What's Changing

macsetup gains a new `init` command that lets users store their configuration in iCloud Drive for automatic sync across machines. The config directory resolution (`get_config_dir()`) is updated to read from a pointer file, making all existing commands iCloud-aware with zero changes to services or adapters.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌───────────────────┐
│ CLI parser   │────▶│get_config_dir│────▶│ Pointer file?     │
│ (main)       │     │ ()           │     │ ~/.config/macsetup │
└─────────────┘     └──────────────┘     │ /config-dir        │
                           │              └────────┬──────────┘
                           │                       │
                    ┌──────▼──────┐         ┌──────▼──────┐
                    │ Default     │         │ iCloud Dir  │
                    │ ~/.config/  │         │ ~/Library/  │
                    │ macsetup    │         │ Mobile Docs │
                    └─────────────┘         └─────────────┘
```

## Key Files

### New files
- `src/macsetup/adapters/icloud.py` — iCloud Drive detection, eviction check, conflict detection
- `src/macsetup/services/init.py` — Init command logic (iCloud setup, migration, revert)
- `tests/unit/test_icloud.py` — iCloud adapter tests
- `tests/unit/test_init.py` — Init service tests

### Modified files
- `src/macsetup/cli.py` — Update `get_config_dir()` for pointer awareness; add `init` command and parser

## Build & Test

```bash
# Run all tests
uv run pytest

# Run only new tests
uv run pytest tests/unit/test_icloud.py tests/unit/test_init.py

# Run lint
uv run ruff check .

# Test the init command manually
uv run macsetup init --status
uv run macsetup init --icloud
uv run macsetup init --local
```

## Development Sequence

1. **iCloud adapter** (`adapters/icloud.py`) — Detection utilities, no dependencies on existing code
2. **Pointer file resolution** — Update `get_config_dir()`, add pointer read/write/delete
3. **Init service** (`services/init.py`) — Business logic for init --icloud, --local, --status
4. **CLI integration** — Wire up `cmd_init()` and argparse subcommand
5. **Eviction & conflict detection** — Add warnings to config directory validation
