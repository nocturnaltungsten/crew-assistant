# Provider Base Classes
# Production-grade abstraction for AI providers with optimizations

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


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
    capabilities: list[str] = field(default_factory=list)  # ["chat", "completion", "embedding"]
    performance_tier: str = "balanced"  # "fast", "balanced", "capable"
    last_tested: float = field(default_factory=time.time)


@dataclass
class ChatMessage:
    """Standardized chat message format."""

    role: str  # "user", "assistant", "system"
    content: str
    name: str | None = None
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatChunk:
    """Streaming response chunk."""

    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    tokens_used: int | None = None
    is_final: bool = False


@dataclass
class ProviderHealth:
    """Provider health status."""

    is_healthy: bool
    response_time: float
    last_check: float
    error_message: str | None = None
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0


@dataclass
class ProviderMetrics:
    """Provider performance metrics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_tokens: int = 0
    uptime_start: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0

    @property
    def failure_rate(self) -> float:
        return 100.0 - self.success_rate


@dataclass
class ChatResponse:
    """Standardized response from provider."""

    content: str
    model: str
    provider: str
    tokens_used: int | None = None
    finish_reason: str | None = None
    response_time: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cached: bool = False
    request_id: str | None = None


class BaseProvider(ABC):
    """Abstract base class for AI providers with production features."""

    def __init__(self, config: dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self.name = self.__class__.__name__.replace("Provider", "").lower()

        # Performance and reliability features
        self.metrics = ProviderMetrics()
        self.health = ProviderHealth(is_healthy=True, response_time=0.0, last_check=time.time())

        # Configuration with defaults
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.enable_streaming = config.get("enable_streaming", True)
        self.enable_caching = config.get("enable_caching", True)
        self.circuit_breaker_threshold = config.get("circuit_breaker_threshold", 5)

        # Internal state
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = 0.0
        self._circuit_breaker_open = False
        self._response_cache: dict[str, Any] = {}
        self._cache_ttl = config.get("cache_ttl", 300)  # 5 minutes

        logger.info(
            f"Initialized {self.display_name} provider with config: timeout={self.timeout}s, retries={self.max_retries}"
        )

    @abstractmethod
    def chat(self, messages: list[ChatMessage], model: str, **kwargs: Any) -> ChatResponse:
        """Send chat messages and get response."""
        pass

    async def chat_async(self, messages: list[ChatMessage], model: str, **kwargs: Any) -> ChatResponse:
        """Async version of chat (default implementation runs sync in thread)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.chat, messages, model, **kwargs)

    def chat_streaming(
        self, messages: list[ChatMessage], model: str, **kwargs: Any
    ) -> Iterator[ChatChunk]:
        """Stream chat response in chunks (override for native streaming)."""
        # Default implementation: convert regular response to single chunk
        response = self.chat(messages, model, **kwargs)
        yield ChatChunk(
            content=response.content,
            model=response.model,
            provider=response.provider,
            finish_reason=response.finish_reason,
            tokens_used=response.tokens_used,
            is_final=True,
        )

    def chat_with_retry(self, messages: list[ChatMessage], model: str, **kwargs: Any) -> ChatResponse:
        """Chat with automatic retry logic and circuit breaker."""
        if self._is_circuit_breaker_open():
            raise ConnectionError(f"Circuit breaker open for {self.name} provider")

        start_time = time.time()
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Check cache first
                cache_key = self._generate_cache_key(messages, model, kwargs)
                if self.enable_caching and cache_key in self._response_cache:
                    cached_data = self._response_cache[cache_key]
                    if time.time() - cached_data["timestamp"] < self._cache_ttl:
                        response: ChatResponse = cached_data["response"]
                        response.cached = True
                        response.response_time = time.time() - start_time
                        self._update_metrics(True, response.response_time)
                        return response

                # Make the actual request
                response = self.chat(messages, model, **kwargs)
                response.response_time = time.time() - start_time

                # Cache successful response
                if self.enable_caching:
                    self._response_cache[cache_key] = {
                        "response": response,
                        "timestamp": time.time(),
                    }

                # Reset circuit breaker on success
                self._circuit_breaker_failures = 0
                self._circuit_breaker_open = False

                self._update_metrics(True, response.response_time)
                self._update_health(True, response.response_time)

                return response

            except Exception as e:
                last_exception = e
                self._circuit_breaker_failures += 1
                self._circuit_breaker_last_failure = time.time()

                # Open circuit breaker if threshold reached
                if self._circuit_breaker_failures >= self.circuit_breaker_threshold:
                    self._circuit_breaker_open = True
                    logger.warning(
                        f"Circuit breaker opened for {self.name} provider after {self._circuit_breaker_failures} failures"
                    )

                if attempt < self.max_retries:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {self.name}, retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed for {self.name}: {e}")

        # All attempts failed
        total_time = time.time() - start_time
        self._update_metrics(False, total_time)
        self._update_health(False, total_time, str(last_exception))

        raise last_exception or ConnectionError(f"All retry attempts failed for {self.name}")

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
            return True, f"Model '{model}' is working (responded in {response.response_time:.2f}s)"
        except Exception as e:
            return False, f"Model '{model}' failed: {str(e)}"

    async def test_model_async(self, model: str) -> tuple[bool, str]:
        """Async version of model testing."""
        try:
            test_messages = [ChatMessage(role="user", content="Hello")]
            response = await self.chat_async(test_messages, model, max_tokens=10)
            return True, f"Model '{model}' is working (responded in {response.response_time:.2f}s)"
        except Exception as e:
            return False, f"Model '{model}' failed: {str(e)}"

    def batch_chat(self, requests: list[tuple[list[ChatMessage], str, dict]]) -> list[ChatResponse]:
        """Process multiple chat requests (override for native batch support)."""
        responses = []
        for messages, model, kwargs in requests:
            try:
                response = self.chat_with_retry(messages, model, **kwargs)
                responses.append(response)
            except Exception as e:
                # Create error response
                error_response = ChatResponse(
                    content=f"Error: {str(e)}",
                    model=model,
                    provider=self.name,
                    finish_reason="error",
                )
                responses.append(error_response)
        return responses

    async def batch_chat_async(
        self, requests: list[tuple[list[ChatMessage], str, dict]]
    ) -> list[ChatResponse]:
        """Async batch processing with concurrency."""
        tasks = [self.chat_async(messages, model, **kwargs) for messages, model, kwargs in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        responses: list[ChatResponse] = []
        for result in results:
            if isinstance(result, BaseException):
                responses.append(
                    ChatResponse(
                        content="",
                        model="unknown",
                        provider=self.name,
                        error=str(result),
                        tokens_used=0,
                        response_time=0.0,
                    )
                )
            else:
                responses.append(result)
        return responses

    @property
    def display_name(self) -> str:
        """Human-readable provider name."""
        return self.name.title()

    @property
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        if self._is_circuit_breaker_open():
            return False
        return self.test_connection()

    def get_health_status(self) -> ProviderHealth:
        """Get current health status."""
        # Update health with fresh connection test
        start_time = time.time()
        try:
            is_healthy = self.test_connection()
            response_time = time.time() - start_time
            self._update_health(is_healthy, response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self._update_health(False, response_time, str(e))

        return self.health

    def get_metrics(self) -> ProviderMetrics:
        """Get performance metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = ProviderMetrics()
        logger.info(f"Reset metrics for {self.name} provider")

    def clear_cache(self) -> None:
        """Clear response cache."""
        cleared_count = len(self._response_cache)
        self._response_cache.clear()
        logger.info(f"Cleared {cleared_count} cached responses for {self.name} provider")

    def _generate_cache_key(self, messages: list[ChatMessage], model: str, kwargs: dict) -> str:
        """Generate cache key for request."""
        import hashlib

        content = "".join([f"{msg.role}:{msg.content}" for msg in messages])
        cache_params = f"{model}:{content}:{sorted(kwargs.items())}"
        return hashlib.md5(cache_params.encode()).hexdigest()

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open."""
        if not self._circuit_breaker_open:
            return False

        # Auto-reset circuit breaker after 60 seconds
        if time.time() - self._circuit_breaker_last_failure > 60:
            self._circuit_breaker_open = False
            self._circuit_breaker_failures = 0
            logger.info(f"Circuit breaker auto-reset for {self.name} provider")
            return False

        return True

    def _update_metrics(self, success: bool, response_time: float) -> None:
        """Update performance metrics."""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        # Update average response time
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            self.metrics.average_response_time = (
                self.metrics.average_response_time * (self.metrics.total_requests - 1)
                + response_time
            ) / self.metrics.total_requests

    def _update_health(
        self, is_healthy: bool, response_time: float, error_message: str | None = None
    ) -> None:
        """Update health status."""
        self.health.is_healthy = is_healthy
        self.health.response_time = response_time
        self.health.last_check = time.time()
        self.health.error_message = error_message

        if not is_healthy:
            self.health.consecutive_failures += 1
        else:
            self.health.consecutive_failures = 0


class ProviderError(Exception):
    """Base exception for provider-related errors."""

    pass


class ModelNotFoundError(ProviderError):
    """Raised when requested model is not available."""

    pass


class ConnectionError(ProviderError):
    """Raised when provider connection fails."""

    pass


class CircuitBreakerOpenError(ProviderError):
    """Raised when circuit breaker is open."""

    pass


class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out."""

    pass
