# Provider Module
# Clean abstraction for AI providers

from .base import (
    BaseProvider,
    ChatMessage,
    ChatResponse,
    ConnectionError,
    ModelInfo,
    ModelNotFoundError,
    ProviderError,
)
from .lmstudio import LMStudioProvider
from .ollama import OllamaProvider
from .registry import ProviderRegistry, get_provider, list_available_providers

__all__ = [
    # Base classes
    "BaseProvider",
    "ModelInfo",
    "ChatMessage",
    "ChatResponse",

    # Exceptions
    "ProviderError",
    "ModelNotFoundError",
    "ConnectionError",

    # Providers
    "OllamaProvider",
    "LMStudioProvider",

    # Registry
    "ProviderRegistry",
    "get_provider",
    "list_available_providers"
]
