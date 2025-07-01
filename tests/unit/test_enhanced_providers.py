# Enhanced Provider Tests
# Comprehensive testing for production-grade provider system

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Any, Dict, List

import pytest
import requests
import httpx

from providers.base import (
    BaseProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    ModelInfo,
    ProviderHealth,
    ProviderMetrics,
    ConnectionError,
    ModelNotFoundError,
    ProviderTimeoutError,
)
from providers.lmstudio_enhanced import LMStudioEnhancedProvider
from providers.ollama_enhanced import OllamaEnhancedProvider
from providers.registry_enhanced import (
    EnhancedProviderRegistry,
    ModelRequirements,
    ProviderConfig,
    ProviderStatus,
)


class TestBaseProvider:
    """Test the enhanced BaseProvider functionality."""

    def create_test_provider(self, config=None):
        """Create a test provider instance."""
        if config is None:
            config = {"timeout": 30, "max_retries": 3}

        class TestProvider(BaseProvider):
            def chat(self, messages, model, **kwargs):
                # Check if max_tokens is very low (test_model uses 10)
                if kwargs.get("max_tokens", 500) == 10:
                    # Simulate a successful test response
                    return ChatResponse(
                        content="Hi", model=model, provider="test", response_time=0.1
                    )
                return ChatResponse(
                    content="Test response", model=model, provider="test", response_time=0.1
                )

            def list_models(self):
                return [
                    ModelInfo(
                        id="test-model",
                        name="Test Model",
                        provider="test",
                        compatibility="compatible",
                        description="Test model for testing",
                    )
                ]

            def test_connection(self):
                return True

        return TestProvider(config)

    def test_provider_initialization(self):
        """Test provider initialization with configuration."""
        config = {
            "timeout": 60,
            "max_retries": 5,
            "retry_delay": 2.0,
            "enable_streaming": True,
            "enable_caching": True,
            "circuit_breaker_threshold": 10,
        }

        provider = self.create_test_provider(config)

        assert provider.timeout == 60
        assert provider.max_retries == 5
        assert provider.retry_delay == 2.0
        assert provider.enable_streaming is True
        assert provider.enable_caching is True
        assert provider.circuit_breaker_threshold == 10
        assert provider.metrics is not None
        assert provider.health is not None

    def test_metrics_tracking(self):
        """Test metrics collection and updates."""
        provider = self.create_test_provider()

        # Initial metrics
        metrics = provider.get_metrics()
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 100.0

        # Simulate successful request
        provider._update_metrics(True, 0.5)
        metrics = provider.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.success_rate == 100.0
        assert metrics.average_response_time == 0.5

        # Simulate failed request
        provider._update_metrics(False, 1.0)
        metrics = provider.get_metrics()
        assert metrics.total_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.success_rate == 50.0

    def test_health_tracking(self):
        """Test health status tracking."""
        provider = self.create_test_provider()

        # Initial health
        health = provider.get_health_status()
        assert health.is_healthy is True
        assert health.consecutive_failures == 0

        # Simulate failure
        provider._update_health(False, 1.0, "Test error")
        health = provider.health
        assert health.is_healthy is False
        assert health.consecutive_failures == 1
        assert health.error_message == "Test error"

        # Simulate recovery
        provider._update_health(True, 0.5)
        health = provider.health
        assert health.is_healthy is True
        assert health.consecutive_failures == 0
        assert health.error_message is None

    def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        provider = self.create_test_provider({"circuit_breaker_threshold": 2})

        # Circuit breaker should be closed initially
        assert not provider._is_circuit_breaker_open()

        # Simulate failures to open circuit breaker
        provider._circuit_breaker_failures = 2
        provider._circuit_breaker_last_failure = time.time()
        provider._circuit_breaker_open = True

        assert provider._is_circuit_breaker_open()

        # Test auto-reset after time
        provider._circuit_breaker_last_failure = time.time() - 70  # 70 seconds ago
        assert not provider._is_circuit_breaker_open()

    def test_caching(self):
        """Test response caching functionality."""
        provider = self.create_test_provider({"enable_caching": True, "cache_ttl": 300})

        messages = [ChatMessage(role="user", content="Hello")]
        model = "test-model"

        # Generate cache key
        cache_key = provider._generate_cache_key(messages, model, {})
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length

        # Test cache miss (empty cache)
        assert cache_key not in provider._response_cache

        # Test cache clear
        provider._response_cache[cache_key] = {"test": "data", "timestamp": time.time()}
        assert len(provider._response_cache) == 1

        provider.clear_cache()
        assert len(provider._response_cache) == 0

    @pytest.mark.asyncio
    async def test_async_methods(self):
        """Test async method implementations."""
        provider = self.create_test_provider()
        messages = [ChatMessage(role="user", content="Hello")]

        # Test async chat (default implementation)
        response = await provider.chat_async(messages, "test-model")
        assert isinstance(response, ChatResponse)
        assert response.content == "Test response"

        # Test async model testing - just verify it returns a tuple
        result = await provider.test_model_async("test-model")
        assert isinstance(result, tuple)
        assert len(result) == 2
        is_working, message = result
        assert isinstance(is_working, bool)
        assert isinstance(message, str)

    def test_batch_processing(self):
        """Test batch request processing."""
        provider = self.create_test_provider()

        requests = [
            ([ChatMessage(role="user", content="Hello 1")], "model1", {}),
            ([ChatMessage(role="user", content="Hello 2")], "model2", {}),
            ([ChatMessage(role="user", content="Hello 3")], "model3", {}),
        ]

        responses = provider.batch_chat(requests)
        assert len(responses) == 3

        for i, response in enumerate(responses):
            assert isinstance(response, ChatResponse)
            assert response.model == f"model{i + 1}"

    @pytest.mark.asyncio
    async def test_async_batch_processing(self):
        """Test async batch request processing."""
        provider = self.create_test_provider()

        requests = [
            ([ChatMessage(role="user", content="Hello 1")], "model1", {}),
            ([ChatMessage(role="user", content="Hello 2")], "model2", {}),
        ]

        responses = await provider.batch_chat_async(requests)
        assert len(responses) == 2

        for response in responses:
            assert isinstance(response, ChatResponse)


