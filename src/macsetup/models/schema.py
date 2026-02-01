"""JSON schema validation for macsetup configuration."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

# Find schema file relative to this module
_SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "schemas" / "config.schema.json"


def load_schema() -> dict:
    """Load the configuration schema from disk."""
    if not _SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {_SCHEMA_PATH}")
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def validate_config(config: dict) -> list[str]:
    """Validate a configuration dictionary against the schema.

    Args:
        config: The configuration dictionary to validate.

    Returns:
        A list of validation error messages. Empty list if valid.
    """
    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(config), key=lambda e: e.json_path):
        errors.append(f"{error.json_path}: {error.message}")
    return errors


def is_valid(config: dict) -> bool:
    """Check if a configuration dictionary is valid.

    Args:
        config: The configuration dictionary to validate.

    Returns:
        True if valid, False otherwise.
    """
    return len(validate_config(config)) == 0


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        message = f"Configuration validation failed with {len(errors)} error(s):\n"
        message += "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


def validate_config_strict(config: dict) -> None:
    """Validate configuration and raise if invalid.

    Args:
        config: The configuration dictionary to validate.

    Raises:
        ConfigValidationError: If validation fails.
    """
    errors = validate_config(config)
    if errors:
        raise ConfigValidationError(errors)
