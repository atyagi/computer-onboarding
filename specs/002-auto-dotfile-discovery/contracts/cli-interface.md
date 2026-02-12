# CLI Interface Contract: Automatic Dotfile Discovery

**Feature**: 002-auto-dotfile-discovery
**Date**: 2026-02-12

## Modified Command: `macsetup capture`

### New Flags

#### `--exclude-dotfiles PATHS`

Comma-separated list of dotfile paths to exclude from auto-discovery.

```text
--exclude-dotfiles PATHS    Dotfile paths to exclude from auto-discovery (comma-separated)
```

**Behavior**:
- Paths are relative to `$HOME` (same format as `--dotfiles`)
- Excluded paths are removed from the auto-discovered list before capture
- Does not affect user-specified `--dotfiles` entries (explicit inclusion overrides exclusion)
- No error if an excluded path isn't in the registry or doesn't exist

**Examples**:
```bash
macsetup capture --exclude-dotfiles ".vimrc,.tmux.conf"
macsetup capture --exclude-dotfiles ".config/nvim/init.vim"
```

#### `--include-sensitive`

Include sensitive dotfiles (e.g., `.ssh/config`, `.aws/credentials`) in auto-discovery.

```text
--include-sensitive          Include sensitive dotfiles in auto-discovery
```

**Behavior**:
- Boolean flag (no argument)
- When absent: sensitive registry entries are skipped during discovery
- When present: sensitive entries are discovered alongside default entries
- Can be combined with `--exclude-dotfiles` to include sensitive but skip specific ones

**Examples**:
```bash
macsetup capture --include-sensitive
macsetup capture --include-sensitive --exclude-dotfiles ".aws/credentials"
```

### Modified Flag: `--dotfiles PATHS`

**Previous behavior**: Specifies dotfiles to capture (the only source of dotfile paths).
**New behavior**: Specifies *additional* dotfiles to capture beyond auto-discovery.

```text
--dotfiles PATHS             Additional dotfiles to capture (comma-separated)
```

Help text already says "Additional" — no wording change needed.

**Behavior change**: Previously, omitting `--dotfiles` meant zero dotfiles captured. Now, omitting `--dotfiles` still triggers auto-discovery of known dotfiles. This is the intended parity with Homebrew/MAS.

### Existing Flag: `--skip-dotfiles` (unchanged)

Disables all dotfile capture, including auto-discovery. No behavioral change.

## Flag Interaction Matrix

| `--skip-dotfiles` | `--dotfiles` | `--exclude-dotfiles` | `--include-sensitive` | Result |
|--------------------|--------------|----------------------|-----------------------|--------|
| No | No | No | No | Auto-discover default dotfiles |
| No | Yes | No | No | Auto-discover + user-specified (merged, de-duped) |
| No | No | Yes | No | Auto-discover minus excluded paths |
| No | No | No | Yes | Auto-discover default + sensitive dotfiles |
| No | Yes | Yes | Yes | Auto-discover all + user-specified - excluded (merged, de-duped) |
| Yes | * | * | * | No dotfiles captured (all flags ignored) |

## Output Contract

### Human-readable output (default)

Discovery progress is reported during capture:

```text
Capturing configuration to ~/.config/macsetup (profile: default)

  [1/3] Capturing Homebrew packages
  [2/3] Capturing Mac App Store apps
  [1/8] Discovered .zshrc
  [2/8] Discovered .gitconfig
  [3/8] Discovered .config/starship.toml
  ...
  [!] Skipped .zsh_history (exceeds 1 MB size limit)
  [!] Skipped .config/foo (permission denied)

Configuration saved to ~/.config/macsetup/config.yaml
  Homebrew: 2 taps, 45 formulas, 12 casks
  Mac App Store: 8 apps
  Dotfiles: 8 files
```

### JSON output (`--json`)

No structural changes to JSON output. The `dotfiles` array in the config object contains discovered + user-specified dotfiles. No distinction between source types in output (a dotfile is a dotfile).

```json
{
  "success": true,
  "config_path": "~/.config/macsetup/config.yaml",
  "profile": "default",
  "config": {
    "profiles": {
      "default": {
        "dotfiles": [
          {"path": ".zshrc"},
          {"path": ".gitconfig"},
          {"path": ".config/starship.toml"}
        ]
      }
    }
  }
}
```

## Exit Codes (unchanged)

- `0`: Success
- `2`: Configuration error
- `3`: Partial failure (some items failed)
- `130`: Interrupted (SIGINT)
