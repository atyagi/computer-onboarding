"""Unit tests for preview service."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from macsetup.models.config import (
    Applications,
    Configuration,
    Dotfile,
    HomebrewApps,
    MacApp,
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
                ),
                dotfiles=[Dotfile(path=".zshrc"), Dotfile(path=".gitconfig")],
                preferences=[
                    Preference(domain="com.apple.dock", key="autohide", value=True, type="bool")
                ],
            ),
            "work": Profile(
                name="work",
                extends="default",
                description="Work profile",
                applications=Applications(
                    homebrew=HomebrewApps(
                        formulas=["git", "python", "node"],
                        casks=["slack"],
                    ),
                ),
            ),
        },
    )


class TestPreviewService:
    """Tests for preview service (T072)."""

    def test_preview_service_can_be_created(self, sample_config):
        """Preview service can be instantiated."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="default")
        assert service is not None

    def test_preview_lists_all_items(self, sample_config):
        """Preview service lists all items that would be installed."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="default")
        items = service.preview()

        assert "taps" in items
        assert "formulas" in items
        assert "casks" in items
        assert "mas" in items
        assert "dotfiles" in items
        assert "preferences" in items

        assert items["taps"] == ["homebrew/cask-fonts"]
        assert items["formulas"] == ["git", "python"]
        assert items["casks"] == ["visual-studio-code"]
        assert len(items["mas"]) == 1
        assert len(items["dotfiles"]) == 2
        assert len(items["preferences"]) == 1

    def test_preview_handles_empty_profile(self):
        """Preview service handles profile with no items."""
        from macsetup.services.preview import PreviewService

        config = Configuration(
            version="1.0",
            metadata=Metadata(
                captured_at=datetime.now(UTC),
                source_machine="test",
                macos_version="14.2",
                tool_version="1.0.0",
            ),
            profiles={"empty": Profile(name="empty")},
        )
        service = PreviewService(config=config, profile="empty")
        items = service.preview()

        assert items["taps"] == []
        assert items["formulas"] == []
        assert items["casks"] == []
        assert items["mas"] == []
        assert items["dotfiles"] == []
        assert items["preferences"] == []

    def test_preview_raises_on_missing_profile(self, sample_config):
        """Preview service raises error for missing profile."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="nonexistent")
        with pytest.raises(ValueError, match="not found"):
            service.preview()


class TestProfileInheritance:
    """Tests for profile inheritance (T073)."""

    def test_resolve_profile_without_inheritance(self, sample_config):
        """Resolving a profile without extends returns it as-is."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="default")
        resolved = service.resolve_profile()

        assert resolved.name == "default"
        assert resolved.applications.homebrew.formulas == ["git", "python"]

    def test_resolve_profile_with_inheritance(self, sample_config):
        """Resolving a profile with extends merges parent fields."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="work")
        resolved = service.resolve_profile()

        # Work profile should have its own apps
        assert "node" in resolved.applications.homebrew.formulas
        assert "slack" in resolved.applications.homebrew.casks
        # Work profile inherits dotfiles and preferences from default
        assert len(resolved.dotfiles) == 2
        assert len(resolved.preferences) == 1

    def test_resolve_profile_child_overrides_parent(self, sample_config):
        """Child profile overrides parent values for same fields."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="work")
        resolved = service.resolve_profile()

        # Work profile defines its own formulas - should use work's
        assert resolved.applications.homebrew.formulas == ["git", "python", "node"]


class TestPreviewDiff:
    """Tests for diff calculation (T074)."""

    def test_diff_shows_new_items(self, sample_config):
        """Diff identifies items that need to be installed."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="default")

        with patch.object(service, "_get_installed_formulas", return_value=["git"]):
            with patch.object(service, "_get_installed_casks", return_value=[]):
                with patch.object(service, "_get_installed_taps", return_value=[]):
                    with patch.object(service, "_get_installed_mas", return_value=[]):
                        diff = service.diff()

        assert "python" in diff["formulas_to_install"]
        assert "git" not in diff["formulas_to_install"]
        assert "visual-studio-code" in diff["casks_to_install"]

    def test_diff_shows_already_installed(self, sample_config):
        """Diff identifies items that are already installed."""
        from macsetup.services.preview import PreviewService

        service = PreviewService(config=sample_config, profile="default")

        with patch.object(service, "_get_installed_formulas", return_value=["git", "python"]):
            with patch.object(service, "_get_installed_casks", return_value=["visual-studio-code"]):
                with patch.object(
                    service, "_get_installed_taps", return_value=["homebrew/cask-fonts"]
                ):
                    with patch.object(service, "_get_installed_mas", return_value=[497799835]):
                        diff = service.diff()

        assert diff["formulas_to_install"] == []
        assert diff["casks_to_install"] == []
        assert diff["taps_to_install"] == []
        assert diff["mas_to_install"] == []
