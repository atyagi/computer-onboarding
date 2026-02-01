"""Unit tests for data models."""

from datetime import UTC, datetime


class TestConfiguration:
    """Tests for Configuration model."""

    def test_configuration_requires_version(self):
        """Configuration must have a version string."""
        from macsetup.models.config import Configuration, Metadata

        metadata = Metadata(
            captured_at=datetime.now(UTC),
            source_machine="test-machine",
            macos_version="14.2",
            tool_version="1.0.0",
        )
        config = Configuration(version="1.0", metadata=metadata, profiles={})
        assert config.version == "1.0"

    def test_configuration_requires_metadata(self):
        """Configuration must have metadata."""
        from macsetup.models.config import Configuration, Metadata

        metadata = Metadata(
            captured_at=datetime.now(UTC),
            source_machine="test-machine",
            macos_version="14.2",
            tool_version="1.0.0",
        )
        config = Configuration(version="1.0", metadata=metadata, profiles={})
        assert config.metadata.source_machine == "test-machine"

    def test_configuration_has_profiles_dict(self):
        """Configuration must have a profiles dictionary."""
        from macsetup.models.config import Configuration, Metadata, Profile

        metadata = Metadata(
            captured_at=datetime.now(UTC),
            source_machine="test-machine",
            macos_version="14.2",
            tool_version="1.0.0",
        )
        default_profile = Profile(name="default")
        config = Configuration(
            version="1.0", metadata=metadata, profiles={"default": default_profile}
        )
        assert "default" in config.profiles
        assert config.profiles["default"].name == "default"


class TestMetadata:
    """Tests for Metadata model."""

    def test_metadata_requires_captured_at(self):
        """Metadata must have a captured_at timestamp."""
        from macsetup.models.config import Metadata

        now = datetime.now(UTC)
        metadata = Metadata(
            captured_at=now,
            source_machine="test-machine",
            macos_version="14.2",
            tool_version="1.0.0",
        )
        assert metadata.captured_at == now

    def test_metadata_requires_source_machine(self):
        """Metadata must have a source_machine hostname."""
        from macsetup.models.config import Metadata

        metadata = Metadata(
            captured_at=datetime.now(UTC),
            source_machine="MacBook-Pro",
            macos_version="14.2",
            tool_version="1.0.0",
        )
        assert metadata.source_machine == "MacBook-Pro"

    def test_metadata_requires_macos_version(self):
        """Metadata must have a macos_version."""
        from macsetup.models.config import Metadata

        metadata = Metadata(
            captured_at=datetime.now(UTC),
            source_machine="test-machine",
            macos_version="14.2.1",
            tool_version="1.0.0",
        )
        assert metadata.macos_version == "14.2.1"

    def test_metadata_requires_tool_version(self):
        """Metadata must have a tool_version."""
        from macsetup.models.config import Metadata

        metadata = Metadata(
            captured_at=datetime.now(UTC),
            source_machine="test-machine",
            macos_version="14.2",
            tool_version="1.0.0",
        )
        assert metadata.tool_version == "1.0.0"


class TestProfile:
    """Tests for Profile model."""

    def test_profile_requires_name(self):
        """Profile must have a name."""
        from macsetup.models.config import Profile

        profile = Profile(name="work")
        assert profile.name == "work"

    def test_profile_description_is_optional(self):
        """Profile description is optional."""
        from macsetup.models.config import Profile

        profile = Profile(name="default")
        assert profile.description is None

        profile_with_desc = Profile(name="work", description="Work machine config")
        assert profile_with_desc.description == "Work machine config"

    def test_profile_extends_is_optional(self):
        """Profile extends is optional for inheritance."""
        from macsetup.models.config import Profile

        profile = Profile(name="default")
        assert profile.extends is None

        profile_extending = Profile(name="work", extends="default")
        assert profile_extending.extends == "default"

    def test_profile_has_applications(self):
        """Profile can have applications."""
        from macsetup.models.config import Applications, Profile

        apps = Applications()
        profile = Profile(name="default", applications=apps)
        assert profile.applications is not None

    def test_profile_has_dotfiles_list(self):
        """Profile can have dotfiles list."""
        from macsetup.models.config import Dotfile, Profile

        dotfile = Dotfile(path=".zshrc")
        profile = Profile(name="default", dotfiles=[dotfile])
        assert len(profile.dotfiles) == 1
        assert profile.dotfiles[0].path == ".zshrc"

    def test_profile_has_preferences_list(self):
        """Profile can have preferences list."""
        from macsetup.models.config import Preference, Profile

        pref = Preference(domain="com.apple.dock", key="autohide", value=True, type="bool")
        profile = Profile(name="default", preferences=[pref])
        assert len(profile.preferences) == 1
        assert profile.preferences[0].domain == "com.apple.dock"


