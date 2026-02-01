# Data Model: macOS Configuration Sync CLI

**Feature**: 001-macos-config-sync
**Date**: 2026-01-31

## Entities

### Configuration

The root entity representing a complete machine configuration snapshot.

```python
@dataclass
class Configuration:
    version: str                    # Schema version (e.g., "1.0")
    metadata: Metadata              # Capture context
    profiles: dict[str, Profile]    # Named configuration subsets
```

**Validation Rules**:
- `version` must be a valid semver string
- `metadata` is required
- At least one profile must exist (default: "default")

---

### Metadata

Contextual information about when/where configuration was captured.

```python
@dataclass
class Metadata:
    captured_at: datetime           # UTC timestamp of capture
    source_machine: str             # Hostname of source machine
    macos_version: str              # macOS version (e.g., "14.2")
    tool_version: str               # macsetup version used for capture
```

**Validation Rules**:
- `captured_at` must be ISO 8601 format
- `macos_version` must match pattern `\d+\.\d+(\.\d+)?`

---

### Profile

A named subset of configuration for context-specific setups.

```python
@dataclass
class Profile:
    name: str                       # Profile identifier (e.g., "work", "personal")
    description: str | None         # Optional description
    extends: str | None             # Parent profile to inherit from
    applications: Applications      # Apps to install
    dotfiles: list[Dotfile]         # Config files to sync
    preferences: list[Preference]   # System preferences to apply
```

**Validation Rules**:
- `name` must be unique within configuration
- `extends` must reference an existing profile name (no cycles)

**State Transitions**:
- Profile can be active/inactive during setup (via --profile flag)
- Inheritance resolved at setup time (child overrides parent)

---

### Applications

Container for all application sources.

```python
@dataclass
class Applications:
    homebrew: HomebrewApps | None   # Homebrew-installed apps
    mas: list[MacApp]               # Mac App Store apps
    manual: list[ManualApp]         # Apps requiring manual install
```

---

### HomebrewApps

Homebrew package manager configuration.

```python
@dataclass
class HomebrewApps:
    taps: list[str]                 # Third-party repositories
    formulas: list[str]             # CLI tools
    casks: list[str]                # GUI applications
```

**Validation Rules**:
- Tap format: `owner/repo` (e.g., "homebrew/cask-fonts")
- Formula/cask names must be valid Homebrew identifiers

---

### MacApp

Mac App Store application.

```python
@dataclass
class MacApp:
    id: int                         # App Store ID (numeric)
    name: str                       # Display name (for readability)
```

**Validation Rules**:
- `id` must be positive integer
- `name` is for documentation only (not used for install)

---

### ManualApp

Application requiring manual installation.

```python
@dataclass
class ManualApp:
    name: str                       # Application name
    url: str | None                 # Download URL (optional)
    instructions: str | None        # Installation instructions
```

---

### Dotfile

User configuration file.

```python
@dataclass
class Dotfile:
    path: str                       # Path relative to $HOME
    mode: str                       # "symlink" or "copy"
    template: bool                  # If true, process with variables
```

**Validation Rules**:
- `path` must not contain `..` (no directory traversal)
- `path` must not be absolute (no leading `/`)
- `mode` defaults to "symlink"

**State Transitions**:
- On capture: file content stored in config repo
- On setup: symlink created (or file copied if mode="copy")

---

### Preference

macOS system preference setting.

```python
@dataclass
class Preference:
    domain: str                     # Preference domain (e.g., "com.apple.dock")
    key: str | None                 # Specific key (None = entire domain)
    value: Any | None               # Value to set (None = capture current)
    type: str | None                # Type hint for defaults command
```

**Validation Rules**:
- `domain` must not be empty
- `type` if specified must be one of: string, int, float, bool, array, dict

---

### SetupState

Tracks progress of setup operation for resume capability.

```python
@dataclass
class SetupState:
    started_at: datetime            # When setup began
    profile: str                    # Active profile
    completed_items: list[str]      # Successfully installed items
    failed_items: list[FailedItem]  # Items that failed with error
    status: str                     # "in_progress", "completed", "failed"
```

**State Transitions**:
- Created on setup start
- Updated after each item install attempt
- Removed on successful completion

---

### FailedItem

Record of a failed installation.

```python
@dataclass
class FailedItem:
    type: str                       # "formula", "cask", "mas", "dotfile", "preference"
    identifier: str                 # What failed
    error: str                      # Error message
    timestamp: datetime             # When it failed
```

## Relationships

```
Configuration
    └── Metadata (1:1)
    └── Profile (1:N)
        └── Applications (1:1)
        │   └── HomebrewApps (1:1)
        │   └── MacApp (1:N)
        │   └── ManualApp (1:N)
        └── Dotfile (1:N)
        └── Preference (1:N)

SetupState (separate, for resume)
    └── FailedItem (1:N)
```

## Storage Format

### Primary Configuration (YAML)

File: `~/.config/macsetup/config.yaml` (or user-specified)

```yaml
version: "1.0"
metadata:
  captured_at: "2026-01-31T10:00:00Z"
  source_machine: "MacBook-Pro"
  macos_version: "14.2"
  tool_version: "1.0.0"

profiles:
  default:
    description: "Full machine setup"
    applications:
      homebrew:
        taps:
          - homebrew/cask-fonts
        formulas:
          - git
          - python
          - node
        casks:
          - visual-studio-code
          - docker
      mas:
        - id: 497799835
          name: "Xcode"
      manual:
        - name: "Adobe Creative Cloud"
          url: "https://www.adobe.com/creativecloud/desktop-app.html"
    dotfiles:
      - path: ".zshrc"
      - path: ".gitconfig"
    preferences:
      - domain: "com.apple.dock"
        key: "autohide"
        value: true
        type: bool

  work:
    description: "Work machine (excludes personal apps)"
    extends: "default"
    applications:
      homebrew:
        casks: []  # Override: no casks from default
```

### Setup State (JSON)

File: `~/.config/macsetup/.state.json`

```json
{
  "started_at": "2026-01-31T10:30:00Z",
  "profile": "default",
  "completed_items": ["tap:homebrew/cask-fonts", "formula:git", "formula:python"],
  "failed_items": [
    {
      "type": "cask",
      "identifier": "docker",
      "error": "Cask 'docker' requires Rosetta 2",
      "timestamp": "2026-01-31T10:32:15Z"
    }
  ],
  "status": "in_progress"
}
```

### Dotfile Storage

Directory: `~/.config/macsetup/dotfiles/`

Each tracked dotfile is stored at its relative path:
- `dotfiles/.zshrc`
- `dotfiles/.gitconfig`
- `dotfiles/.config/starship.toml`
