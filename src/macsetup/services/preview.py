"""Preview service for macsetup."""

from macsetup.adapters.homebrew import HomebrewAdapter
from macsetup.adapters.mas import MasAdapter
from macsetup.models.config import (
    Configuration,
    Profile,
)


class PreviewService:
    """Service for previewing what setup would do."""

    def __init__(self, config: Configuration, profile: str = "default"):
        self.config = config
        self.profile_name = profile
        self.homebrew = HomebrewAdapter()
        self.mas = MasAdapter()

    def _get_profile(self) -> Profile:
        """Get the requested profile."""
        if self.profile_name not in self.config.profiles:
            raise ValueError(f"Profile '{self.profile_name}' not found")
        return self.config.profiles[self.profile_name]

    def resolve_profile(self) -> Profile:
        """Resolve a profile with inheritance.

        If the profile has an `extends` field, merge parent profile fields.
        Child values override parent values for fields the child defines.
        """
        profile = self._get_profile()
        if not profile.extends:
            return profile

        if profile.extends not in self.config.profiles:
            raise ValueError(f"Parent profile '{profile.extends}' not found")

        parent = self.config.profiles[profile.extends]

        # Merge: child overrides parent for defined fields
        merged_apps = profile.applications or parent.applications
        merged_dotfiles = profile.dotfiles if profile.dotfiles else parent.dotfiles
        merged_preferences = profile.preferences if profile.preferences else parent.preferences

        return Profile(
            name=profile.name,
            description=profile.description or parent.description,
            applications=merged_apps,
            dotfiles=merged_dotfiles,
            preferences=merged_preferences,
        )

    def preview(self) -> dict:
        """Preview what setup would install.

        Returns:
            Dict with lists of items by category.
        """
        profile = self.resolve_profile()

        taps = []
        formulas = []
        casks = []
        mas_apps = []

        if profile.applications:
            if profile.applications.homebrew:
                taps = list(profile.applications.homebrew.taps)
                formulas = list(profile.applications.homebrew.formulas)
                casks = list(profile.applications.homebrew.casks)
            mas_apps = [{"id": a.id, "name": a.name} for a in profile.applications.mas]

        dotfiles = [{"path": d.path, "mode": d.mode} for d in profile.dotfiles]
        preferences = [
            {"domain": p.domain, "key": p.key, "value": p.value} for p in profile.preferences
        ]

        return {
            "taps": taps,
            "formulas": formulas,
            "casks": casks,
            "mas": mas_apps,
            "dotfiles": dotfiles,
            "preferences": preferences,
        }

    def _get_installed_formulas(self) -> list[str]:
        """Get currently installed Homebrew formulas."""
        if not self.homebrew.is_available():
            return []
        return self.homebrew.list_formulas()

    def _get_installed_casks(self) -> list[str]:
        """Get currently installed Homebrew casks."""
        if not self.homebrew.is_available():
            return []
        return self.homebrew.list_casks()

    def _get_installed_taps(self) -> list[str]:
        """Get currently installed Homebrew taps."""
        if not self.homebrew.is_available():
            return []
        return self.homebrew.list_taps()

    def _get_installed_mas(self) -> list[int]:
        """Get currently installed MAS app IDs."""
        if not self.mas.is_available():
            return []
        return [app_id for app_id, _ in self.mas.list_installed()]

    def diff(self) -> dict:
        """Compare config against current system state.

        Returns:
            Dict showing what needs to be installed vs what's already present.
        """
        profile = self.resolve_profile()

        installed_formulas = self._get_installed_formulas()
        installed_casks = self._get_installed_casks()
        installed_taps = self._get_installed_taps()
        installed_mas = self._get_installed_mas()

        taps = []
        formulas = []
        casks = []
        mas_apps = []

        if profile.applications and profile.applications.homebrew:
            brew = profile.applications.homebrew
            taps = brew.taps
            formulas = brew.formulas
            casks = brew.casks
        if profile.applications:
            mas_apps = profile.applications.mas

        return {
            "taps_to_install": [t for t in taps if t not in installed_taps],
            "taps_installed": [t for t in taps if t in installed_taps],
            "formulas_to_install": [f for f in formulas if f not in installed_formulas],
            "formulas_installed": [f for f in formulas if f in installed_formulas],
            "casks_to_install": [c for c in casks if c not in installed_casks],
            "casks_installed": [c for c in casks if c in installed_casks],
            "mas_to_install": [a for a in mas_apps if a.id not in installed_mas],
            "mas_installed": [a for a in mas_apps if a.id in installed_mas],
        }
