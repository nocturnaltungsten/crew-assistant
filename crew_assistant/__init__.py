"""Crew Assistant - Local-first AI orchestration platform."""

__version__ = "0.2.0"
__author__ = "Crew Assistant Team"
__email__ = "nocturnaltungsten@protonmail.com"

from .config import Settings, get_settings

__all__ = ["Settings", "get_settings", "__version__"]