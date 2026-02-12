"""Unit tests for adapters."""

import os
from unittest.mock import MagicMock, patch


class TestHomebrewAdapter:
    """Tests for Homebrew adapter."""

    def test_is_available_when_brew_exists(self):
        """Homebrew adapter is available when brew command exists."""
        from macsetup.adapters.homebrew import HomebrewAdapter

        adapter = HomebrewAdapter()
        with patch("shutil.which", return_value="/opt/homebrew/bin/brew"):
            assert adapter.is_available() is True

    def test_is_available_when_brew_missing(self):
        """Homebrew adapter is not available when brew command is missing."""
        from macsetup.adapters.homebrew import HomebrewAdapter

        adapter = HomebrewAdapter()
        with patch("shutil.which", return_value=None):
            assert adapter.is_available() is False

    def test_install_tap(self):
        """Homebrew adapter can tap a repository."""
        from macsetup.adapters.homebrew import HomebrewAdapter

        adapter = HomebrewAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.install_tap("homebrew/cask-fonts")
            assert result.success is True
            mock_run.assert_called_once()
            assert "tap" in mock_run.call_args[0][0]

    def test_install_formula(self):
        """Homebrew adapter can install a formula."""
        from macsetup.adapters.homebrew import HomebrewAdapter

        adapter = HomebrewAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.install_formula("git")
            assert result.success is True
            mock_run.assert_called_once()
            assert "install" in mock_run.call_args[0][0]

    def test_install_cask(self):
        """Homebrew adapter can install a cask."""
        from macsetup.adapters.homebrew import HomebrewAdapter

        adapter = HomebrewAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.install_cask("visual-studio-code")
            assert result.success is True
            mock_run.assert_called_once()
            assert "--cask" in mock_run.call_args[0][0]

    def test_is_formula_installed(self):
        """Homebrew adapter can check if a formula is installed."""
        from macsetup.adapters.homebrew import HomebrewAdapter

        adapter = HomebrewAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="git\n", stderr="")
            assert adapter.is_formula_installed("git") is True

    def test_is_cask_installed(self):
        """Homebrew adapter can check if a cask is installed."""
        from macsetup.adapters.homebrew import HomebrewAdapter

        adapter = HomebrewAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="visual-studio-code\n", stderr=""
            )
            assert adapter.is_cask_installed("visual-studio-code") is True


class TestMasAdapter:
    """Tests for Mac App Store adapter."""

    def test_is_available_when_mas_exists(self):
        """MAS adapter is available when mas command exists."""
        from macsetup.adapters.mas import MasAdapter

        adapter = MasAdapter()
        with patch("shutil.which", return_value="/opt/homebrew/bin/mas"):
            assert adapter.is_available() is True

    def test_is_available_when_mas_missing(self):
        """MAS adapter is not available when mas command is missing."""
        from macsetup.adapters.mas import MasAdapter

        adapter = MasAdapter()
        with patch("shutil.which", return_value=None):
            assert adapter.is_available() is False

    def test_install_app(self):
        """MAS adapter can install an app by ID."""
        from macsetup.adapters.mas import MasAdapter

        adapter = MasAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.install(497799835)
            assert result.success is True
            mock_run.assert_called_once()
            assert "install" in mock_run.call_args[0][0]

    def test_is_installed(self):
        """MAS adapter can check if an app is installed."""
        from macsetup.adapters.mas import MasAdapter

        adapter = MasAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="497799835  Xcode (15.0)\n", stderr=""
            )
            assert adapter.is_installed(497799835) is True

    def test_is_signed_in(self):
        """MAS adapter can check if user is signed in."""
        from macsetup.adapters.mas import MasAdapter

        adapter = MasAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="user@example.com", stderr="")
            assert adapter.is_signed_in() is True