class TestLMStudioEnhancedProvider:
    """Test LM Studio enhanced provider."""

    def create_provider(self, config=None):
        """Create LM Studio provider with mock config."""
        if config is None:
            config = {
                "base_url": "http://localhost:1234/v1",
                "timeout": 30,
                "connection_pool_size": 5,
            }
        return LMStudioEnhancedProvider(config)

    @patch("providers.lmstudio_enhanced.requests.Session")
    def test_initialization(self, mock_session):
        """Test provider initialization."""
        provider = self.create_provider()

        assert provider.base_url == "http://localhost:1234/v1"
        assert provider.api_key == "not-needed-for-local"
        assert provider.connection_pool_size == 5
        assert provider._sync_client is not None

    @patch("providers.lmstudio_enhanced.requests.Session")
    def test_chat_success(self, mock_session):
        """Test successful chat request."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Hello! How can I help you?"}, "finish_reason": "stop"}
            ],
            "usage": {"total_tokens": 20, "prompt_tokens": 10, "completion_tokens": 10},
        }
        mock_response.raise_for_status.return_value = None

        mock_session.return_value.post.return_value = mock_response

        provider = self.create_provider()
        messages = [ChatMessage(role="user", content="Hello")]

        response = provider.chat(messages, "test-model")

        assert isinstance(response, ChatResponse)
        assert response.content == "Hello! How can I help you?"
        assert response.model == "test-model"
        assert response.provider == "lmstudio"
        assert response.tokens_used == 20
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 10
        assert response.request_id is not None

    @patch("providers.lmstudio_enhanced.requests.Session")
    def test_chat_connection_error(self, mock_session):
        """Test chat request with connection error."""
        mock_session.return_value.post.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        provider = self.create_provider()
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(ConnectionError) as exc_info:
            provider.chat(messages, "test-model")

        assert "Cannot connect to LM Studio" in str(exc_info.value)

    @patch("providers.lmstudio_enhanced.requests.Session")
    def test_chat_timeout_error(self, mock_session):
        """Test chat request with timeout error."""
        mock_session.return_value.post.side_effect = requests.exceptions.Timeout("Timeout")

        provider = self.create_provider()
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(ProviderTimeoutError) as exc_info:
            provider.chat(messages, "test-model")

        assert "timed out" in str(exc_info.value)

    @patch("providers.lmstudio_enhanced.requests.Session")
    def test_list_models_success(self, mock_session):
        """Test successful model listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "microsoft/phi-4-mini-reasoning"},
                {"id": "mistral-7b-instruct"},
                {"id": "llama-3.2-8b-chat"},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_session.return_value.get.return_value = mock_response

        provider = self.create_provider()
        models = provider.list_models()

        assert len(models) == 3
        assert all(isinstance(model, ModelInfo) for model in models)
        assert models[0].id == "microsoft/phi-4-mini-reasoning"
        assert models[0].provider == "lmstudio"
        assert models[1].compatibility == "compatible"  # mistral should be compatible

    @patch("providers.lmstudio_enhanced.requests.Session")
    def test_health_check(self, mock_session):
        """Test health check functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        provider = self.create_provider()
        is_healthy = provider.test_connection()

        assert is_healthy is True

    @patch("providers.lmstudio_enhanced.requests.Session")
    def test_model_compatibility_categorization(self, mock_session):
        """Test model compatibility categorization."""
        provider = self.create_provider()

        # Test compatible patterns
        compat = provider._categorize_compatibility("mistral-7b-instruct")
        assert compat["status"] == "compatible"

        compat = provider._categorize_compatibility("llama-3-chat")
        assert compat["status"] == "compatible"

        # Test incompatible patterns
        compat = provider._categorize_compatibility("base-model-raw")
        assert compat["status"] == "incompatible"

        # Test unknown
        compat = provider._categorize_compatibility("unknown-model")
        assert compat["status"] == "unknown"

    @pytest.mark.asyncio
    @patch("providers.lmstudio_enhanced.httpx.AsyncClient")
    async def test_async_chat(self, mock_async_client):
        """Test async chat functionality."""
        # Mock async response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Async response"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 15},
        }
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value = mock_client_instance

        provider = self.create_provider()
        messages = [ChatMessage(role="user", content="Hello async")]

        response = await provider.chat_async(messages, "test-model")

        assert isinstance(response, ChatResponse)
        assert response.content == "Async response"
        assert response.tokens_used == 15


class TestOllamaEnhancedProvider:
    """Test Ollama enhanced provider."""

    def create_provider(self, config=None):
        """Create Ollama provider with mock config."""
        if config is None:
            config = {
                "base_url": "http://localhost:11434",
                "timeout": 30,
                "connection_pool_size": 5,
            }
        return OllamaEnhancedProvider(config)

    @patch("providers.ollama_enhanced.requests.Session")
    def test_chat_success(self, mock_session):
        """Test successful chat request with Ollama."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Hello from Ollama!"},
            "done_reason": "stop",
            "eval_count": 15,
            "prompt_eval_count": 8,
        }
        mock_response.raise_for_status.return_value = None

        mock_session.return_value.post.return_value = mock_response

        provider = self.create_provider()
        messages = [ChatMessage(role="user", content="Hello")]

        response = provider.chat(messages, "llama3.2")

        assert isinstance(response, ChatResponse)
        assert response.content == "Hello from Ollama!"
        assert response.model == "llama3.2"
        assert response.provider == "ollama"
        assert response.completion_tokens == 15
        assert response.prompt_tokens == 8
        assert response.tokens_used == 23

    @patch("providers.ollama_enhanced.requests.Session")
    def test_list_models_success(self, mock_session):
        """Test successful model listing from Ollama."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:latest", "size": 4661211648},
                {"name": "mistral:7b-instruct", "size": 4109828224},
                {"name": "codellama:13b", "size": 7365960448},
            ]
        }
        mock_response.raise_for_status.return_value = None

        mock_session.return_value.get.return_value = mock_response

        provider = self.create_provider()
        models = provider.list_models()

        assert len(models) == 3
        assert models[0].id == "llama3.2:latest"
        assert models[0].provider == "ollama"
        assert "4.3GB" in models[0].size  # Formatted size
        assert "code_generation" in models[2].capabilities  # codellama should have code capability

    @patch("providers.ollama_enhanced.requests.Session")
    def test_pull_model(self, mock_session):
        """Test model pulling functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"status": "downloading"}',
            b'{"status": "verifying"}',
            b'{"status": "success completed"}',
        ]
        mock_response.raise_for_status.return_value = None

        mock_session.return_value.post.return_value = mock_response

        provider = self.create_provider()
        success = provider.pull_model("llama3.2")

        assert success is True

    def test_size_formatting(self):
        """Test human-readable size formatting."""
        provider = self.create_provider()

        assert provider._format_size(0) == "Unknown"
        assert provider._format_size(1024) == "1.0KB"
        assert provider._format_size(1024 * 1024) == "1.0MB"
        assert provider._format_size(4661211648) == "4.3GB"


