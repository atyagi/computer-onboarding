"""Unit tests for capture service."""

from dataclasses import dataclass, field
from unittest.mock import patch

import pytest

from macsetup.adapters import AdapterResult
from macsetup.models.config import Configuration, Dotfile


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory."""
    return tmp_path / "config"


class TestCaptureHomebrew:
    """Tests for capturing Homebrew packages (T047)."""

    def test_capture_lists_installed_formulas(self, config_dir):
        """Capture service calls homebrew adapter to list formulas."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=True):
            with patch.object(service.homebrew, "list_formulas", return_value=["git", "python"]):
                with patch.object(service.homebrew, "list_casks", return_value=[]):
                    with patch.object(service.homebrew, "list_taps", return_value=[]):
                        with patch.object(service.mas, "is_available", return_value=False):
                            with patch.object(service.defaults, "is_available", return_value=False):
                                result = service.capture()
        profile = result.profiles["default"]
        assert profile.applications.homebrew.formulas == ["git", "python"]

    def test_capture_lists_installed_casks(self, config_dir):
        """Capture service calls homebrew adapter to list casks."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=True):
            with patch.object(service.homebrew, "list_formulas", return_value=[]):
                with patch.object(
                    service.homebrew, "list_casks", return_value=["visual-studio-code", "docker"]
                ):
                    with patch.object(service.homebrew, "list_taps", return_value=[]):
                        with patch.object(service.mas, "is_available", return_value=False):
                            with patch.object(service.defaults, "is_available", return_value=False):
                                result = service.capture()
        profile = result.profiles["default"]
        assert profile.applications.homebrew.casks == ["visual-studio-code", "docker"]

    def test_capture_lists_installed_taps(self, config_dir):
        """Capture service calls homebrew adapter to list taps."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=True):
            with patch.object(service.homebrew, "list_formulas", return_value=[]):
                with patch.object(service.homebrew, "list_casks", return_value=[]):
                    with patch.object(
                        service.homebrew, "list_taps", return_value=["homebrew/cask-fonts"]
                    ):
                        with patch.object(service.mas, "is_available", return_value=False):
                            with patch.object(service.defaults, "is_available", return_value=False):
                                result = service.capture()
        profile = result.profiles["default"]
        assert profile.applications.homebrew.taps == ["homebrew/cask-fonts"]

    def test_capture_skips_homebrew_when_unavailable(self, config_dir):
        """Capture service skips Homebrew when not available."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()
        profile = result.profiles["default"]
        assert profile.applications.homebrew is None


class TestCaptureMas:
    """Tests for capturing Mac App Store apps (T048)."""

    def test_capture_lists_mas_apps(self, config_dir):
        """Capture service calls mas adapter to list installed apps."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=True):
                with patch.object(
                    service.mas, "list_installed", return_value=[(497799835, "Xcode")]
                ):
                    with patch.object(service.defaults, "is_available", return_value=False):
                        result = service.capture()
        profile = result.profiles["default"]
        assert len(profile.applications.mas) == 1
        assert profile.applications.mas[0].id == 497799835
        assert profile.applications.mas[0].name == "Xcode"

    def test_capture_skips_mas_when_unavailable(self, config_dir):
        """Capture service skips MAS when not available."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()
        profile = result.profiles["default"]
        assert profile.applications.mas == []


class TestCaptureDotfiles:
    """Tests for capturing dotfiles (T049)."""

    def test_capture_copies_specified_dotfiles(self, config_dir, tmp_path):
        """Capture service copies specified dotfiles to config dir."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        # Create a fake home dir with a dotfile
        home = tmp_path / "home"
        home.mkdir()
        zshrc = home / ".zshrc"
        zshrc.write_text("export PATH=/usr/local/bin:$PATH")

        service = CaptureService(config_dir=config_dir, dotfiles=[".zshrc"])

        empty_discovery = DiscoveryResult(discovered=[], warnings=[])

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=empty_discovery,
                        ):
                            with patch.object(
                                service.dotfiles_adapter,
                                "copy_to_config",
                                return_value=AdapterResult(success=True),
                            ) as mock_copy:
                                result = service.capture()
                                mock_copy.assert_called_once()

        profile = result.profiles["default"]
        assert len(profile.dotfiles) == 1
        assert profile.dotfiles[0].path == ".zshrc"

    def test_capture_skips_nonexistent_dotfiles(self, config_dir, tmp_path):
        """Capture service skips dotfiles that don't exist."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        service = CaptureService(config_dir=config_dir, dotfiles=[".nonexistent"])

        empty_discovery = DiscoveryResult(discovered=[], warnings=[])

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=empty_discovery,
                        ):
                            result = service.capture()

        profile = result.profiles["default"]
        assert len(profile.dotfiles) == 0


class TestCaptureMergeAndDedup:
    """Tests for merging auto-discovered with explicit dotfiles (T010)."""

    def test_user_specified_dotfiles_added_to_discovered(self, config_dir, tmp_path):
        """User-specified dotfiles are added to discovered list (FR-003)."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()
        (home / ".my-custom-rc").write_text("# custom")

        fake_result = DiscoveryResult(
            discovered=[Dotfile(path=".zshrc")],
            warnings=[],
        )

        service = CaptureService(config_dir=config_dir, dotfiles=[".my-custom-rc"])

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ):
                            with patch.object(
                                service.dotfiles_adapter,
                                "copy_to_config",
                                return_value=AdapterResult(success=True),
                            ):
                                result = service.capture()

        profile = result.profiles["default"]
        paths = [d.path for d in profile.dotfiles]
        assert ".zshrc" in paths
        assert ".my-custom-rc" in paths

    def test_duplicate_paths_appear_only_once(self, config_dir, tmp_path):
        """Duplicate paths (same in discovered and user-specified) appear only once."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()
        (home / ".zshrc").write_text("# zsh")

        fake_result = DiscoveryResult(
            discovered=[Dotfile(path=".zshrc")],
            warnings=[],
        )

        # User also specifies .zshrc explicitly
        service = CaptureService(config_dir=config_dir, dotfiles=[".zshrc"])

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ):
                            with patch.object(
                                service.dotfiles_adapter,
                                "copy_to_config",
                                return_value=AdapterResult(success=True),
                            ):
                                result = service.capture()

        profile = result.profiles["default"]
        paths = [d.path for d in profile.dotfiles]
        assert paths.count(".zshrc") == 1

    def test_user_specified_nonexistent_still_attempted(self, config_dir, tmp_path):
        """User-specified paths for non-existent files are still attempted."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        fake_result = DiscoveryResult(discovered=[], warnings=[])

        service = CaptureService(config_dir=config_dir, dotfiles=[".nonexistent-custom"])

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ):
                            result = service.capture()

        profile = result.profiles["default"]
        # Non-existent file is skipped (existing behavior preserved)
        assert len(profile.dotfiles) == 0


