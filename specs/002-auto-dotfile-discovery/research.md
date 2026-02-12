# Research: Automatic Dotfile Discovery

**Feature**: 002-auto-dotfile-discovery
**Date**: 2026-02-12

## R1: Which dotfiles are commonly found on macOS developer machines?

**Decision**: Curate a registry of ~35 well-known dotfile paths organized by category. The list is based on common macOS developer tooling and covers shell, git, editor, terminal, and development tool configurations.

**Rationale**: Researched common dotfile management tools (chezmoi, yadm, stow, mackup) and macOS developer workflows. The selected paths represent files that are:
1. Commonly present on developer machines
2. Useful to sync across machines
3. Text-based configuration (not binary data or caches)

**Default entries** (auto-discovered):

| Category | Paths |
|----------|-------|
| Shell | `.bashrc`, `.bash_profile`, `.zshrc`, `.zshenv`, `.zprofile`, `.profile` |
| Git | `.gitconfig`, `.gitignore_global` |
| Editor | `.vimrc`, `.config/nvim/init.vim`, `.config/nvim/init.lua`, `.editorconfig` |
| Terminal | `.config/starship.toml`, `.tmux.conf`, `.config/alacritty/alacritty.toml`, `.config/kitty/kitty.conf`, `.wezterm.lua` |
| Dev tools | `.npmrc`, `.gemrc`, `.config/gh/config.yml`, `.config/pip/pip.conf`, `.config/pypoetry/config.toml`, `.cargo/config.toml`, `.docker/config.json` |
| Shell extras | `.aliases`, `.exports`, `.functions`, `.path`, `.inputrc` |
| Misc | `.hushlogin`, `.curlrc`, `.wgetrc` |

**Sensitive entries** (opt-in via `--include-sensitive`):

| Category | Paths |
|----------|-------|
| SSH | `.ssh/config` |
| Cloud | `.aws/config`, `.aws/credentials` |
| Security | `.gnupg/gpg.conf`, `.gnupg/gpg-agent.conf` |
| Secrets | `.netrc`, `.env` |

**Alternatives considered**:
- Scanning all dotfiles in `$HOME` recursively: Rejected — too broad, would capture caches, history files, and application data directories
- Using a YAML/JSON config file for the registry: Rejected for now (YAGNI) — a Python data structure is simpler, testable, and sufficient. Can be externalized later if needed

## R2: How should the registry be structured in code?

**Decision**: A Python module (`models/registry.py`) containing a `DotfileRegistryEntry` dataclass and a module-level `KNOWN_DOTFILES` list.

**Rationale**: This follows the existing project patterns:
- `models/config.py` uses dataclasses for all data structures
- No external file parsing needed (no YAML/JSON for the registry itself)
- Easy to test: import the list and validate properties
- Easy to extend: add a new entry = add one line

**Alternatives considered**:
- YAML file with registry data: Adds file I/O and parsing; harder to validate at import time; YAGNI
- Enum-based approach: Too rigid for a growing list; dataclass is more flexible

## R3: Where should discovery logic live?

**Decision**: Add a `discover_dotfiles()` method to `DotfilesAdapter` that takes the home directory, exclusion list, and include-sensitive flag, and returns a list of discovered `Dotfile` objects.

**Rationale**: Follows the existing adapter pattern:
- `HomebrewAdapter` has `list_formulas()`, `list_casks()`, `list_taps()` for discovery
- `MasAdapter` has `list_installed()` for discovery
- `DotfilesAdapter` currently has no discovery method — this adds it
- The adapter is the right layer because it handles filesystem interaction (already has `exists()`, `is_symlink_valid()`)

**Alternatives considered**:
- Put discovery in `CaptureService`: Mixes business logic with filesystem scanning; harder to test in isolation
- Create a new `DiscoveryAdapter`: Over-engineering for a simple scan; violates "one tool = one adapter"

## R4: How should the 1 MB file size check work?

**Decision**: Before capturing each discovered dotfile, check `Path.stat().st_size` and skip if > 1,048,576 bytes (1 MiB). Report a warning via the progress callback.

**Rationale**: Simple, fast (`stat()` is already called implicitly by `exists()`), and prevents capturing large history files (`.zsh_history`, `.bash_history`) or accidentally oversized configs.

**Alternatives considered**:
- Hardcode exclusion of known large files (`.zsh_history`): Fragile; the size check is more general
- Configurable threshold via CLI flag: YAGNI for initial release; can be added later

## R5: How should merge and de-duplication work?

**Decision**: Build the final dotfile list as: `auto_discovered + user_specified`, then de-duplicate by `path` (keeping the first occurrence). User-specified paths via `--dotfiles` that match an auto-discovered path use the auto-discovered entry (since both would have default settings anyway).

**Rationale**: Simple set-union by path. Order: auto-discovered first (alphabetical by path within registry order), then user-specified additions. De-duplication ensures no repeated entries in config.yaml.

**Alternatives considered**:
- User-specified overrides auto-discovered (different mode/template): Over-engineering for initial release; both would have defaults