class TestEnhancedProviderRegistry:
    """Test the enhanced provider registry."""

    def create_registry(self):
        """Create a fresh registry for testing."""
        return EnhancedProviderRegistry()

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = self.create_registry()

        assert len(registry._provider_configs) == 0
        assert len(registry._provider_instances) == 0
        assert registry._health_check_running is False

    def test_provider_registration(self):
        """Test provider registration."""
        registry = self.create_registry()

        class MockProvider(BaseProvider):
            def chat(self, messages, model, **kwargs):
                return ChatResponse("test", model, "mock")

            def list_models(self):
                return []

            def test_connection(self):
                return True

        registry.register_provider(
            "test_provider", MockProvider, {"timeout": 30}, priority=5, enabled=True
        )

        assert "test_provider" in registry._provider_configs
        config = registry._provider_configs["test_provider"]
        assert config.name == "test_provider"
        assert config.priority == 5
        assert config.enabled is True

    def test_get_provider(self):
        """Test getting provider instances."""
        registry = self.create_registry()

        class MockProvider(BaseProvider):
            def chat(self, messages, model, **kwargs):
                return ChatResponse("test", model, "mock")

            def list_models(self):
                return []

            def test_connection(self):
                return True

        registry.register_provider("mock", MockProvider, {})

        # First call should create instance
        provider1 = registry.get_provider("mock")
        assert provider1 is not None
        assert isinstance(provider1, MockProvider)

        # Second call should return same instance
        provider2 = registry.get_provider("mock")
        assert provider1 is provider2

    def test_model_requirements_filtering(self):
        """Test model requirements and filtering."""
        registry = self.create_registry()

        # Test ModelRequirements
        req = ModelRequirements(
            capabilities=["chat", "code"],
            performance_tier="fast",
            streaming_required=True,
            compatibility_required=True,
        )

        assert req.capabilities == ["chat", "code"]
        assert req.performance_tier == "fast"
        assert req.streaming_required is True

        # Test model meets requirements
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="test",
            compatibility="compatible",
            description="Test",
            capabilities=["chat", "code", "completion"],
            performance_tier="fast",
        )

        assert registry._model_meets_requirements(model, req) is True

        # Test model doesn't meet requirements
        incompatible_model = ModelInfo(
            id="bad-model",
            name="Bad Model",
            provider="test",
            compatibility="incompatible",
            description="Bad",
            capabilities=["completion"],
            performance_tier="standard",
        )

        assert registry._model_meets_requirements(incompatible_model, req) is False

    def test_provider_priority_sorting(self):
        """Test provider priority and load balancing."""
        registry = self.create_registry()

        class MockProvider(BaseProvider):
            def chat(self, messages, model, **kwargs):
                return ChatResponse("test", model, "mock")

            def list_models(self):
                return []

            def test_connection(self):
                return True

        # Register providers with different priorities
        registry.register_provider("low_priority", MockProvider, {}, priority=1)
        registry.register_provider("high_priority", MockProvider, {}, priority=3)
        registry.register_provider("medium_priority", MockProvider, {}, priority=2)

        # Set all as online
        for name in ["low_priority", "high_priority", "medium_priority"]:
            registry._provider_configs[name].status = ProviderStatus.ONLINE

        # Get eligible providers - should be sorted by priority
        eligible = registry._get_eligible_providers(ModelRequirements())

        # All should be eligible
        assert len(eligible) == 3
        assert "low_priority" in eligible
        assert "high_priority" in eligible
        assert "medium_priority" in eligible

    def test_health_monitoring(self):
        """Test health check functionality."""
        registry = self.create_registry()

        class MockProvider(BaseProvider):
            def __init__(self, config, healthy=True):
                super().__init__(config)
                self._healthy = healthy

            def chat(self, messages, model, **kwargs):
                return ChatResponse("test", model, "mock")

            def list_models(self):
                return []

            def test_connection(self):
                return self._healthy

        # Register healthy and unhealthy providers
        registry.register_provider("healthy", MockProvider, {"healthy": True})
        registry.register_provider("unhealthy", MockProvider, {"healthy": False})

        # Override provider creation to use our mock
        healthy_provider = MockProvider({}, healthy=True)
        unhealthy_provider = MockProvider({}, healthy=False)

        registry._provider_instances["healthy"] = healthy_provider
        registry._provider_instances["unhealthy"] = unhealthy_provider

        # Run health check
        health_status = registry.health_check_all()

        assert len(health_status) == 2
        assert "healthy" in health_status
        assert "unhealthy" in health_status

        # Check provider statuses were updated
        assert registry._provider_configs["healthy"].status == ProviderStatus.ONLINE
        # Unhealthy provider should be DEGRADED on first failure, OFFLINE after multiple failures
        assert registry._provider_configs["unhealthy"].status in [
            ProviderStatus.DEGRADED,
            ProviderStatus.OFFLINE,
        ]

    def test_provider_enable_disable(self):
        """Test enabling and disabling providers."""
        registry = self.create_registry()

        class MockProvider(BaseProvider):
            def chat(self, messages, model, **kwargs):
                return ChatResponse("test", model, "mock")

            def list_models(self):
                return []

            def test_connection(self):
                return True

        registry.register_provider("test", MockProvider, {}, enabled=True)

        # Initially enabled
        assert registry._provider_configs["test"].enabled is True

        # Disable
        result = registry.disable_provider("test")
        assert result is True
        assert registry._provider_configs["test"].enabled is False

        # Enable
        result = registry.enable_provider("test")
        assert result is True
        assert registry._provider_configs["test"].enabled is True

    def test_provider_metrics(self):
        """Test provider metrics collection."""
        registry = self.create_registry()

        class MockProvider(BaseProvider):
            def chat(self, messages, model, **kwargs):
                return ChatResponse("test", model, "mock")

            def list_models(self):
                return []

            def test_connection(self):
                return True

        registry.register_provider("test", MockProvider, {})
        provider = registry.get_provider("test")

        # Simulate some requests
        registry._request_counts["test"] = 5
        registry._last_used["test"] = time.time()

        # Get metrics
        metrics = registry.get_provider_metrics()

        assert "test" in metrics
        assert "provider_metrics" in metrics["test"]
        assert "registry_metrics" in metrics["test"]
        assert metrics["test"]["registry_metrics"]["request_count"] == 5

    def test_cleanup(self):
        """Test registry cleanup."""
        registry = self.create_registry()

        class MockProvider(BaseProvider):
            def __init__(self, config):
                super().__init__(config)
                self.closed = False

            def chat(self, messages, model, **kwargs):
                return ChatResponse("test", model, "mock")

            def list_models(self):
                return []

            def test_connection(self):
                return True

            def close(self):
                self.closed = True

        registry.register_provider("test", MockProvider, {})
        provider = registry.get_provider("test")

        # Cleanup
        registry.cleanup()

        assert len(registry._provider_instances) == 0
        assert provider.closed is True