class TestCaptureExclusionFiltering:
    """Tests for exclusion and sensitive filtering in capture service (T018)."""

    def test_exclude_dotfiles_does_not_affect_user_specified(self, config_dir, tmp_path):
        """--exclude-dotfiles does not affect user-specified --dotfiles entries."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()
        (home / ".vimrc").write_text("set nocp")

        # Discovery returns nothing (vimrc excluded), but user explicitly specifies .vimrc
        fake_result = DiscoveryResult(discovered=[], warnings=[])

        service = CaptureService(
            config_dir=config_dir,
            dotfiles=[".vimrc"],
            exclude_dotfiles=[".vimrc"],
            include_sensitive=False,
        )

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ):
                            with patch.object(
                                service.dotfiles_adapter,
                                "copy_to_config",
                                return_value=AdapterResult(success=True),
                            ):
                                result = service.capture()

        profile = result.profiles["default"]
        paths = [d.path for d in profile.dotfiles]
        # User-specified .vimrc should still be captured even though it's excluded from discovery
        assert ".vimrc" in paths

    def test_exclude_and_sensitive_passed_to_discover(self, config_dir, tmp_path):
        """exclude_dotfiles and include_sensitive are passed through to discover_dotfiles."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        fake_result = DiscoveryResult(discovered=[], warnings=[])

        service = CaptureService(
            config_dir=config_dir,
            exclude_dotfiles=[".vimrc"],
            include_sensitive=True,
        )

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ) as mock_discover:
                            service.capture()

                            mock_discover.assert_called_once_with(
                                home=home,
                                exclude=[".vimrc"],
                                include_sensitive=True,
                            )


