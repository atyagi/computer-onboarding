"""Unit tests for setup service."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from macsetup.adapters import AdapterResult
from macsetup.models.config import (
    Applications,
    Configuration,
    Dotfile,
    HomebrewApps,
    MacApp,
    ManualApp,
    Metadata,
    Preference,
    Profile,
)


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return Configuration(
        version="1.0",
        metadata=Metadata(
            captured_at=datetime.now(UTC),
            source_machine="test-machine",
            macos_version="14.2",
            tool_version="1.0.0",
        ),
        profiles={
            "default": Profile(
                name="default",
                applications=Applications(
                    homebrew=HomebrewApps(
                        taps=["homebrew/cask-fonts"],
                        formulas=["git", "python"],
                        casks=["visual-studio-code"],
                    ),
                    mas=[MacApp(id=497799835, name="Xcode")],
                    manual=[ManualApp(name="Adobe Creative Cloud")],
                ),
                dotfiles=[Dotfile(path=".zshrc")],
                preferences=[
                    Preference(domain="com.apple.dock", key="autohide", value=True, type="bool")
                ],
            )
        },
    )


class TestSetupService:
    """Tests for setup service."""

    def test_setup_service_can_be_created(self, sample_config, tmp_path):
        """Setup service can be instantiated."""
        from macsetup.services.setup import SetupService

        service = SetupService(config=sample_config, config_dir=tmp_path, profile="default")
        assert service is not None

    def test_setup_service_installs_taps(self, sample_config, tmp_path):
        """Setup service installs Homebrew taps."""
        from macsetup.services.setup import SetupService

        service = SetupService(config=sample_config, config_dir=tmp_path, profile="default")

        with patch.object(service.homebrew, "install_tap") as mock_tap:
            mock_tap.return_value = AdapterResult(success=True)
            with patch.object(service.homebrew, "is_available", return_value=True):
                with patch.object(service.mas, "is_available", return_value=False):
                    with patch.object(service.dotfiles, "symlink") as mock_symlink:
                        mock_symlink.return_value = AdapterResult(success=True)
                        with patch.object(service.homebrew, "is_tap_installed", return_value=False):
                            with patch.object(
                                service.homebrew, "is_formula_installed", return_value=True
                            ):
                                with patch.object(
                                    service.homebrew, "is_cask_installed", return_value=True
                                ):
                                    with patch.object(
                                        service.homebrew, "install_formula"
                                    ) as mock_formula:
                                        mock_formula.return_value = AdapterResult(success=True)
                                        with patch.object(
                                            service.defaults, "write"
                                        ) as mock_defaults:
                                            mock_defaults.return_value = AdapterResult(success=True)
                                            service.run()
                                            mock_tap.assert_called()

    def test_setup_service_installs_formulas(self, sample_config, tmp_path):
        """Setup service installs Homebrew formulas."""
        from macsetup.services.setup import SetupService

        service = SetupService(config=sample_config, config_dir=tmp_path, profile="default")

        with patch.object(service.homebrew, "install_formula") as mock_formula:
            mock_formula.return_value = AdapterResult(success=True)
            with patch.object(service.homebrew, "is_available", return_value=True):
                with patch.object(service.mas, "is_available", return_value=False):
                    with patch.object(service.homebrew, "install_tap") as mock_tap:
                        mock_tap.return_value = AdapterResult(success=True)
                        with patch.object(service.homebrew, "is_tap_installed", return_value=False):
                            with patch.object(
                                service.homebrew, "is_formula_installed", return_value=False
                            ):
                                with patch.object(
                                    service.homebrew, "is_cask_installed", return_value=True
                                ):
                                    with patch.object(service.dotfiles, "symlink") as mock_symlink:
                                        mock_symlink.return_value = AdapterResult(success=True)
                                        with patch.object(
                                            service.defaults, "write"
                                        ) as mock_defaults:
                                            mock_defaults.return_value = AdapterResult(success=True)
                                            service.run()
                                            mock_formula.assert_called()

    def test_setup_service_installs_casks(self, sample_config, tmp_path):
        """Setup service installs Homebrew casks."""
        from macsetup.services.setup import SetupService

        service = SetupService(config=sample_config, config_dir=tmp_path, profile="default")

        with patch.object(service.homebrew, "install_cask") as mock_cask:
            mock_cask.return_value = AdapterResult(success=True)
            with patch.object(service.homebrew, "is_available", return_value=True):
                with patch.object(service.mas, "is_available", return_value=False):
                    with patch.object(service.homebrew, "install_tap") as mock_tap:
                        mock_tap.return_value = AdapterResult(success=True)
                        with patch.object(service.homebrew, "is_tap_installed", return_value=True):
                            with patch.object(
                                service.homebrew, "is_formula_installed", return_value=True
                            ):
                                with patch.object(
                                    service.homebrew, "is_cask_installed", return_value=False
                                ):
                                    with patch.object(
                                        service.homebrew, "install_formula"
                                    ) as mock_formula:
                                        mock_formula.return_value = AdapterResult(success=True)
                                        with patch.object(
                                            service.dotfiles, "symlink"
                                        ) as mock_symlink:
                                            mock_symlink.return_value = AdapterResult(success=True)
                                            with patch.object(
                                                service.defaults, "write"
                                            ) as mock_defaults:
                                                mock_defaults.return_value = AdapterResult(
                                                    success=True
                                                )
                                                service.run()
                                                mock_cask.assert_called()

    def test_setup_service_tracks_failed_items(self, sample_config, tmp_path):
        """Setup service tracks failed items."""
        from macsetup.services.setup import SetupService

        service = SetupService(config=sample_config, config_dir=tmp_path, profile="default")

        with patch.object(service.homebrew, "install_tap") as mock_tap:
            mock_tap.return_value = AdapterResult(success=False, error="Network error")
            with patch.object(service.homebrew, "is_available", return_value=True):
                with patch.object(service.mas, "is_available", return_value=False):
                    with patch.object(service.homebrew, "is_tap_installed", return_value=False):
                        with patch.object(
                            service.homebrew, "is_formula_installed", return_value=True
                        ):
                            with patch.object(
                                service.homebrew, "is_cask_installed", return_value=True
                            ):
                                with patch.object(service.dotfiles, "symlink") as mock_symlink:
                                    mock_symlink.return_value = AdapterResult(success=True)
                                    with patch.object(service.defaults, "write") as mock_defaults:
                                        mock_defaults.return_value = AdapterResult(success=True)
                                        result = service.run()
                                        assert len(result.failed_items) > 0

    def test_setup_service_skips_installed_items(self, sample_config, tmp_path):
        """Setup service skips already-installed items (idempotency)."""
        from macsetup.services.setup import SetupService

        service = SetupService(config=sample_config, config_dir=tmp_path, profile="default")

        with patch.object(service.homebrew, "install_formula") as mock_formula:
            mock_formula.return_value = AdapterResult(success=True)
            with patch.object(service.homebrew, "is_available", return_value=True):
                with patch.object(service.mas, "is_available", return_value=True):
                    with patch.object(service.homebrew, "install_tap") as mock_tap:
                        mock_tap.return_value = AdapterResult(success=True)
                        # Mark all items as already installed
                        with patch.object(service.homebrew, "is_tap_installed", return_value=True):
                            with patch.object(
                                service.homebrew, "is_formula_installed", return_value=True
                            ):
                                with patch.object(
                                    service.homebrew, "is_cask_installed", return_value=True
                                ):
                                    with patch.object(service.dotfiles, "symlink") as mock_symlink:
                                        mock_symlink.return_value = AdapterResult(success=True)
                                        with patch.object(
                                            service.defaults, "write"
                                        ) as mock_defaults:
                                            mock_defaults.return_value = AdapterResult(success=True)
                                            service.run()
                                            # install_formula should not be called since items are installed
                                            mock_formula.assert_not_called()

    def test_setup_service_returns_manual_apps(self, sample_config, tmp_path):
        """Setup service returns list of manual apps at the end."""
        from macsetup.services.setup import SetupService

        service = SetupService(config=sample_config, config_dir=tmp_path, profile="default")

        with patch.object(service.homebrew, "is_available", return_value=True):
            with patch.object(service.mas, "is_available", return_value=False):
                with patch.object(service.homebrew, "install_tap") as mock_tap:
                    mock_tap.return_value = AdapterResult(success=True)
                    with patch.object(service.homebrew, "is_tap_installed", return_value=True):
                        with patch.object(
                            service.homebrew, "is_formula_installed", return_value=True
                        ):
                            with patch.object(
                                service.homebrew, "is_cask_installed", return_value=True
                            ):
                                with patch.object(
                                    service.homebrew, "install_formula"
                                ) as mock_formula:
                                    mock_formula.return_value = AdapterResult(success=True)
                                    with patch.object(service.dotfiles, "symlink") as mock_symlink:
                                        mock_symlink.return_value = AdapterResult(success=True)
                                        with patch.object(
                                            service.defaults, "write"
                                        ) as mock_defaults:
                                            mock_defaults.return_value = AdapterResult(success=True)
                                            result = service.run()
                                            assert len(result.manual_apps) == 1
                                            assert (
                                                result.manual_apps[0].name == "Adobe Creative Cloud"
                                            )


class TestSetupStateModel:
    """Tests for SetupState model."""

    def test_setup_state_has_started_at(self):
        """SetupState has started_at timestamp."""
        from macsetup.models.config import SetupState

        now = datetime.now(UTC)
        state = SetupState(started_at=now, profile="default")
        assert state.started_at == now

    def test_setup_state_has_profile(self):
        """SetupState has profile name."""
        from macsetup.models.config import SetupState

        state = SetupState(started_at=datetime.now(UTC), profile="work")
        assert state.profile == "work"

    def test_setup_state_has_completed_items(self):
        """SetupState tracks completed items."""
        from macsetup.models.config import SetupState

        state = SetupState(
            started_at=datetime.now(UTC),
            profile="default",
            completed_items=["formula:git", "cask:vscode"],
        )
        assert len(state.completed_items) == 2

    def test_setup_state_has_failed_items(self):
        """SetupState tracks failed items."""
        from macsetup.models.config import FailedItem, SetupState

        failed = FailedItem(
            type="cask",
            identifier="docker",
            error="Requires Rosetta",
            timestamp=datetime.now(UTC),
        )
        state = SetupState(started_at=datetime.now(UTC), profile="default", failed_items=[failed])
        assert len(state.failed_items) == 1

    def test_setup_state_has_status(self):
        """SetupState has status field."""
        from macsetup.models.config import SetupState

        state = SetupState(started_at=datetime.now(UTC), profile="default", status="completed")
        assert state.status == "completed"


class TestFailedItemModel:
    """Tests for FailedItem model."""

    def test_failed_item_has_type(self):
        """FailedItem has type field."""
        from macsetup.models.config import FailedItem

        item = FailedItem(
            type="cask", identifier="docker", error="error", timestamp=datetime.now(UTC)
        )
        assert item.type == "cask"

    def test_failed_item_has_identifier(self):
        """FailedItem has identifier field."""
        from macsetup.models.config import FailedItem

        item = FailedItem(
            type="cask", identifier="docker", error="error", timestamp=datetime.now(UTC)
        )
        assert item.identifier == "docker"

    def test_failed_item_has_error(self):
        """FailedItem has error field."""
        from macsetup.models.config import FailedItem

        item = FailedItem(
            type="cask",
            identifier="docker",
            error="Requires Rosetta",
            timestamp=datetime.now(UTC),
        )
        assert item.error == "Requires Rosetta"

    def test_failed_item_has_timestamp(self):
        """FailedItem has timestamp field."""
        from macsetup.models.config import FailedItem

        now = datetime.now(UTC)
        item = FailedItem(type="cask", identifier="docker", error="error", timestamp=now)
        assert item.timestamp == now