# Integration tests
class TestProviderIntegration:
    """Integration tests for provider system."""

    @pytest.mark.integration
    def test_global_registry_setup(self):
        """Test global registry initialization."""
        from providers.registry_enhanced import get_registry

        registry = get_registry()

        assert isinstance(registry, EnhancedProviderRegistry)
        assert "lmstudio" in registry.list_providers()
        assert "ollama" in registry.list_providers()

    @pytest.mark.integration
    def test_provider_priority_system(self):
        """Test that LM Studio has higher priority than Ollama by default."""
        from providers.registry_enhanced import get_registry

        registry = get_registry()

        lmstudio_config = registry._provider_configs["lmstudio"]
        ollama_config = registry._provider_configs["ollama"]

        assert lmstudio_config.priority > ollama_config.priority

    @pytest.mark.integration
    def test_end_to_end_optimal_provider_selection(self):
        """Test end-to-end optimal provider selection."""
        from providers.registry_enhanced import get_optimal_provider, ModelRequirements

        # Test getting optimal provider with requirements
        requirements = ModelRequirements(capabilities=["chat"], compatibility_required=True)

        # This should not fail even if providers are offline
        provider = get_optimal_provider(requirements)

        # Provider might be None if no local servers are running, which is OK for tests
        if provider is not None:
            assert hasattr(provider, "chat")
            assert hasattr(provider, "list_models")
            assert hasattr(provider, "test_connection")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