class TestCaptureDiscoveryProgress:
    """Tests for discovery progress reporting (T013)."""

    def test_progress_callback_called_for_discovered_dotfiles(self, config_dir, tmp_path):
        """Progress callback is called for each discovered dotfile with 'Discovered' message (FR-010)."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        fake_result = DiscoveryResult(
            discovered=[Dotfile(path=".zshrc"), Dotfile(path=".gitconfig")],
            warnings=[],
        )

        progress_messages = []

        def track_progress(message, current, total):
            progress_messages.append(message)

        service = CaptureService(
            config_dir=config_dir,
            progress_callback=track_progress,
        )

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ):
                            with patch.object(
                                service.dotfiles_adapter,
                                "copy_to_config",
                                return_value=AdapterResult(success=True),
                            ):
                                service.capture()

        discovered_msgs = [m for m in progress_messages if "Discovered" in m]
        assert len(discovered_msgs) == 2
        assert any(".zshrc" in m for m in discovered_msgs)
        assert any(".gitconfig" in m for m in discovered_msgs)

    def test_warning_messages_reported_for_skipped_files(self, config_dir, tmp_path):
        """Warning messages are reported for skipped files (oversized, unreadable)."""
        from macsetup.adapters.dotfiles import DiscoveryResult
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        fake_result = DiscoveryResult(
            discovered=[],
            warnings=[
                "Skipped .zsh_history (exceeds 1 MB size limit)",
                "Skipped .config/foo (permission denied)",
            ],
        )

        progress_messages = []

        def track_progress(message, current, total):
            progress_messages.append(message)

        service = CaptureService(
            config_dir=config_dir,
            progress_callback=track_progress,
        )

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ):
                            service.capture()

        warning_msgs = [m for m in progress_messages if "[!]" in m]
        assert len(warning_msgs) == 2

    def test_skip_dotfiles_produces_no_discovery_progress(self, config_dir, tmp_path):
        """--skip-dotfiles produces no discovery progress output."""
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        progress_messages = []

        def track_progress(message, current, total):
            progress_messages.append(message)

        service = CaptureService(
            config_dir=config_dir,
            skip_dotfiles=True,
            progress_callback=track_progress,
        )

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        service.capture()

        discovered_msgs = [m for m in progress_messages if "Discovered" in m]
        assert len(discovered_msgs) == 0


class TestCaptureAutoDiscovery:
    """Tests for auto-discovery integration in capture service (T006)."""

    def test_capture_calls_discovery_and_includes_dotfiles(self, config_dir, tmp_path):
        """Capture service calls discover_dotfiles and includes results in output."""
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()
        (home / ".zshrc").write_text("# zsh")

        @dataclass
        class FakeDiscoveryResult:
            discovered: list[Dotfile] = field(default_factory=list)
            warnings: list[str] = field(default_factory=list)

        fake_result = FakeDiscoveryResult(
            discovered=[Dotfile(path=".zshrc")],
            warnings=[],
        )

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ) as mock_discover:
                            with patch.object(
                                service.dotfiles_adapter,
                                "copy_to_config",
                                return_value=AdapterResult(success=True),
                            ):
                                result = service.capture()
                                mock_discover.assert_called_once()

        profile = result.profiles["default"]
        assert len(profile.dotfiles) >= 1
        assert any(d.path == ".zshrc" for d in profile.dotfiles)

    def test_capture_skip_dotfiles_disables_discovery(self, config_dir, tmp_path):
        """--skip-dotfiles disables auto-discovery (FR-009)."""
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()
        (home / ".zshrc").write_text("# zsh")

        service = CaptureService(config_dir=config_dir, skip_dotfiles=True)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                        ) as mock_discover:
                            result = service.capture()
                            mock_discover.assert_not_called()

        profile = result.profiles["default"]
        assert profile.dotfiles == []

    def test_capture_empty_discovery_produces_empty_list(self, config_dir, tmp_path):
        """Empty discovery (no dotfiles found) produces empty list without errors."""
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        @dataclass
        class FakeDiscoveryResult:
            discovered: list[Dotfile] = field(default_factory=list)
            warnings: list[str] = field(default_factory=list)

        fake_result = FakeDiscoveryResult(discovered=[], warnings=[])

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ):
                            result = service.capture()

        profile = result.profiles["default"]
        assert profile.dotfiles == []

    def test_capture_auto_discovers_without_dotfiles_flag(self, config_dir, tmp_path):
        """Capture auto-discovers dotfiles even when no --dotfiles flag is passed."""
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        @dataclass
        class FakeDiscoveryResult:
            discovered: list[Dotfile] = field(default_factory=list)
            warnings: list[str] = field(default_factory=list)

        fake_result = FakeDiscoveryResult(
            discovered=[Dotfile(path=".gitconfig")],
            warnings=[],
        )

        # No dotfiles argument passed — auto-discovery should still run
        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        with patch.object(
                            service.dotfiles_adapter,
                            "discover_dotfiles",
                            return_value=fake_result,
                        ) as mock_discover:
                            with patch.object(
                                service.dotfiles_adapter,
                                "copy_to_config",
                                return_value=AdapterResult(success=True),
                            ):
                                result = service.capture()
                                mock_discover.assert_called_once()

        profile = result.profiles["default"]
        assert len(profile.dotfiles) >= 1
        assert any(d.path == ".gitconfig" for d in profile.dotfiles)


class TestCapturePreferences:
    """Tests for capturing system preferences (T050)."""

    def test_capture_reads_specified_preferences(self, config_dir):
        """Capture service reads specified preference domains."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(
            config_dir=config_dir,
            preference_domains=["com.apple.dock"],
        )

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=True):
                    with patch.object(
                        service.defaults,
                        "read",
                        return_value="{\n    autohide = 1;\n}",
                    ):
                        result = service.capture()

        profile = result.profiles["default"]
        assert len(profile.preferences) == 1
        assert profile.preferences[0].domain == "com.apple.dock"

    def test_capture_skips_preferences_when_none_specified(self, config_dir):
        """Capture service skips preferences when none are specified."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()

        profile = result.profiles["default"]
        assert profile.preferences == []


class TestCaptureService:
    """Tests for capture service orchestration (T051)."""

    def test_capture_service_can_be_created(self, config_dir):
        """Capture service can be instantiated."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)
        assert service is not None

    def test_capture_returns_configuration(self, config_dir):
        """Capture service returns a Configuration object."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()

        assert isinstance(result, Configuration)
        assert result.version == "1.0"
        assert "default" in result.profiles

    def test_capture_populates_metadata(self, config_dir):
        """Capture service populates metadata with machine info."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.platform") as mock_platform:
                        mock_platform.node.return_value = "test-machine"
                        mock_platform.mac_ver.return_value = ("14.2", ("", "", ""), "")
                        result = service.capture()

        assert result.metadata.source_machine == "test-machine"
        assert result.metadata.macos_version == "14.2"
        assert result.metadata.tool_version == "1.0.0"

    def test_capture_uses_specified_profile_name(self, config_dir):
        """Capture service uses the specified profile name."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir, profile="work")

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()

        assert "work" in result.profiles

    def test_capture_skips_apps_when_requested(self, config_dir):
        """Capture service skips app capture when skip_apps=True."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir, skip_apps=True)

        with patch.object(service.homebrew, "is_available", return_value=True):
            with patch.object(service.mas, "is_available", return_value=True):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()

        # Homebrew list methods should not be called
        profile = result.profiles["default"]
        assert profile.applications.homebrew is None
        assert profile.applications.mas == []

    def test_capture_skips_dotfiles_when_requested(self, config_dir):
        """Capture service skips dotfile capture when skip_dotfiles=True."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(config_dir=config_dir, dotfiles=[".zshrc"], skip_dotfiles=True)

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()

        profile = result.profiles["default"]
        assert profile.dotfiles == []

    def test_capture_skips_preferences_when_requested(self, config_dir):
        """Capture service skips preferences when skip_preferences=True."""
        from macsetup.services.capture import CaptureService

        service = CaptureService(
            config_dir=config_dir,
            preference_domains=["com.apple.dock"],
            skip_preferences=True,
        )

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    result = service.capture()

        profile = result.profiles["default"]
        assert profile.preferences == []