class TestApplications:
    """Tests for Applications model."""

    def test_applications_has_homebrew(self):
        """Applications can have homebrew apps."""
        from macsetup.models.config import Applications, HomebrewApps

        homebrew = HomebrewApps(formulas=["git"], casks=["visual-studio-code"], taps=[])
        apps = Applications(homebrew=homebrew)
        assert apps.homebrew is not None
        assert "git" in apps.homebrew.formulas

    def test_applications_has_mas_apps(self):
        """Applications can have Mac App Store apps."""
        from macsetup.models.config import Applications, MacApp

        mas_app = MacApp(id=497799835, name="Xcode")
        apps = Applications(mas=[mas_app])
        assert len(apps.mas) == 1
        assert apps.mas[0].id == 497799835

    def test_applications_has_manual_apps(self):
        """Applications can have manual apps."""
        from macsetup.models.config import Applications, ManualApp

        manual = ManualApp(name="Adobe Creative Cloud", url="https://adobe.com")
        apps = Applications(manual=[manual])
        assert len(apps.manual) == 1
        assert apps.manual[0].name == "Adobe Creative Cloud"


class TestHomebrewApps:
    """Tests for HomebrewApps model."""

    def test_homebrew_has_taps(self):
        """HomebrewApps can have taps."""
        from macsetup.models.config import HomebrewApps

        homebrew = HomebrewApps(taps=["homebrew/cask-fonts"])
        assert "homebrew/cask-fonts" in homebrew.taps

    def test_homebrew_has_formulas(self):
        """HomebrewApps can have formulas."""
        from macsetup.models.config import HomebrewApps

        homebrew = HomebrewApps(formulas=["git", "python", "node"])
        assert len(homebrew.formulas) == 3

    def test_homebrew_has_casks(self):
        """HomebrewApps can have casks."""
        from macsetup.models.config import HomebrewApps

        homebrew = HomebrewApps(casks=["visual-studio-code", "docker"])
        assert len(homebrew.casks) == 2


class TestMacApp:
    """Tests for MacApp model."""

    def test_mac_app_requires_id(self):
        """MacApp must have an id."""
        from macsetup.models.config import MacApp

        app = MacApp(id=497799835, name="Xcode")
        assert app.id == 497799835

    def test_mac_app_requires_name(self):
        """MacApp must have a name."""
        from macsetup.models.config import MacApp

        app = MacApp(id=497799835, name="Xcode")
        assert app.name == "Xcode"


class TestManualApp:
    """Tests for ManualApp model."""

    def test_manual_app_requires_name(self):
        """ManualApp must have a name."""
        from macsetup.models.config import ManualApp

        app = ManualApp(name="Adobe Creative Cloud")
        assert app.name == "Adobe Creative Cloud"

    def test_manual_app_url_is_optional(self):
        """ManualApp url is optional."""
        from macsetup.models.config import ManualApp

        app = ManualApp(name="Adobe Creative Cloud")
        assert app.url is None

        app_with_url = ManualApp(name="Adobe", url="https://adobe.com")
        assert app_with_url.url == "https://adobe.com"

    def test_manual_app_instructions_is_optional(self):
        """ManualApp instructions is optional."""
        from macsetup.models.config import ManualApp

        app = ManualApp(name="Adobe Creative Cloud", instructions="Download from website")
        assert app.instructions == "Download from website"


class TestDotfile:
    """Tests for Dotfile model."""

    def test_dotfile_requires_path(self):
        """Dotfile must have a path."""
        from macsetup.models.config import Dotfile

        dotfile = Dotfile(path=".zshrc")
        assert dotfile.path == ".zshrc"

    def test_dotfile_mode_defaults_to_symlink(self):
        """Dotfile mode defaults to symlink."""
        from macsetup.models.config import Dotfile

        dotfile = Dotfile(path=".zshrc")
        assert dotfile.mode == "symlink"

    def test_dotfile_mode_can_be_copy(self):
        """Dotfile mode can be copy."""
        from macsetup.models.config import Dotfile

        dotfile = Dotfile(path=".zshrc", mode="copy")
        assert dotfile.mode == "copy"

    def test_dotfile_template_defaults_to_false(self):
        """Dotfile template defaults to False."""
        from macsetup.models.config import Dotfile

        dotfile = Dotfile(path=".zshrc")
        assert dotfile.template is False


class TestPreference:
    """Tests for Preference model."""

    def test_preference_requires_domain(self):
        """Preference must have a domain."""
        from macsetup.models.config import Preference

        pref = Preference(domain="com.apple.dock")
        assert pref.domain == "com.apple.dock"

    def test_preference_key_is_optional(self):
        """Preference key is optional (None = entire domain)."""
        from macsetup.models.config import Preference

        pref = Preference(domain="com.apple.dock")
        assert pref.key is None

        pref_with_key = Preference(domain="com.apple.dock", key="autohide")
        assert pref_with_key.key == "autohide"

    def test_preference_value_can_be_any_type(self):
        """Preference value can be any type."""
        from macsetup.models.config import Preference

        pref_bool = Preference(domain="com.apple.dock", key="autohide", value=True, type="bool")
        assert pref_bool.value is True

        pref_int = Preference(domain="com.apple.dock", key="tilesize", value=48, type="int")
        assert pref_int.value == 48

        pref_str = Preference(domain="test", key="name", value="test", type="string")
        assert pref_str.value == "test"

    def test_preference_type_is_optional(self):
        """Preference type is optional."""
        from macsetup.models.config import Preference

        pref = Preference(domain="com.apple.dock", key="autohide", value=True)
        assert pref.type is None
