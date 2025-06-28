# LM Studio Provider Implementation
# OpenAI-compatible API integration

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


class LMStudioProvider(BaseProvider):
    """LM Studio AI provider implementation."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:1234/v1").rstrip("/")
        self.api_key = config.get("api_key", "not-needed-for-local")
        self.timeout = config.get("timeout", 30)

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        **kwargs
    ) -> ChatResponse:
        """Send chat messages to LM Studio."""

        # Convert to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", 500),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})

            return ChatResponse(
                content=message.get("content", ""),
                model=model,
                provider="lmstudio",
                tokens_used=result.get("usage", {}).get("total_tokens"),
                finish_reason=choice.get("finish_reason", "completed")
            )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to LM Studio at {self.base_url}")
        except requests.exceptions.Timeout:
            raise ConnectionError(f"LM Studio request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found in LM Studio")
            raise ConnectionError(f"LM Studio HTTP error: {e}")
        except Exception as e:
            raise ConnectionError(f"LM Studio error: {e}")

    def list_models(self) -> list[ModelInfo]:
        """Get available models from LM Studio."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            response.raise_for_status()

            models_data = response.json().get("data", [])
            models = []

            for model in models_data:
                model_id = model.get("id", "unknown")

                # Determine compatibility based on name patterns
                compatibility = self._categorize_compatibility(model_id)

                models.append(ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider="lmstudio",
                    compatibility=compatibility["status"],
                    description=compatibility["reason"]
                ))

            return models

        except Exception as e:
            raise ConnectionError(f"Failed to fetch LM Studio models: {e}")

    def test_connection(self) -> bool:
        """Test LM Studio connection."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=5)
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
