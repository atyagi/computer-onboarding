"""Dotfile registry for auto-discovery."""

from dataclasses import dataclass


@dataclass
class DotfileRegistryEntry:
    """A well-known dotfile path in the curated registry."""

    path: str
    category: str
    sensitive: bool = False


KNOWN_DOTFILES: list[DotfileRegistryEntry] = [
    # Shell
    DotfileRegistryEntry(path=".bashrc", category="shell"),
    DotfileRegistryEntry(path=".bash_profile", category="shell"),
    DotfileRegistryEntry(path=".zshrc", category="shell"),
    DotfileRegistryEntry(path=".zshenv", category="shell"),
    DotfileRegistryEntry(path=".zprofile", category="shell"),
    DotfileRegistryEntry(path=".profile", category="shell"),
    # Shell extras
    DotfileRegistryEntry(path=".aliases", category="shell-extras"),
    DotfileRegistryEntry(path=".exports", category="shell-extras"),
    DotfileRegistryEntry(path=".functions", category="shell-extras"),
    DotfileRegistryEntry(path=".path", category="shell-extras"),
    DotfileRegistryEntry(path=".inputrc", category="shell-extras"),
    # Git
    DotfileRegistryEntry(path=".gitconfig", category="git"),
    DotfileRegistryEntry(path=".gitignore_global", category="git"),
    # Editor
    DotfileRegistryEntry(path=".vimrc", category="editor"),
    DotfileRegistryEntry(path=".config/nvim/init.vim", category="editor"),
    DotfileRegistryEntry(path=".config/nvim/init.lua", category="editor"),
    DotfileRegistryEntry(path=".editorconfig", category="editor"),
    # Terminal
    DotfileRegistryEntry(path=".config/starship.toml", category="terminal"),
    DotfileRegistryEntry(path=".tmux.conf", category="terminal"),
    DotfileRegistryEntry(path=".config/alacritty/alacritty.toml", category="terminal"),
    DotfileRegistryEntry(path=".config/kitty/kitty.conf", category="terminal"),
    DotfileRegistryEntry(path=".wezterm.lua", category="terminal"),
    # Dev tools
    DotfileRegistryEntry(path=".npmrc", category="dev-tools"),
    DotfileRegistryEntry(path=".gemrc", category="dev-tools"),
    DotfileRegistryEntry(path=".config/gh/config.yml", category="dev-tools"),
    DotfileRegistryEntry(path=".config/pip/pip.conf", category="dev-tools"),
    DotfileRegistryEntry(path=".config/pypoetry/config.toml", category="dev-tools"),
    DotfileRegistryEntry(path=".cargo/config.toml", category="dev-tools"),
    DotfileRegistryEntry(path=".docker/config.json", category="dev-tools"),
    # Misc
    DotfileRegistryEntry(path=".hushlogin", category="misc"),
    DotfileRegistryEntry(path=".curlrc", category="misc"),
    DotfileRegistryEntry(path=".wgetrc", category="misc"),
    # Sensitive - SSH
    DotfileRegistryEntry(path=".ssh/config", category="ssh", sensitive=True),
    # Sensitive - Cloud
    DotfileRegistryEntry(path=".aws/config", category="cloud", sensitive=True),
    DotfileRegistryEntry(path=".aws/credentials", category="cloud", sensitive=True),
    # Sensitive - Security
    DotfileRegistryEntry(path=".gnupg/gpg.conf", category="security", sensitive=True),
    DotfileRegistryEntry(path=".gnupg/gpg-agent.conf", category="security", sensitive=True),
    # Sensitive - Secrets
    DotfileRegistryEntry(path=".netrc", category="secrets", sensitive=True),
    DotfileRegistryEntry(path=".env", category="secrets", sensitive=True),
]
