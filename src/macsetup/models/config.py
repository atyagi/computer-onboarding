"""Data models for macsetup configuration."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Metadata:
    """Contextual information about when/where configuration was captured."""

    captured_at: datetime
    source_machine: str
    macos_version: str
    tool_version: str


@dataclass
class HomebrewApps:
    """Homebrew package manager configuration."""

    taps: list[str] = field(default_factory=list)
    formulas: list[str] = field(default_factory=list)
    casks: list[str] = field(default_factory=list)


@dataclass
class MacApp:
    """Mac App Store application."""

    id: int
    name: str


@dataclass
class ManualApp:
    """Application requiring manual installation."""

    name: str
    url: str | None = None
    instructions: str | None = None


@dataclass
class Applications:
    """Container for all application sources."""

    homebrew: HomebrewApps | None = None
    mas: list[MacApp] = field(default_factory=list)
    manual: list[ManualApp] = field(default_factory=list)


@dataclass
class Dotfile:
    """User configuration file."""

    path: str
    mode: str = "symlink"
    template: bool = False


@dataclass
class Preference:
    """macOS system preference setting."""

    domain: str
    key: str | None = None
    value: Any | None = None
    type: str | None = None


@dataclass
class Profile:
    """A named subset of configuration for context-specific setups."""

    name: str
    description: str | None = None
    extends: str | None = None
    applications: Applications | None = None
    dotfiles: list[Dotfile] = field(default_factory=list)
    preferences: list[Preference] = field(default_factory=list)


@dataclass
class Configuration:
    """The root entity representing a complete machine configuration snapshot."""

    version: str
    metadata: Metadata
    profiles: dict[str, Profile]


@dataclass
class FailedItem:
    """Record of a failed installation."""

    type: str
    identifier: str
    error: str
    timestamp: datetime


@dataclass
class SetupState:
    """Tracks progress of setup operation for resume capability."""

    started_at: datetime
    profile: str
    completed_items: list[str] = field(default_factory=list)
    failed_items: list[FailedItem] = field(default_factory=list)
    status: str = "in_progress"


def _parse_metadata(data: dict) -> Metadata:
    """Parse metadata from YAML dict."""
    captured_at = data.get("captured_at")
    if isinstance(captured_at, str):
        captured_at = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    return Metadata(
        captured_at=captured_at,
        source_machine=data["source_machine"],
        macos_version=data["macos_version"],
        tool_version=data["tool_version"],
    )


def _parse_homebrew(data: dict | None) -> HomebrewApps | None:
    """Parse homebrew apps from YAML dict."""
    if data is None:
        return None
    return HomebrewApps(
        taps=data.get("taps", []),
        formulas=data.get("formulas", []),
        casks=data.get("casks", []),
    )


def _parse_mas_apps(data: list | None) -> list[MacApp]:
    """Parse Mac App Store apps from YAML list."""
    if data is None:
        return []
    return [MacApp(id=app["id"], name=app["name"]) for app in data]


def _parse_manual_apps(data: list | None) -> list[ManualApp]:
    """Parse manual apps from YAML list."""
    if data is None:
        return []
    return [
        ManualApp(
            name=app["name"],
            url=app.get("url"),
            instructions=app.get("instructions"),
        )
        for app in data
    ]


def _parse_applications(data: dict | None) -> Applications | None:
    """Parse applications from YAML dict."""
    if data is None:
        return None
    return Applications(
        homebrew=_parse_homebrew(data.get("homebrew")),
        mas=_parse_mas_apps(data.get("mas")),
        manual=_parse_manual_apps(data.get("manual")),
    )


def _parse_dotfiles(data: list | None) -> list[Dotfile]:
    """Parse dotfiles from YAML list."""
    if data is None:
        return []
    return [
        Dotfile(
            path=df["path"],
            mode=df.get("mode", "symlink"),
            template=df.get("template", False),
        )
        for df in data
    ]


def _parse_preferences(data: list | None) -> list[Preference]:
    """Parse preferences from YAML list."""
    if data is None:
        return []
    return [
        Preference(
            domain=pref["domain"],
            key=pref.get("key"),
            value=pref.get("value"),
            type=pref.get("type"),
        )
        for pref in data
    ]


def _parse_profile(name: str, data: dict) -> Profile:
    """Parse a profile from YAML dict."""
    return Profile(
        name=name,
        description=data.get("description"),
        extends=data.get("extends"),
        applications=_parse_applications(data.get("applications")),
        dotfiles=_parse_dotfiles(data.get("dotfiles")),
        preferences=_parse_preferences(data.get("preferences")),
    )


def load_config(path: Path) -> Configuration:
    """Load a configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A Configuration object.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    profiles = {}
    for profile_name, profile_data in data.get("profiles", {}).items():
        profiles[profile_name] = _parse_profile(profile_name, profile_data or {})

    return Configuration(
        version=data["version"],
        metadata=_parse_metadata(data["metadata"]),
        profiles=profiles,
    )