class TestDefaultsAdapter:
    """Tests for defaults adapter."""

    def test_is_available(self):
        """Defaults adapter is always available on macOS."""
        from macsetup.adapters.defaults import DefaultsAdapter

        adapter = DefaultsAdapter()
        # defaults command is built into macOS
        assert adapter.is_available() is True

    def test_read_preference(self):
        """Defaults adapter can read a preference."""
        from macsetup.adapters.defaults import DefaultsAdapter

        adapter = DefaultsAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="1\n", stderr="")
            result = adapter.read("com.apple.dock", "autohide")
            assert result == "1"

    def test_write_preference(self):
        """Defaults adapter can write a preference."""
        from macsetup.adapters.defaults import DefaultsAdapter

        adapter = DefaultsAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.write("com.apple.dock", "autohide", True, "bool")
            assert result.success is True
            mock_run.assert_called_once()
            assert "write" in mock_run.call_args[0][0]

    def test_write_dict_preference(self):
        """Defaults adapter correctly formats dict arguments."""
        from macsetup.adapters.defaults import DefaultsAdapter

        adapter = DefaultsAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.write(
                "com.example.app", "prefs", {"key1": "val1", "key2": "val2"}, "dict"
            )
            assert result.success is True
            mock_run.assert_called_once()
            # Verify args are separate: ["-dict", "key1", "val1", "key2", "val2"]
            call_args = mock_run.call_args[0][0]
            assert "write" in call_args
            assert "-dict" in call_args
            dict_idx = call_args.index("-dict")
            # Check that keys and values are separate arguments
            assert call_args[dict_idx + 1] in ["key1", "key2"]
            assert call_args[dict_idx + 2] in ["val1", "val2"]

    def test_import_domain(self):
        """Defaults adapter can import a domain from a file."""
        from macsetup.adapters.defaults import DefaultsAdapter

        adapter = DefaultsAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.import_domain("com.apple.dock", "/path/to/file.plist")
            assert result.success is True


