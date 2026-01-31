# macsetup Quickstart

## Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/atyagi/computer-onboarding.git
cd computer-onboarding

# Install dependencies (uv will automatically install Python 3.14 if needed)
uv sync

# Install (adds macsetup to PATH)
./install.sh
```

Prerequisites:
- macOS 12 (Monterey) or later
- uv (installs Python 3.14 automatically)
- Homebrew (installed automatically if missing)

## Capture Your Current Machine

```bash
# Capture everything (apps, dotfiles, preferences)
macsetup capture

# Capture to a custom directory (e.g., Git repo)
macsetup capture --config-dir ~/dotfiles

# Capture specific dotfiles
macsetup capture --dotfiles ".zshrc,.gitconfig,.config/starship.toml"
```

Configuration is saved to `~/.config/macsetup/config.yaml` by default.

## Set Up a New Machine

```bash
# Preview what will be installed
macsetup preview

# Run setup
macsetup setup

# Resume if interrupted
macsetup setup --resume

# Use a specific profile
macsetup setup --profile work
```

## Managing Profiles

```bash
# List profiles
macsetup profile list

# Create a work profile that excludes personal apps
macsetup profile create work

# Show profile differences
macsetup profile diff default work
```

## Common Workflows

### Back up current machine to Git

```bash
# Initial setup
mkdir ~/dotfiles && cd ~/dotfiles
git init
macsetup capture --config-dir .

# Commit and push
git add .
git commit -m "Initial configuration capture"
git remote add origin git@github.com:you/dotfiles.git
git push -u origin main
```

### Restore on a new machine

```bash
# Clone your config
git clone git@github.com:you/dotfiles.git ~/.config/macsetup

# Preview first
macsetup preview

# Apply
macsetup setup
```

### Keep config in sync

```bash
# Start background sync (captures changes hourly)
macsetup sync start

# Or manually sync
macsetup capture
cd ~/.config/macsetup
git add . && git commit -m "Update config" && git push
```

## Troubleshooting

### "brew: command not found"

Homebrew will be installed automatically. If it fails:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### App Store apps not installing

Sign into the App Store first:
```bash
mas signin your@email.com
```

### Setup was interrupted

Resume from where you left off:
```bash
macsetup setup --resume
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MACSETUP_CONFIG_DIR` | Override config directory |
| `MACSETUP_NO_COLOR` | Disable colored output |

## Next Steps

- Edit `~/.config/macsetup/config.yaml` to customize your configuration
- Create profiles for different machine types (work, personal, server)
- Set up a Git repo for version control
- Enable background sync for automatic updates
