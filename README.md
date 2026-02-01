# macsetup

macOS Configuration Sync CLI - Capture, store, and restore macOS machine configurations including Homebrew/App Store applications, dotfiles, and system preferences.

## Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone git@github.com:atyagi/computer-onboarding.git
cd computer-onboarding

# Install dependencies
uv sync

# Install (adds macsetup to PATH)
./install.sh
```

## Quick Start

```bash
# Capture your current machine configuration
macsetup capture

# Preview what would be installed
macsetup preview

# Set up a new machine
macsetup setup
```

## Documentation

See [quickstart.md](specs/001-macos-config-sync/quickstart.md) for detailed usage.
