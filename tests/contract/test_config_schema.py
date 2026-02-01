"""Contract tests for config schema validation."""

import pytest
from jsonschema import ValidationError, validate

from macsetup.models.schema import load_schema


@pytest.fixture
def schema():
    """Load the config schema."""
    return load_schema()


class TestConfigSchemaValidation:
    """Tests for config.schema.json validation."""

    def test_valid_minimal_config(self, schema):
        """Minimal valid configuration passes validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {},
            },
        }
        validate(instance=config, schema=schema)

    def test_valid_full_config(self, schema):
        """Full configuration with all fields passes validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2.1",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {
                    "description": "Full machine setup",
                    "applications": {
                        "homebrew": {
                            "taps": ["homebrew/cask-fonts"],
                            "formulas": ["git", "python", "node"],
                            "casks": ["visual-studio-code", "docker"],
                        },
                        "mas": [{"id": 497799835, "name": "Xcode"}],
                        "manual": [
                            {
                                "name": "Adobe Creative Cloud",
                                "url": "https://www.adobe.com/creativecloud",
                            }
                        ],
                    },
                    "dotfiles": [
                        {"path": ".zshrc"},
                        {"path": ".gitconfig", "mode": "copy"},
                        {"path": ".config/starship.toml", "template": True},
                    ],
                    "preferences": [
                        {
                            "domain": "com.apple.dock",
                            "key": "autohide",
                            "value": True,
                            "type": "bool",
                        }
                    ],
                },
                "work": {
                    "description": "Work profile",
                    "extends": "default",
                },
            },
        }
        validate(instance=config, schema=schema)

    def test_missing_version_fails(self, schema):
        """Config without version fails validation."""
        config = {
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {"default": {}},
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=config, schema=schema)
        assert "'version' is a required property" in str(exc_info.value)

    def test_missing_metadata_fails(self, schema):
        """Config without metadata fails validation."""
        config = {
            "version": "1.0",
            "profiles": {"default": {}},
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=config, schema=schema)
        assert "'metadata' is a required property" in str(exc_info.value)

    def test_missing_profiles_fails(self, schema):
        """Config without profiles fails validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=config, schema=schema)
        assert "'profiles' is a required property" in str(exc_info.value)

    def test_empty_profiles_fails(self, schema):
        """Config with empty profiles dict fails validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {},
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=config, schema=schema)
        assert "minProperties" in str(exc_info.value) or "should have at least" in str(
            exc_info.value
        )

    def test_invalid_version_format_fails(self, schema):
        """Config with invalid version format fails validation."""
        config = {
            "version": "v1.0.0",  # Invalid: should be "1.0"
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {"default": {}},
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_macos_version_format_fails(self, schema):
        """Config with invalid macOS version format fails validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "Sonoma",  # Invalid: should be "14.2"
                "tool_version": "1.0.0",
            },
            "profiles": {"default": {}},
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_dotfile_path_with_traversal_fails(self, schema):
        """Dotfile path with directory traversal fails validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {
                    "dotfiles": [{"path": "../etc/passwd"}],  # Invalid: directory traversal
                }
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_dotfile_path_absolute_fails(self, schema):
        """Dotfile path that is absolute fails validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {
                    "dotfiles": [{"path": "/etc/passwd"}],  # Invalid: absolute path
                }
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_dotfile_mode_fails(self, schema):
        """Dotfile with invalid mode fails validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {
                    "dotfiles": [{"path": ".zshrc", "mode": "hardlink"}],  # Invalid mode
                }
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_homebrew_tap_format_fails(self, schema):
        """Homebrew tap with invalid format fails validation."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {
                    "applications": {
                        "homebrew": {
                            "taps": ["invalid-tap-format"],  # Invalid: should be owner/repo
                        }
                    }
                }
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_mas_app_requires_id_and_name(self, schema):
        """Mac App Store app requires both id and name."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {
                    "applications": {
                        "mas": [{"name": "Xcode"}],  # Missing id
                    }
                }
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=config, schema=schema)
        assert "'id' is a required property" in str(exc_info.value)

    def test_preference_type_must_be_valid(self, schema):
        """Preference type must be one of the valid options."""
        config = {
            "version": "1.0",
            "metadata": {
                "captured_at": "2026-01-31T10:00:00Z",
                "source_machine": "MacBook-Pro",
                "macos_version": "14.2",
                "tool_version": "1.0.0",
            },
            "profiles": {
                "default": {
                    "preferences": [
                        {
                            "domain": "com.apple.dock",
                            "key": "test",
                            "value": "test",
                            "type": "invalid_type",
                        }
                    ]
                }
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)
