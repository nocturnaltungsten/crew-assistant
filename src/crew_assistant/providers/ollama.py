# Enhanced Ollama Provider Implementation
# Production-grade native Ollama API integration

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


class OllamaProvider(BaseProvider):
    """Production Ollama AI provider with native API and streaming support."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434").rstrip("/")

        # Enhanced configuration
        self.connection_pool_size = config.get("connection_pool_size", 8)
        self.keep_alive_timeout = config.get("keep_alive_timeout", 30)
        self.stream_timeout = config.get("stream_timeout", 300)
        self.pull_timeout = config.get("pull_timeout", 600)  # For model pulling

        # Initialize HTTP clients with connection pooling
        self._sync_client = requests.Session()
        self._sync_client.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "CrewAssistant/1.0.0 (Ollama Provider)",
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

        logger.info(f"Ollama provider initialized with pool size {self.connection_pool_size}")

    def chat(self, messages: list[ChatMessage], model: str, **kwargs: Any) -> ChatResponse:
        """Send chat messages to Ollama with enhanced error handling."""
        start_time = time.time()

        # Convert to Ollama format
        ollama_messages = []
        for msg in messages:
            formatted_msg = {"role": msg.role, "content": msg.content}
            # Ollama doesn't support 'name' field like OpenAI
            ollama_messages.append(formatted_msg)

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 500),
                "top_p": kwargs.get("top_p", 0.9),
                "repeat_penalty": kwargs.get("frequency_penalty", 1.0)
                + 1.0,  # Convert to Ollama format
                "seed": kwargs.get("seed", -1),
                "top_k": kwargs.get("top_k", 40),
            },
            "keep_alive": "5m",  # Keep model loaded for 5 minutes
        }

        # Generate request ID for tracking
        request_id = f"ollama_{int(time.time() * 1000)}_{hash(str(payload)) % 10000}"

        logger.debug(
            f"[{request_id}] Sending chat request to Ollama: {len(ollama_messages)} messages"
        )

        try:
            response = self._sync_client.post(
                f"{self.base_url}/api/chat", json=payload, timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            message = result.get("message", {})

            response_time = time.time() - start_time

            # Extract token usage if available
            tokens_used = None
            prompt_tokens = None
            completion_tokens = None

            if "eval_count" in result:
                completion_tokens = result.get("eval_count", 0)
                prompt_tokens = result.get("prompt_eval_count", 0)
                tokens_used = (prompt_tokens or 0) + (completion_tokens or 0)

            chat_response = ChatResponse(
                content=message.get("content", ""),
                model=model,
                provider="ollama",
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=result.get("done_reason", "completed"),
                response_time=response_time,
                request_id=request_id,
            )

            logger.debug(
                f"[{request_id}] Ollama response: {len(chat_response.content)} chars in {response_time:.2f}s"
            )
            return chat_response

        except requests.exceptions.ConnectionError as e:
            logger.error(f"[{request_id}] Ollama connection error: {e}")
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")
        except requests.exceptions.Timeout:
            logger.error(f"[{request_id}] Ollama timeout after {self.timeout}s")
            raise ProviderTimeoutError(f"Ollama request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"[{request_id}] Ollama HTTP error: {e.response.status_code} - {e.response.text if e.response else 'No response'}"
            )
            if e.response and e.response.status_code == 404:
                # Model might not be pulled yet
                error_text = e.response.text
                if "model" in error_text.lower() and "not found" in error_text.lower():
                    raise ModelNotFoundError(
                        f"Model '{model}' not found. Try pulling it first with: ollama pull {model}"
                    )
                raise ModelNotFoundError(f"Model '{model}' not found in Ollama")
            elif e.response and e.response.status_code == 400:
                raise ConnectionError("Ollama bad request - check model name and parameters")
            raise ConnectionError(f"Ollama HTTP error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"[{request_id}] Invalid JSON response from Ollama: {e}")
            raise ConnectionError(f"Invalid JSON response from Ollama: {e}")
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected Ollama error: {e}")
            raise ConnectionError(f"Ollama error: {e}")

    async def chat_async(
        self, messages: list[ChatMessage], model: str, **kwargs: Any
    ) -> ChatResponse:
        """Async chat with Ollama using connection pooling."""
        if not self._async_client:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(
                    max_keepalive_connections=self.connection_pool_size,
                    max_connections=self.connection_pool_size * 2,
                    keepalive_expiry=self.keep_alive_timeout,
                ),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CrewAssistant/1.0.0 (Ollama Provider Async)",
                },
            )

        start_time = time.time()

        # Convert to Ollama format
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 500),
                "top_p": kwargs.get("top_p", 0.9),
                "repeat_penalty": kwargs.get("frequency_penalty", 1.0) + 1.0,
                "seed": kwargs.get("seed", -1),
                "top_k": kwargs.get("top_k", 40),
            },
            "keep_alive": "5m",
        }

        request_id = f"ollama_async_{int(time.time() * 1000)}_{hash(str(payload)) % 10000}"

        try:
            response = await self._async_client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()

            result = response.json()
            message = result.get("message", {})

            response_time = time.time() - start_time

            # Extract token usage
            tokens_used = None
            prompt_tokens = None
            completion_tokens = None

            if "eval_count" in result:
                completion_tokens = result.get("eval_count", 0)
                prompt_tokens = result.get("prompt_eval_count", 0)
                tokens_used = (prompt_tokens or 0) + (completion_tokens or 0)

            return ChatResponse(
                content=message.get("content", ""),
                model=model,
                provider="ollama",
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=result.get("done_reason", "completed"),
                response_time=response_time,
                request_id=request_id,
            )

        except httpx.ConnectError as e:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(f"Ollama async request timed out: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found. Try: ollama pull {model}")
            raise ConnectionError(f"Ollama async HTTP error: {e}")
        except Exception as e:
            raise ConnectionError(f"Ollama async error: {e}")

    def chat_streaming(
        self, messages: list[ChatMessage], model: str, **kwargs: Any
    ) -> Iterator[ChatChunk]:
        """Stream chat response from Ollama (fallback to non-streaming)."""
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
        """Get available models from Ollama with enhanced metadata."""
        try:
            response = self._sync_client.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()

            models_data = response.json().get("models", [])
            models = []

            for model in models_data:
                model_id = model.get("name", "unknown")
                size_bytes = model.get("size", 0)

                # Parse model details
                model.get("details", {})

                # Determine compatibility and capabilities
                compatibility = self._categorize_compatibility(model_id)

                capabilities = ["chat", "completion"]
                if "instruct" in model_id.lower():
                    capabilities.append("instruction_following")
                if "code" in model_id.lower():
                    capabilities.append("code_generation")
                if "embed" in model_id.lower():
                    capabilities.append("embedding")

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
                        provider="ollama",
                        compatibility=compatibility["status"],
                        description=compatibility["reason"],
                        size=self._format_size(size_bytes),
                        capabilities=capabilities,
                        performance_tier=performance_tier,
                        last_tested=time.time(),
                    )
                )

            logger.info(f"Retrieved {len(models)} models from Ollama")
            return models

        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
            raise ConnectionError(f"Failed to fetch Ollama models: {e}")

    def test_connection(self) -> bool:
        """Test Ollama connection with enhanced diagnostics."""
        try:
            response = self._sync_client.get(f"{self.base_url}/api/tags", timeout=5)
            is_healthy = response.status_code == 200

            if is_healthy:
                logger.debug(f"Ollama health check passed: {response.status_code}")
            else:
                logger.warning(
                    f"Ollama health check failed: {response.status_code} - {response.text}"
                )

            return is_healthy
        except Exception as e:
            logger.error(f"Ollama health check error: {e}")
            return False

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            logger.info(f"Pulling model {model_name} from Ollama registry...")

            payload = {"name": model_name}
            response = self._sync_client.post(
                f"{self.base_url}/api/pull", json=payload, timeout=self.pull_timeout, stream=True
            )
            response.raise_for_status()

            # Process streaming response for progress updates
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        status = data.get("status", "")
                        if "completed" in status.lower():
                            logger.info(f"Successfully pulled model {model_name}")
                            return True
                        elif "error" in status.lower():
                            logger.error(f"Error pulling model {model_name}: {status}")
                            return False
                    except json.JSONDecodeError:
                        continue

            return True

        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    def show_model_info(self, model_name: str) -> dict[str, Any] | None:
        """Get detailed information about a specific model."""
        try:
            payload = {"name": model_name}
            response = self._sync_client.post(f"{self.base_url}/api/show", json=payload, timeout=10)
            response.raise_for_status()

            result: dict[str, Any] = response.json()
            return result

        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            return None

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
        """Get Ollama server information."""
        try:
            # Try to get server status
            response = self._sync_client.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])

            # Try to get version info
            version_info = {}
            try:
                version_response = self._sync_client.get(f"{self.base_url}/api/version", timeout=3)
                if version_response.status_code == 200:
                    version_info = version_response.json()
            except:
                pass

            return {
                "server_url": self.base_url,
                "status": "online",
                "model_count": len(models),
                "api_version": "ollama_native",
                "version_info": version_info,
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

    def _format_size(self, size_bytes: int) -> str:
        """Format model size in human-readable format."""
        if size_bytes == 0:
            return "Unknown"

        size_float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_float < 1024:
                return f"{size_float:.1f}{unit}"
            size_float /= 1024

        return f"{size_bytes:.1f}PB"

    def _categorize_compatibility(self, model_id: str) -> dict[str, str]:
        """Enhanced model compatibility categorization for Ollama."""
        model_lower = model_id.lower()

        # High compatibility patterns (known to work well with Ollama)
        high_compat_patterns = [
            "instruct",
            "chat",
            "conversational",
            "dialog",
            "assistant",
            "helpful",
            "alpaca",
            "vicuna",
            "orca",
        ]

        # Ollama-specific model families (generally compatible)
        ollama_families = [
            "llama",
            "mistral",
            "gemma",
            "qwen",
            "phi",
            "mixtral",
            "neural",
            "starling",
            "openhermes",
            "dolphin",
            "tinyllama",
            "codellama",
            "deepseek",
            "wizard",
            "zephyr",
            "openchat",
        ]

        # Incompatible patterns
        incompatible_patterns = ["base", "foundation", "embedding", "pretrain", "raw", "untuned"]

        # Specialized models
        code_patterns = ["code", "coding", "python", "javascript", "programming"]
        embedding_patterns = ["embed", "embedding", "nomic", "bge"]

        for pattern in high_compat_patterns:
            if pattern in model_lower:
                return {
                    "status": "compatible",
                    "reason": "Optimized for chat and instruction following",
                }

        for pattern in ollama_families:
            if pattern in model_lower:
                return {"status": "compatible", "reason": "Well-supported Ollama model family"}

        for pattern in code_patterns:
            if pattern in model_lower:
                return {
                    "status": "compatible",
                    "reason": "Code-specialized model with chat support",
                }

        for pattern in embedding_patterns:
            if pattern in model_lower:
                return {
                    "status": "incompatible",
                    "reason": "Embedding model - not for text generation",
                }

        for pattern in incompatible_patterns:
            if pattern in model_lower:
                return {
                    "status": "incompatible",
                    "reason": "Base model - requires fine-tuning for chat",
                }

        return {"status": "unknown", "reason": "Compatibility unknown - test recommended"}
