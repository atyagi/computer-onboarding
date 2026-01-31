# CLI Interface Contract

**Feature**: 001-macos-config-sync
**Date**: 2026-01-31

## Command Structure

```
macsetup <command> [options]
```

All commands support:
- `--help` - Display command help
- `--version` - Display tool version
- `--config-dir <path>` - Override config directory (default: `~/.config/macsetup`)
- `--json` - Output in JSON format (for scripting)
- `--quiet` - Suppress non-essential output
- `--verbose` - Enable debug output

---

## Commands

### `macsetup capture`

Capture current machine configuration.

**Usage**:
```
macsetup capture [options]
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `--profile <name>` | Profile to capture to | `default` |
| `--dotfiles <paths>` | Additional dotfiles to capture (comma-separated) | - |
| `--preferences <domains>` | Additional preference domains (comma-separated) | - |
| `--skip-apps` | Skip application capture | `false` |
| `--skip-dotfiles` | Skip dotfile capture | `false` |
| `--skip-preferences` | Skip preference capture | `false` |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Config directory not writable |
| 3 | External tool (brew/mas) not available |

**Output (stdout)**:
```
Capturing configuration to ~/.config/macsetup/config.yaml
  ✓ Homebrew: 45 formulas, 12 casks, 3 taps
  ✓ App Store: 8 apps
  ✓ Dotfiles: 15 files
  ✓ Preferences: 5 domains
Configuration saved.
```

**JSON Output** (`--json`):
```json
{
  "success": true,
  "config_path": "/Users/user/.config/macsetup/config.yaml",
  "summary": {
    "formulas": 45,
    "casks": 12,
    "taps": 3,
    "mas_apps": 8,
    "dotfiles": 15,
    "preference_domains": 5
  }
}
```

---

### `macsetup setup`

Apply configuration to current machine.

**Usage**:
```
macsetup setup [options]
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `--profile <name>` | Profile to apply | `default` |
| `--dry-run` | Show what would be done without making changes | `false` |
| `--include <items>` | Only install these items (comma-separated) | - |
| `--exclude <items>` | Skip these items (comma-separated) | - |
| `--resume` | Resume interrupted setup | `false` |
| `--force` | Reinstall already-installed items | `false` |
| `--no-dotfiles` | Skip dotfile setup | `false` |
| `--no-preferences` | Skip preference setup | `false` |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success (all items installed) |
| 1 | General error |
| 2 | Config file not found or invalid |
| 3 | Partial success (some items failed) |
| 4 | Network error |
| 130 | Interrupted by user (SIGINT) |

**Output (stdout)**:
```
Applying configuration from ~/.config/macsetup/config.yaml (profile: default)

Installing Homebrew packages...
  [1/45] git ✓
  [2/45] python ✓
  ...

Installing casks...
  [1/12] visual-studio-code ✓
  ...

Setup complete with 2 failures:
  ✗ docker: Cask requires Rosetta 2
  ✗ mas:497799835 (Xcode): Not signed into App Store

Manual steps required:
  - Adobe Creative Cloud: https://www.adobe.com/creativecloud/desktop-app.html
```

**JSON Output** (`--json`):
```json
{
  "success": false,
  "completed": 55,
  "failed": 2,
  "failures": [
    {"type": "cask", "name": "docker", "error": "Cask requires Rosetta 2"},
    {"type": "mas", "id": 497799835, "name": "Xcode", "error": "Not signed into App Store"}
  ],
  "manual_required": [
    {"name": "Adobe Creative Cloud", "url": "https://www.adobe.com/creativecloud/desktop-app.html"}
  ]
}
```

---

### `macsetup preview`

Show what setup would do without making changes.

**Usage**:
```
macsetup preview [options]
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `--profile <name>` | Profile to preview | `default` |
| `--diff` | Show what's different from current state | `false` |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Config file not found or invalid |

**Output (stdout)**:
```
Preview of setup (profile: default):

Applications to install:
  Homebrew formulas (45):
    git, python, node, ...
  Homebrew casks (12):
    visual-studio-code, docker, ...
  App Store (8):
    Xcode, Keynote, ...

Dotfiles to link:
  ~/.zshrc -> ~/.config/macsetup/dotfiles/.zshrc
  ~/.gitconfig -> ~/.config/macsetup/dotfiles/.gitconfig

Preferences to apply:
  com.apple.dock.autohide = true
  com.apple.dock.tilesize = 48

Manual steps (3):
  - Adobe Creative Cloud
```

---

### `macsetup sync`

Manage background sync daemon.

**Usage**:
```
macsetup sync <subcommand>
```

**Subcommands**:
| Subcommand | Description |
|------------|-------------|
| `start` | Start background sync |
| `stop` | Stop background sync |
| `status` | Show sync status |
| `now` | Run sync immediately |

**Options** (for `start`):
| Option | Description | Default |
|--------|-------------|---------|
| `--interval <minutes>` | Sync interval | `60` |
| `--watch` | Watch dotfiles for changes | `true` |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Daemon not running (for stop/status) |

---

### `macsetup profile`

Manage configuration profiles.

**Usage**:
```
macsetup profile <subcommand> [name]
```

**Subcommands**:
| Subcommand | Description |
|------------|-------------|
| `list` | List all profiles |
| `show <name>` | Show profile details |
| `create <name>` | Create new profile |
| `delete <name>` | Delete profile |
| `diff <name1> <name2>` | Compare two profiles |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Profile not found |
| 2 | Profile already exists (for create) |

---

### `macsetup validate`

Validate configuration file.

**Usage**:
```
macsetup validate [options]
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `--strict` | Fail on warnings | `false` |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Valid |
| 1 | Invalid (errors) |
| 2 | Valid with warnings (if --strict) |

---

## Progress Indication

Long-running operations display progress:

```
Installing casks [████████████░░░░░░░░] 60% (7/12) visual-studio-code
```

Progress is updated in-place on TTY, line-by-line on non-TTY.

## Signal Handling

| Signal | Behavior |
|--------|----------|
| SIGINT (Ctrl+C) | Graceful stop, save state, exit 130 |
| SIGTERM | Same as SIGINT |
| SIGHUP | Ignored (daemon continues) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MACSETUP_CONFIG_DIR` | Override default config directory |
| `MACSETUP_NO_COLOR` | Disable colored output |
| `HOMEBREW_NO_AUTO_UPDATE` | Set by macsetup during install for speed |
