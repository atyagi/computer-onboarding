# Research: macOS Configuration Sync CLI

**Feature**: 001-macos-config-sync
**Date**: 2026-01-31

## Technology Decisions

### Language Choice: Shell + Python 3.14

**Decision**: Use bash scripts as the primary interface with Python 3.14 for complex logic

**Rationale**:
- Simplest approach that directly wraps existing tools (brew, mas, defaults)
- No compilation required - immediate execution and modification
- Python 3.14 provides latest performance improvements and language features
- Python provides structured data handling (YAML parsing, JSON output)
- Most portable for the target audience (developers with Python already installed)
- Aligns with Constitution Principle II (Simplicity First)

**Alternatives Rejected**:
- Swift: Requires Xcode installation, compilation step, overkill for wrapping CLI tools
- Go: Good CLI ergonomics but adds compilation complexity for tool wrapping
- Rust: Excellent but steep learning curve, overkill for this use case

### Python Version & Dependency Management: uv

**Decision**: Use uv for both Python version management and dependency management

**Rationale**:
- Single tool for Python version + dependencies (replaces pyenv + pip/poetry/pipenv)
- Extremely fast (10-100x faster than pip)
- Lockfile support for reproducible builds
- Compatible with standard pyproject.toml
- Written in Rust, minimal dependencies
- Active development by Astral (same team as Ruff)

**Implementation**:
- `.python-version` file specifies Python 3.14
- `pyproject.toml` defines dependencies
- `uv.lock` ensures reproducible installs
- `uv run` executes commands in the project environment

### Package Manager Integration

**Decision**: Support Homebrew (formulas + casks) and Mac App Store (mas-cli)

**Rationale**:
- Homebrew is the de facto standard for macOS package management
- mas-cli provides CLI access to Mac App Store (required for some apps)
- Both tools are idempotent and scriptable
- Direct download apps marked as "manual" in config

**Implementation**:
- `brew bundle dump` generates Brewfile (formulas, casks, taps)
- `mas list` captures App Store apps
- Restore uses `brew bundle install` and `mas install`

### Dotfile Management

**Decision**: Copy tracked dotfiles to config directory, symlink on restore

**Rationale**:
- Simple file operations, no complex version control within the tool
- User's Git repo provides versioning
- Symlinks allow live updates to sync back

**Implementation**:
- Config specifies dotfile paths relative to $HOME
- Capture: copy file contents to `config/dotfiles/`
- Restore: symlink from $HOME to config location

### System Preferences

**Decision**: Use `defaults read/write` for preference domains

**Rationale**:
- Built-in macOS command, no dependencies
- Well-documented domains for common preferences
- JSON-serializable values

**Implementation**:
- Maintain list of "tracked" preference domains in config
- Capture: `defaults export domain -` for each tracked domain
- Restore: `defaults import domain file`

### Configuration Format

**Decision**: YAML with JSON schema validation

**Rationale**:
- Human-readable and editable
- Git-friendly (meaningful diffs)
- Python has excellent YAML support (PyYAML/ruamel.yaml)
- JSON schema provides validation without additional tooling

**Structure**:
```yaml
version: "1.0"
metadata:
  captured_at: "2026-01-31T10:00:00Z"
  source_machine: "MacBook-Pro"
  macos_version: "14.2"

profiles:
  default:
    applications:
      homebrew:
        formulas: [git, python, node]
        casks: [visual-studio-code, docker]
        taps: [homebrew/cask-fonts]
      mas:
        - id: 497799835
          name: "Xcode"
    dotfiles:
      - path: ".zshrc"
      - path: ".gitconfig"
    preferences:
      - domain: "com.apple.dock"
        keys: [autohide, tilesize]
```

### Testing Strategy

**Decision**: pytest for Python code, bats for shell scripts

**Rationale**:
- pytest is standard for Python testing
- bats (Bash Automated Testing System) is standard for shell script testing
- Both support TDD workflow required by constitution

**Implementation**:
- Unit tests: mock system calls, test parsing/formatting
- Integration tests: test against actual brew/defaults (in CI)
- Contract tests: validate config file schema

### CLI Framework

**Decision**: argparse (Python stdlib) + bash wrapper

**Rationale**:
- No external dependencies for CLI parsing
- Bash wrapper provides native shell experience
- Python handles subcommands and complex options

**Commands**:
- `macsetup capture` - Capture current configuration
- `macsetup setup` - Apply configuration to machine
- `macsetup preview` - Show what would be changed
- `macsetup sync` - Background sync daemon
- `macsetup profile` - Manage configuration profiles

## Open Questions Resolved

### Q: How to handle apps requiring manual intervention?
**A**: Mark in config with `manual: true` flag. Setup command lists these at the end with instructions.

### Q: How to handle preference domains that vary by macOS version?
**A**: Include macOS version in config metadata. Warn on version mismatch, apply compatible subset.

### Q: How to handle network interruption during setup?
**A**: Each app install is atomic. Track completed installs in state file. Resume skips completed items.

### Q: Where to store configuration?
**A**: User-specified via `--config-dir` flag. Defaults to `~/.config/macsetup/`. Recommend Git repo.
