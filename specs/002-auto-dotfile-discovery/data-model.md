# Data Model: Automatic Dotfile Discovery

**Feature**: 002-auto-dotfile-discovery
**Date**: 2026-02-12

## New Entity: DotfileRegistryEntry

Represents a single well-known dotfile in the curated registry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | str | Yes | Path relative to `$HOME` (e.g., `.zshrc`, `.config/starship.toml`) |
| category | str | Yes | Grouping label (e.g., `shell`, `git`, `editor`, `terminal`, `dev-tools`, `sensitive`) |
| sensitive | bool | No (default: False) | If True, excluded from auto-discovery unless `--include-sensitive` is passed |

**Validation rules**:
- `path` must not start with `/` or contain `..` (consistent with existing Dotfile schema)
- `category` must be a non-empty string
- Each `path` must be unique across the entire registry

**Relationships**:
- Registry entries produce `Dotfile` objects (existing entity) when discovered on disk
- A `DotfileRegistryEntry` maps 1:1 to a potential `Dotfile(path=entry.path, mode="symlink", template=False)`

## Existing Entity: Dotfile (unchanged)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| path | str | Yes | — | Path relative to `$HOME` |
| mode | str | No | "symlink" | Installation mode: "symlink" or "copy" |
| template | bool | No | False | Whether to process with template variables |

No changes needed. Auto-discovered dotfiles produce standard `Dotfile` instances indistinguishable from manually-specified ones.

## Data Flow

```text
KNOWN_DOTFILES (registry)
    │
    ▼
DotfilesAdapter.discover_dotfiles(home, excludes, include_sensitive)
    │  - Filters by sensitive flag
    │  - Checks Path.exists() for each entry
    │  - Skips directories, unreadable, oversized files
    │
    ▼
List[Dotfile]  (discovered)
    │
    ▼
CaptureService._capture_dotfiles()
    │  - Merges with user --dotfiles
    │  - De-duplicates by path
    │  - Copies each to config_dir/dotfiles/
    │
    ▼
Profile.dotfiles  (final list in config.yaml)
```

## State Transitions

No state transitions apply. Registry entries are static data. Discovery is a stateless scan. The resulting `Dotfile` objects follow the existing lifecycle (capture → store in YAML → restore via setup).
