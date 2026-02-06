"""Unit tests for capture service."""

from unittest.mock import patch

import pytest

from macsetup.adapters import AdapterResult
from macsetup.models.config import Configuration


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
        from macsetup.services.capture import CaptureService

        # Create a fake home dir with a dotfile
        home = tmp_path / "home"
        home.mkdir()
        zshrc = home / ".zshrc"
        zshrc.write_text("export PATH=/usr/local/bin:$PATH")

        service = CaptureService(config_dir=config_dir, dotfiles=[".zshrc"])

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
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
        from macsetup.services.capture import CaptureService

        home = tmp_path / "home"
        home.mkdir()

        service = CaptureService(config_dir=config_dir, dotfiles=[".nonexistent"])

        with patch.object(service.homebrew, "is_available", return_value=False):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.defaults, "is_available", return_value=False):
                    with patch("macsetup.services.capture.Path.home", return_value=home):
                        result = service.capture()

        profile = result.profiles["default"]
        assert len(profile.dotfiles) == 0


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