class TestDotfilesAdapter:
    """Tests for dotfiles adapter."""

    def test_is_available(self):
        """Dotfiles adapter is always available."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        assert adapter.is_available() is True

    def test_symlink_creates_symlink(self, tmp_path):
        """Dotfiles adapter can create a symlink."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()

        # Create source file
        source = tmp_path / "source" / ".zshrc"
        source.parent.mkdir(parents=True)
        source.write_text("# zshrc content")

        # Create target directory
        target = tmp_path / "home" / ".zshrc"
        target.parent.mkdir(parents=True)

        result = adapter.symlink(source, target)
        assert result.success is True
        assert target.is_symlink()
        assert target.resolve() == source

    def test_copy_creates_copy(self, tmp_path):
        """Dotfiles adapter can copy a file."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()

        # Create source file
        source = tmp_path / "source" / ".zshrc"
        source.parent.mkdir(parents=True)
        source.write_text("# zshrc content")

        # Create target directory
        target = tmp_path / "home" / ".zshrc"
        target.parent.mkdir(parents=True)

        result = adapter.copy(source, target)
        assert result.success is True
        assert target.exists()
        assert not target.is_symlink()
        assert target.read_text() == "# zshrc content"

    def test_exists_returns_true_for_existing_file(self, tmp_path):
        """Dotfiles adapter can check if a file exists."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()

        # Create file
        path = tmp_path / ".zshrc"
        path.write_text("content")

        assert adapter.exists(path) is True

    def test_exists_returns_false_for_missing_file(self, tmp_path):
        """Dotfiles adapter returns False for missing files."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        path = tmp_path / ".missing"

        assert adapter.exists(path) is False


class TestDotfilesAdapterDiscovery:
    """Tests for dotfile auto-discovery (T005)."""

    def test_discover_finds_existing_files(self, tmp_path):
        """discover_dotfiles returns Dotfile objects for files that exist."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        (home / ".zshrc").write_text("# zshrc")
        (home / ".gitconfig").write_text("[user]")

        result = adapter.discover_dotfiles(home=home)
        paths = [d.path for d in result.discovered]
        assert ".zshrc" in paths
        assert ".gitconfig" in paths

    def test_discover_skips_missing_files(self, tmp_path):
        """discover_dotfiles skips files that don't exist (FR-004)."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        # Don't create any dotfiles

        result = adapter.discover_dotfiles(home=home)
        assert result.discovered == []

    def test_discover_skips_directories(self, tmp_path):
        """discover_dotfiles skips directories (FR-006)."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        # Create .ssh/config as a directory instead of a file
        ssh_config = home / ".ssh" / "config"
        ssh_config.mkdir(parents=True)

        result = adapter.discover_dotfiles(home=home, include_sensitive=True)
        paths = [d.path for d in result.discovered]
        assert ".ssh/config" not in paths

    def test_discover_skips_unreadable_files_with_warning(self, tmp_path):
        """discover_dotfiles skips unreadable files and reports warning (FR-005)."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        unreadable = home / ".zshrc"
        unreadable.write_text("content")
        os.chmod(unreadable, 0o000)

        try:
            result = adapter.discover_dotfiles(home=home)
            paths = [d.path for d in result.discovered]
            assert ".zshrc" not in paths
            assert any(".zshrc" in w for w in result.warnings)
        finally:
            os.chmod(unreadable, 0o644)

    def test_discover_skips_oversized_files_with_warning(self, tmp_path):
        """discover_dotfiles skips files over 1 MB with warning (FR-007)."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        big_file = home / ".zshrc"
        big_file.write_bytes(b"x" * (1_048_576 + 1))

        result = adapter.discover_dotfiles(home=home)
        paths = [d.path for d in result.discovered]
        assert ".zshrc" not in paths
        assert any(".zshrc" in w for w in result.warnings)

    def test_discover_returns_dotfile_objects(self, tmp_path):
        """discover_dotfiles returns proper Dotfile objects."""
        from macsetup.adapters.dotfiles import DotfilesAdapter
        from macsetup.models.config import Dotfile

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        (home / ".zshrc").write_text("# zsh")

        result = adapter.discover_dotfiles(home=home)
        assert len(result.discovered) >= 1
        zshrc = next(d for d in result.discovered if d.path == ".zshrc")
        assert isinstance(zshrc, Dotfile)

    def test_discover_excludes_sensitive_by_default(self, tmp_path):
        """discover_dotfiles excludes sensitive entries when include_sensitive=False."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        (home / ".ssh").mkdir()
        (home / ".ssh" / "config").write_text("Host *")
        (home / ".zshrc").write_text("# zsh")

        result = adapter.discover_dotfiles(home=home, include_sensitive=False)
        paths = [d.path for d in result.discovered]
        assert ".zshrc" in paths
        assert ".ssh/config" not in paths

    def test_discover_includes_sensitive_when_requested(self, tmp_path):
        """discover_dotfiles includes sensitive entries when include_sensitive=True."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        (home / ".ssh").mkdir()
        (home / ".ssh" / "config").write_text("Host *")
        (home / ".zshrc").write_text("# zsh")

        result = adapter.discover_dotfiles(home=home, include_sensitive=True)
        paths = [d.path for d in result.discovered]
        assert ".zshrc" in paths
        assert ".ssh/config" in paths

    def test_discover_respects_exclude_list(self, tmp_path):
        """discover_dotfiles skips paths in the exclude list."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        (home / ".zshrc").write_text("# zsh")
        (home / ".gitconfig").write_text("[user]")

        result = adapter.discover_dotfiles(home=home, exclude=[".zshrc"])
        paths = [d.path for d in result.discovered]
        assert ".zshrc" not in paths
        assert ".gitconfig" in paths

    def test_discover_follows_symlinks(self, tmp_path):
        """discover_dotfiles includes symlinks (is_file() or is_symlink())."""
        from macsetup.adapters.dotfiles import DotfilesAdapter

        adapter = DotfilesAdapter()
        home = tmp_path / "home"
        home.mkdir()
        real_file = tmp_path / "real_zshrc"
        real_file.write_text("# real")
        (home / ".zshrc").symlink_to(real_file)

        result = adapter.discover_dotfiles(home=home)
        paths = [d.path for d in result.discovered]
        assert ".zshrc" in paths
