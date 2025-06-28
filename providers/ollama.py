# Ollama Provider Implementation
# Direct integration with Ollama API

from typing import Any

import requests

from .base import (
    BaseProvider,
    ChatMessage,
    ChatResponse,
    ConnectionError,
    ModelInfo,
    ModelNotFoundError,
)


class OllamaProvider(BaseProvider):
    """Ollama AI provider implementation."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434").rstrip("/")
        self.timeout = config.get("timeout", 30)

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs
    ) -> ChatResponse:
        """Send chat messages to Ollama."""

        # Convert to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 500),
                "top_p": kwargs.get("top_p", 0.9),
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            return ChatResponse(
                content=result.get("message", {}).get("content", ""),
                model=model,
                provider="ollama",
                finish_reason=result.get("done_reason", "completed")
            )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except requests.exceptions.Timeout:
            raise ConnectionError(f"Ollama request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found in Ollama")
            raise ConnectionError(f"Ollama HTTP error: {e}")
        except Exception as e:
            raise ConnectionError(f"Ollama error: {e}")

    def list_models(self) -> list[ModelInfo]:
        """Get available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()

            models_data = response.json().get("models", [])
            models = []

            for model in models_data:
                model_id = model.get("name", "unknown")

                # Determine compatibility based on name patterns
                compatibility = self._categorize_compatibility(model_id)

                models.append(ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider="ollama",
                    compatibility=compatibility["status"],
                    description=compatibility["reason"],
                    size=self._format_size(model.get("size", 0))
                ))

            return models

        except Exception as e:
            raise ConnectionError(f"Failed to fetch Ollama models: {e}")

    def test_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _categorize_compatibility(self, model_id: str) -> dict[str, str]:
        """Categorize model compatibility."""
        model_lower = model_id.lower()

        compatible_patterns = [
            "instruct", "chat", "conversational", "dialog",
            "mistral", "llama", "gemma", "qwen", "phi"
        ]

        incompatible_patterns = [
            "base", "foundation", "embedding", "code-only"
        ]

        for pattern in compatible_patterns:
            if pattern in model_lower:
                return {
                    "status": "compatible",
                    "reason": "Supports chat completion format"
                }

        for pattern in incompatible_patterns:
            if pattern in model_lower:
                return {
                    "status": "incompatible",
                    "reason": "Base model - needs fine-tuning for chat"
                }

        return {
            "status": "unknown",
            "reason": "May need testing - try UX mode first"
        }

    def _format_size(self, size_bytes: int) -> str:
        """Format model size in human-readable format."""
        if size_bytes == 0:
            return "Unknown"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024

        return f"{size_bytes:.1f}PB"
