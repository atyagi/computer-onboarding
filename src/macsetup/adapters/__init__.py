"""External tool adapters for macsetup."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AdapterResult:
    """Result of an adapter operation."""

    success: bool
    message: str | None = None
    error: str | None = None


class Adapter(ABC):
    """Base interface for external tool adapters."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the external tool is available on the system."""
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the external tool."""
        pass
