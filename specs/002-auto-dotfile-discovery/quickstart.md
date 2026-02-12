# Quickstart: Automatic Dotfile Discovery

**Feature**: 002-auto-dotfile-discovery

## What Changed

The `macsetup capture` command now automatically discovers common dotfiles on your machine. Previously, you had to explicitly list every dotfile path. Now it works like Homebrew and Mac App Store capture — just run the command and it finds everything.

## Basic Usage

```bash
# Capture everything (apps + dotfiles + preferences)
# Dotfiles are now auto-discovered — no --dotfiles flag needed
macsetup capture

# Add custom dotfiles beyond what's auto-discovered
macsetup capture --dotfiles ".my-custom-rc,.work/settings"

# Exclude specific dotfiles from auto-discovery
macsetup capture --exclude-dotfiles ".vimrc,.tmux.conf"

# Include sensitive dotfiles (SSH, AWS, GPG configs)
macsetup capture --include-sensitive

# Combine flags
macsetup capture --include-sensitive --exclude-dotfiles ".aws/credentials" --dotfiles ".custom-tool-config"

# Skip dotfile capture entirely (same as before)
macsetup capture --skip-dotfiles
```

## What Gets Discovered

By default, the tool scans for well-known dotfiles in these categories:

- **Shell**: `.bashrc`, `.bash_profile`, `.zshrc`, `.zshenv`, `.zprofile`, `.profile`, `.aliases`, `.exports`, `.functions`, `.path`, `.inputrc`
- **Git**: `.gitconfig`, `.gitignore_global`
- **Editors**: `.vimrc`, `.config/nvim/init.vim`, `.config/nvim/init.lua`, `.editorconfig`
- **Terminal**: `.config/starship.toml`, `.tmux.conf`, `.config/alacritty/alacritty.toml`, `.config/kitty/kitty.conf`, `.wezterm.lua`
- **Dev tools**: `.npmrc`, `.gemrc`, `.config/gh/config.yml`, `.config/pip/pip.conf`, `.cargo/config.toml`, `.docker/config.json`
- **Misc**: `.hushlogin`, `.curlrc`, `.wgetrc`

### Sensitive (opt-in only with `--include-sensitive`)

- **SSH**: `.ssh/config`
- **Cloud**: `.aws/config`, `.aws/credentials`
- **Security**: `.gnupg/gpg.conf`, `.gnupg/gpg-agent.conf`
- **Secrets**: `.netrc`, `.env`

## Safety Features

- Files over 1 MB are skipped with a warning (prevents capturing history files)
- Directories are skipped (only files and symlinks are captured)
- Unreadable files are skipped with a warning
- Sensitive dotfiles are never captured unless you explicitly opt in
