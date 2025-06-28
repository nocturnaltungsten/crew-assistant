# Provider Registry
# Dynamic discovery and factory for AI providers

from .base import BaseProvider
from .lmstudio import LMStudioProvider
from .ollama import OllamaProvider


class ProviderRegistry:
    """Registry for managing AI providers."""

    _providers: dict[str, type[BaseProvider]] = {}
    _instances: dict[str, BaseProvider] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[BaseProvider]):
        """Register a provider class."""
        cls._providers[name] = provider_class

    @classmethod
    def get_provider(cls, name: str, config: dict) -> BaseProvider:
        """Get or create provider instance."""
        if name not in cls._instances:
            if name not in cls._providers:
                raise ValueError(f"Unknown provider: {name}")

            cls._instances[name] = cls._providers[name](config)

        return cls._instances[name]

    @classmethod
    def list_providers(cls) -> list[str]:
        """Get list of registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def get_available_providers(cls) -> list[dict]:
        """Get list of available (online) providers with info."""
        available = []

        for name, provider_class in cls._providers.items():
            # Create temporary instance with default config
            default_configs = {
                "ollama": {"base_url": "http://localhost:11434"},
                "lmstudio": {"base_url": "http://localhost:1234/v1"}
            }

            try:
                config = default_configs.get(name, {})
                temp_provider = provider_class(config)

                if temp_provider.is_available:
                    available.append({
                        "name": name,
                        "display_name": temp_provider.display_name,
                        "base_url": config.get("base_url", "Unknown"),
                        "description": cls._get_provider_description(name),
                        "status": "online"
                    })
                else:
                    available.append({
                        "name": name,
                        "display_name": temp_provider.display_name,
                        "base_url": config.get("base_url", "Unknown"),
                        "description": cls._get_provider_description(name),
                        "status": "offline"
                    })
            except Exception:
                # Provider failed to initialize
                available.append({
                    "name": name,
                    "display_name": name.title(),
                    "base_url": "Unknown",
                    "description": cls._get_provider_description(name),
                    "status": "error"
                })

        return available

    @classmethod
    def _get_provider_description(cls, name: str) -> str:
        """Get human-readable description for provider."""
        descriptions = {
            "ollama": "Local Ollama server with native API",
            "lmstudio": "Local LM Studio server with OpenAI-compatible API"
        }
        return descriptions.get(name, f"{name.title()} AI provider")

    @classmethod
    def reset(cls):
        """Clear all provider instances (useful for testing)."""
        cls._instances.clear()


# Register built-in providers
ProviderRegistry.register("ollama", OllamaProvider)
ProviderRegistry.register("lmstudio", LMStudioProvider)


def get_provider(name: str, config: dict) -> BaseProvider:
    """Convenience function to get provider instance."""
    return ProviderRegistry.get_provider(name, config)


def list_available_providers() -> list[dict]:
    """Convenience function to list available providers."""
    return ProviderRegistry.get_available_providers()
