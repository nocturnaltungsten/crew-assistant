# Enhanced LM Studio Provider Implementation
# Production-grade OpenAI-compatible API integration

import asyncio
import json
import time
from collections.abc import Iterator
from typing import Any

import httpx
import requests
from loguru import logger

from .base import (
    BaseProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    ConnectionError,
    ModelInfo,
    ModelNotFoundError,
    ProviderTimeoutError,
)


class LMStudioProvider(BaseProvider):
    """Production LM Studio AI provider with connection pooling and streaming."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:1234/v1").rstrip("/")
        self.api_key = config.get("api_key", "not-needed-for-local")

        # Enhanced configuration for persistent agentic workflows
        self.connection_pool_size = config.get("connection_pool_size", 10)
        self.keep_alive_timeout = config.get(
            "keep_alive_timeout", 300
        )  # 5 min for long conversations
        self.stream_timeout = config.get("stream_timeout", 600)  # 10 min for huge contexts

        # Initialize HTTP clients with connection pooling
        self._sync_client = requests.Session()
        self._sync_client.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "CrewAssistant/1.0.0 (LMStudio Provider)",
            }
        )

        # Configure connection pool
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.connection_pool_size,
            pool_maxsize=self.connection_pool_size,
            max_retries=0,  # We handle retries ourselves
        )
        self._sync_client.mount("http://", adapter)
        self._sync_client.mount("https://", adapter)

        # Async client for streaming and async operations
        self._async_client: httpx.AsyncClient | None = None

        logger.info(f"LM Studio provider initialized with pool size {self.connection_pool_size}")

    def chat(self, messages: list[ChatMessage], model: str, **kwargs: Any) -> ChatResponse:
        """Send chat messages to LM Studio with enhanced error handling."""
        start_time = time.time()

        # Convert to OpenAI format with enhanced metadata
        openai_messages = []
        for msg in messages:
            formatted_msg = {"role": msg.role, "content": msg.content}
            if msg.name:
                formatted_msg["name"] = msg.name
            openai_messages.append(formatted_msg)

        payload = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", 500),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "stream": False,
            "user": kwargs.get("user", "crew-assistant"),
        }

        # Generate request ID for tracking
        request_id = f"lms_{int(time.time() * 1000)}_{hash(str(payload)) % 10000}"

        logger.debug(
            f"[{request_id}] Sending chat request to LM Studio: {len(openai_messages)} messages"
        )

        try:
            response = self._sync_client.post(
                f"{self.base_url}/chat/completions", json=payload, timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = result.get("usage", {})

            response_time = time.time() - start_time

            chat_response = ChatResponse(
                content=message.get("content", ""),
                model=model,
                provider="lmstudio",
                tokens_used=usage.get("total_tokens"),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                finish_reason=choice.get("finish_reason", "completed"),
                response_time=response_time,
                request_id=request_id,
            )

            logger.debug(
                f"[{request_id}] LM Studio response: {len(chat_response.content)} chars in {response_time:.2f}s"
            )
            return chat_response

        except requests.exceptions.ConnectionError as e:
            logger.error(f"[{request_id}] LM Studio connection error: {e}")
            raise ConnectionError(f"Cannot connect to LM Studio at {self.base_url}: {e}")
        except requests.exceptions.Timeout:
            logger.error(f"[{request_id}] LM Studio timeout after {self.timeout}s")
            raise ProviderTimeoutError(f"LM Studio request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"[{request_id}] LM Studio HTTP error: {e.response.status_code} - {e.response.text if e.response else 'No response'}"
            )
            if e.response and e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found in LM Studio")
            elif e.response and e.response.status_code == 429:
                raise ConnectionError("LM Studio rate limit exceeded")
            raise ConnectionError(f"LM Studio HTTP error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"[{request_id}] Invalid JSON response from LM Studio: {e}")
            raise ConnectionError(f"Invalid JSON response from LM Studio: {e}")
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected LM Studio error: {e}")
            raise ConnectionError(f"LM Studio error: {e}")

    async def chat_async(
        self, messages: list[ChatMessage], model: str, **kwargs: Any
    ) -> ChatResponse:
        """Async chat with LM Studio using connection pooling."""
        if not self._async_client:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(
                    max_keepalive_connections=self.connection_pool_size,
                    max_connections=self.connection_pool_size * 2,
                    keepalive_expiry=self.keep_alive_timeout,
                ),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "CrewAssistant/1.0.0 (LMStudio Provider Async)",
                },
            )

        start_time = time.time()

        # Convert to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content, **({"name": msg.name} if msg.name else {})}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", 500),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "stream": False,
            "user": kwargs.get("user", "crew-assistant"),
        }

        request_id = f"lms_async_{int(time.time() * 1000)}_{hash(str(payload)) % 10000}"

        try:
            response = await self._async_client.post(
                f"{self.base_url}/chat/completions", json=payload
            )
            response.raise_for_status()

            result = response.json()
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = result.get("usage", {})

            response_time = time.time() - start_time

            return ChatResponse(
                content=message.get("content", ""),
                model=model,
                provider="lmstudio",
                tokens_used=usage.get("total_tokens"),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                finish_reason=choice.get("finish_reason", "completed"),
                response_time=response_time,
                request_id=request_id,
            )

        except httpx.ConnectError as e:
            raise ConnectionError(f"Cannot connect to LM Studio at {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(f"LM Studio async request timed out: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found in LM Studio")
            raise ConnectionError(f"LM Studio async HTTP error: {e}")
        except Exception as e:
            raise ConnectionError(f"LM Studio async error: {e}")

    def chat_streaming(
        self, messages: list[ChatMessage], model: str, **kwargs: Any
    ) -> Iterator[ChatChunk]:
        """Stream chat response from LM Studio (fallback to non-streaming)."""
        # For sync compatibility, use non-streaming response
        response = self.chat(messages, model, **kwargs)
        yield ChatChunk(
            content=response.content,
            model=response.model,
            provider=response.provider,
            finish_reason=response.finish_reason,
            tokens_used=response.tokens_used,
            is_final=True,
        )

    def list_models(self) -> list[ModelInfo]:
        """Get available models from LM Studio with enhanced metadata."""
        try:
            response = self._sync_client.get(f"{self.base_url}/models", timeout=10)
            response.raise_for_status()

            models_data = response.json().get("data", [])
            models = []

            for model in models_data:
                model_id = model.get("id", "unknown")

                # Extract additional metadata
                context_length = None
                if "context" in str(model).lower():
                    # Try to extract context length from model name/description
                    import re

                    context_match = re.search(r"(\d+)k?\s*(?:context|ctx)", str(model).lower())
                    if context_match:
                        context_length = int(context_match.group(1))
                        if "k" in context_match.group(0).lower():
                            context_length *= 1000

                # Determine compatibility and capabilities
                compatibility = self._categorize_compatibility(model_id)

                capabilities = ["chat", "completion"]
                if "instruct" in model_id.lower():
                    capabilities.append("instruction_following")
                if "code" in model_id.lower():
                    capabilities.append("code_generation")

                # Determine performance tier based on model name
                performance_tier = "standard"
                if any(x in model_id.lower() for x in ["large", "70b", "65b", "180b"]):
                    performance_tier = "high_quality"
                elif any(x in model_id.lower() for x in ["small", "7b", "8b", "13b"]):
                    performance_tier = "fast"

                models.append(
                    ModelInfo(
                        id=model_id,
                        name=model_id,
                        provider="lmstudio",
                        compatibility=compatibility["status"],
                        description=compatibility["reason"],
                        context_length=context_length,
                        capabilities=capabilities,
                        performance_tier=performance_tier,
                        last_tested=time.time(),
                    )
                )

            logger.info(f"Retrieved {len(models)} models from LM Studio")
            return models

        except Exception as e:
            logger.error(f"Failed to fetch LM Studio models: {e}")
            raise ConnectionError(f"Failed to fetch LM Studio models: {e}")

    def test_connection(self) -> bool:
        """Test LM Studio connection with enhanced diagnostics."""
        try:
            response = self._sync_client.get(f"{self.base_url}/models", timeout=5)
            is_healthy = response.status_code == 200

            if is_healthy:
                logger.debug(f"LM Studio health check passed: {response.status_code}")
            else:
                logger.warning(
                    f"LM Studio health check failed: {response.status_code} - {response.text}"
                )

            return is_healthy
        except Exception as e:
            logger.error(f"LM Studio health check error: {e}")
            return False

    def batch_chat(self, requests: list[tuple[list[ChatMessage], str, dict]]) -> list[ChatResponse]:
        """Optimized batch processing for LM Studio."""
        logger.info(f"Processing batch of {len(requests)} requests")
        start_time = time.time()

        responses = []
        for i, (messages, model, kwargs) in enumerate(requests):
            try:
                logger.debug(f"Processing batch request {i + 1}/{len(requests)}")
                response = self.chat(messages, model, **kwargs)
                responses.append(response)
            except Exception as e:
                logger.error(f"Batch request {i + 1} failed: {e}")
                error_response = ChatResponse(
                    content=f"Error: {str(e)}",
                    model=model,
                    provider="lmstudio",
                    finish_reason="error",
                    response_time=0.0,
                )
                responses.append(error_response)

        total_time = time.time() - start_time
        logger.info(f"Batch processing completed in {total_time:.2f}s")
        return responses

    async def batch_chat_async(
        self, requests: list[tuple[list[ChatMessage], str, dict]]
    ) -> list[ChatResponse]:
        """Async batch processing with concurrency control."""
        logger.info(f"Processing async batch of {len(requests)} requests")

        # Limit concurrency to avoid overwhelming LM Studio
        semaphore = asyncio.Semaphore(self.connection_pool_size)

        async def process_request(
            messages: list[ChatMessage], model: str, kwargs: dict
        ) -> ChatResponse:
            async with semaphore:
                try:
                    return await self.chat_async(messages, model, **kwargs)
                except Exception as e:
                    return ChatResponse(
                        content=f"Error: {str(e)}",
                        model=model,
                        provider="lmstudio",
                        finish_reason="error",
                        response_time=0.0,
                    )

        tasks = [process_request(messages, model, kwargs) for messages, model, kwargs in requests]

        return await asyncio.gather(*tasks)

    def get_model_info(self, model_id: str) -> ModelInfo | None:
        """Get detailed information about a specific model."""
        try:
            models = self.list_models()
            for model in models:
                if model.id == model_id:
                    return model
            return None
        except Exception as e:
            logger.error(f"Failed to get model info for {model_id}: {e}")
            return None

    def get_server_info(self) -> dict[str, Any]:
        """Get LM Studio server information."""
        try:
            # Try to get server status
            response = self._sync_client.get(f"{self.base_url}/models", timeout=5)
            response.raise_for_status()

            models = response.json().get("data", [])

            return {
                "server_url": self.base_url,
                "status": "online",
                "model_count": len(models),
                "api_version": "openai_compatible",
                "health_check_time": time.time(),
                "response_time": getattr(response, "elapsed", 0),
            }
        except Exception as e:
            return {
                "server_url": self.base_url,
                "status": "offline",
                "error": str(e),
                "health_check_time": time.time(),
            }

    def close(self) -> None:
        """Clean up connections."""
        if self._sync_client:
            self._sync_client.close()

        if self._async_client:
            asyncio.create_task(self._async_client.aclose())

    def __del__(self) -> None:
        """Cleanup on destruction."""
        self.close()

    def _categorize_compatibility(self, model_id: str) -> dict[str, str]:
        """Enhanced model compatibility categorization."""
        model_lower = model_id.lower()

        # High compatibility patterns (known to work well)
        high_compat_patterns = [
            "instruct",
            "chat",
            "conversational",
            "dialog",
            "assistant",
            "helpful",
            "alpaca",
            "vicuna",
        ]

        # Model family patterns (generally compatible)
        model_families = [
            "mistral",
            "llama",
            "gemma",
            "qwen",
            "phi",
            "mixtral",
            "solar",
            "neural",
            "orca",
            "starling",
            "openhermes",
        ]

        # Incompatible patterns
        incompatible_patterns = [
            "base",
            "foundation",
            "embedding",
            "code-only",
            "pretrain",
            "raw",
            "untuned",
        ]

        # Code-specific models (may work but not optimal)
        code_patterns = ["code", "coding", "python", "javascript", "programming"]

        for pattern in high_compat_patterns:
            if pattern in model_lower:
                return {
                    "status": "compatible",
                    "reason": "Optimized for chat and instruction following",
                }

        for pattern in model_families:
            if pattern in model_lower:
                return {"status": "compatible", "reason": "Known compatible model family"}

        for pattern in code_patterns:
            if pattern in model_lower:
                return {"status": "compatible", "reason": "Code-focused but supports chat format"}

        for pattern in incompatible_patterns:
            if pattern in model_lower:
                return {
                    "status": "incompatible",
                    "reason": "Base model - requires fine-tuning for chat",
                }

        return {"status": "unknown", "reason": "Compatibility unknown - test recommended"}