def _metadata_to_dict(metadata: Metadata) -> dict:
    """Convert Metadata to YAML-serializable dict."""
    captured_at = metadata.captured_at
    if captured_at.tzinfo is not None:
        captured_at_str = captured_at.isoformat().replace("+00:00", "Z")
    else:
        captured_at_str = captured_at.isoformat() + "Z"
    return {
        "captured_at": captured_at_str,
        "source_machine": metadata.source_machine,
        "macos_version": metadata.macos_version,
        "tool_version": metadata.tool_version,
    }


def _homebrew_to_dict(homebrew: HomebrewApps | None) -> dict | None:
    """Convert HomebrewApps to YAML-serializable dict."""
    if homebrew is None:
        return None
    result = {}
    if homebrew.taps:
        result["taps"] = homebrew.taps
    if homebrew.formulas:
        result["formulas"] = homebrew.formulas
    if homebrew.casks:
        result["casks"] = homebrew.casks
    return result if result else None


def _applications_to_dict(apps: Applications | None) -> dict | None:
    """Convert Applications to YAML-serializable dict."""
    if apps is None:
        return None
    result = {}
    homebrew = _homebrew_to_dict(apps.homebrew)
    if homebrew:
        result["homebrew"] = homebrew
    if apps.mas:
        result["mas"] = [{"id": a.id, "name": a.name} for a in apps.mas]
    if apps.manual:
        manual_list = []
        for m in apps.manual:
            md = {"name": m.name}
            if m.url:
                md["url"] = m.url
            if m.instructions:
                md["instructions"] = m.instructions
            manual_list.append(md)
        result["manual"] = manual_list
    return result if result else None


def _dotfiles_to_list(dotfiles: list[Dotfile]) -> list[dict] | None:
    """Convert dotfiles to YAML-serializable list."""
    if not dotfiles:
        return None
    result = []
    for df in dotfiles:
        d = {"path": df.path}
        if df.mode != "symlink":
            d["mode"] = df.mode
        if df.template:
            d["template"] = df.template
        result.append(d)
    return result


def _preferences_to_list(preferences: list[Preference]) -> list[dict] | None:
    """Convert preferences to YAML-serializable list."""
    if not preferences:
        return None
    result = []
    for pref in preferences:
        p = {"domain": pref.domain}
        if pref.key is not None:
            p["key"] = pref.key
        if pref.value is not None:
            p["value"] = pref.value
        if pref.type is not None:
            p["type"] = pref.type
        result.append(p)
    return result


def _profile_to_dict(profile: Profile) -> dict:
    """Convert Profile to YAML-serializable dict."""
    result = {}
    if profile.description:
        result["description"] = profile.description
    if profile.extends:
        result["extends"] = profile.extends
    apps = _applications_to_dict(profile.applications)
    if apps:
        result["applications"] = apps
    dotfiles = _dotfiles_to_list(profile.dotfiles)
    if dotfiles:
        result["dotfiles"] = dotfiles
    preferences = _preferences_to_list(profile.preferences)
    if preferences:
        result["preferences"] = preferences
    return result


def config_to_dict(config: Configuration) -> dict:
    """Convert Configuration to YAML-serializable dict.

    Args:
        config: The Configuration object to convert.

    Returns:
        A dictionary suitable for YAML serialization.
    """
    profiles = {}
    for name, profile in config.profiles.items():
        profiles[name] = _profile_to_dict(profile)

    return {
        "version": config.version,
        "metadata": _metadata_to_dict(config.metadata),
        "profiles": profiles,
    }


def save_config(config: Configuration, path: Path) -> None:
    """Save a configuration to a YAML file.

    Args:
        config: The Configuration object to save.
        path: Path to save the YAML configuration file.
    """
    data = config_to_dict(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
