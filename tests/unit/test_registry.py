"""Tests for dotfile registry data integrity."""

import pytest

from macsetup.models.registry import KNOWN_DOTFILES, DotfileRegistryEntry


class TestDotfileRegistryEntry:
    """Tests for the DotfileRegistryEntry dataclass."""

    def test_entry_has_required_fields(self):
        entry = DotfileRegistryEntry(path=".zshrc", category="shell")
        assert entry.path == ".zshrc"
        assert entry.category == "shell"
        assert entry.sensitive is False

    def test_entry_sensitive_defaults_to_false(self):
        entry = DotfileRegistryEntry(path=".zshrc", category="shell")
        assert entry.sensitive is False

    def test_entry_sensitive_can_be_true(self):
        entry = DotfileRegistryEntry(path=".ssh/config", category="ssh", sensitive=True)
        assert entry.sensitive is True


class TestKnownDotfilesRegistry:
    """Tests for the KNOWN_DOTFILES registry data integrity."""

    def test_registry_is_not_empty(self):
        assert len(KNOWN_DOTFILES) > 0

    def test_all_entries_are_registry_entries(self):
        for entry in KNOWN_DOTFILES:
            assert isinstance(entry, DotfileRegistryEntry)

    def test_all_paths_are_unique(self):
        paths = [entry.path for entry in KNOWN_DOTFILES]
        assert len(paths) == len(set(paths)), (
            f"Duplicate paths found: {[p for p in paths if paths.count(p) > 1]}"
        )

    def test_no_path_starts_with_slash(self):
        for entry in KNOWN_DOTFILES:
            assert not entry.path.startswith("/"), f"Path starts with /: {entry.path}"

    def test_no_path_contains_traversal(self):
        for entry in KNOWN_DOTFILES:
            assert ".." not in entry.path, f"Path contains ..: {entry.path}"

    def test_all_entries_have_non_empty_category(self):
        for entry in KNOWN_DOTFILES:
            assert entry.category, f"Empty category for path: {entry.path}"

    # FR-011: Required default dotfiles
    @pytest.mark.parametrize(
        "path",
        [
            ".bashrc",
            ".bash_profile",
            ".zshrc",
            ".zshenv",
            ".zprofile",
            ".gitconfig",
            ".gitignore_global",
            ".vimrc",
            ".config/nvim/init.vim",
            ".config/nvim/init.lua",
            ".config/starship.toml",
            ".tmux.conf",
            ".config/gh/config.yml",
            ".npmrc",
            ".gemrc",
        ],
    )
    def test_required_default_dotfiles_present(self, path):
        paths = [entry.path for entry in KNOWN_DOTFILES]
        assert path in paths, f"Required default dotfile missing: {path}"

    # FR-011: Required default dotfiles are NOT sensitive
    @pytest.mark.parametrize(
        "path",
        [
            ".bashrc",
            ".bash_profile",
            ".zshrc",
            ".gitconfig",
            ".vimrc",
            ".config/starship.toml",
            ".tmux.conf",
            ".npmrc",
        ],
    )
    def test_default_dotfiles_are_not_sensitive(self, path):
        entry = next(e for e in KNOWN_DOTFILES if e.path == path)
        assert entry.sensitive is False, f"Default dotfile should not be sensitive: {path}"

    # FR-013: Required sensitive dotfiles
    @pytest.mark.parametrize(
        "path",
        [
            ".ssh/config",
            ".aws/credentials",
            ".aws/config",
            ".gnupg/gpg.conf",
            ".gnupg/gpg-agent.conf",
            ".netrc",
            ".env",
        ],
    )
    def test_required_sensitive_dotfiles_present(self, path):
        paths = [entry.path for entry in KNOWN_DOTFILES]
        assert path in paths, f"Required sensitive dotfile missing: {path}"

    # FR-013: Required sensitive dotfiles ARE sensitive
    @pytest.mark.parametrize(
        "path",
        [
            ".ssh/config",
            ".aws/credentials",
            ".aws/config",
            ".gnupg/gpg.conf",
            ".gnupg/gpg-agent.conf",
            ".netrc",
            ".env",
        ],
    )
    def test_sensitive_dotfiles_are_marked_sensitive(self, path):
        entry = next(e for e in KNOWN_DOTFILES if e.path == path)
        assert entry.sensitive is True, f"Sensitive dotfile should be marked sensitive: {path}"
