# Provider Base Classes
# Clean abstraction for AI providers

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    name: str
    provider: str
    compatibility: str  # "compatible", "incompatible", "unknown"
    description: str
    size: str | None = None
    context_length: int | None = None


@dataclass
class ChatMessage:
    """Standardized chat message format."""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class ChatResponse:
    """Standardized response from provider."""
    content: str
    model: str
    provider: str
    tokens_used: int | None = None
    finish_reason: str | None = None


class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self.name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs
    ) -> ChatResponse:
        """Send chat messages and get response."""
        pass

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """Get list of available models."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if provider is available and responding."""
        pass

    def test_model(self, model: str) -> tuple[bool, str]:
        """Test if a specific model works."""
        try:
            test_messages = [ChatMessage(role="user", content="Hello")]
            response = self.chat(test_messages, model, max_tokens=10)
            return True, f"Model '{model}' is working"
        except Exception as e:
            return False, f"Model '{model}' failed: {str(e)}"

    @property
    def display_name(self) -> str:
        """Human-readable provider name."""
        return self.name.title()

    @property
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        return self.test_connection()


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    pass


class ModelNotFoundError(ProviderError):
    """Raised when requested model is not available."""
    pass


class ConnectionError(ProviderError):
    """Raised when provider connection fails."""
    pass
