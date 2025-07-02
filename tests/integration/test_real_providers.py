# REAL Integration Tests for Providers
# These tests connect to ACTUAL LM Studio and Ollama servers
# MOCK TESTS ARE A MOCKERY! These tests are THE REAL DEAL!


import pytest
import requests

# from crew_assistant.providers.lmstudio_enhanced import LMStudioEnhancedProvider  # TODO: Create enhanced providers
# from crew_assistant.providers.ollama_enhanced import OllamaEnhancedProvider  # TODO: Create enhanced providers
# from crew_assistant.providers.registry_enhanced import get_registry, ModelRequirements  # TODO: Create enhanced providers
from crew_assistant.providers.base import ChatMessage, ChatResponse, ModelInfo


def check_server_running(url: str) -> bool:
    """Check if a server is actually running."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False


def get_available_model(provider, exclude_embedding=True) -> str | None:
    """Get the best available model for testing (prefer 8-14GB tool-trained models)."""
    try:
        models = provider.list_models()

        # Prioritize models for testing (avoid 30B+ models, prefer tool-trained)
        preferred_patterns = [
            "instruct",
            "chat",
            "tool",
            "function",
            "agent",
            "8b",
            "7b",
            "13b",
            "14b",
            "12b",  # Smaller model sizes
        ]

        # Avoid large models for testing
        avoid_patterns = ["30b", "32b", "27b", "70b", "65b", "180b", "embed", "embedding"]

        # First pass: Find preferred tool-trained compatible models
        for model in models:
            if any(avoid in model.id.lower() for avoid in avoid_patterns):
                continue

            if model.compatibility == "compatible" and any(
                pattern in model.id.lower() for pattern in preferred_patterns
            ):
                print(f"✅ Selected optimal testing model: {model.id}")
                return model.id

        # Second pass: Any compatible model that's not too large
        for model in models:
            if any(avoid in model.id.lower() for avoid in avoid_patterns):
                continue

            if model.compatibility == "compatible":
                print(f"✅ Selected compatible testing model: {model.id}")
                return model.id

        # Third pass: Any non-embedding model
        for model in models:
            if exclude_embedding and "embed" in model.id.lower():
                continue
            print(f"⚠️ Using fallback model: {model.id}")
            return model.id

        return None
    except Exception as e:
        print(f"Error getting models: {e}")
        return None


class TestRealLMStudioIntegration:
    """REAL integration tests with actual LM Studio server."""

    @pytest.fixture(scope="class")
    def lmstudio_provider(self):
        """Create LM Studio provider if server is running."""
        if not check_server_running("http://localhost:1234/v1/models"):
            pytest.skip("LM Studio server not running on localhost:1234")

        config = {
            "base_url": "http://localhost:1234/v1",
            "timeout": 60,
            "connection_pool_size": 5,
            "enable_streaming": True,
            "enable_caching": True,
        }
        return LMStudioEnhancedProvider(config)

    @pytest.fixture(scope="class")
    def available_model(self, lmstudio_provider):
        """Get an available model for testing."""
        model = get_available_model(lmstudio_provider)
        if not model:
            pytest.skip("No suitable models available in LM Studio")
        return model

    def test_real_connection(self, lmstudio_provider):
        """Test REAL connection to LM Studio server."""
        is_connected = lmstudio_provider.test_connection()
        assert is_connected is True, "LM Studio server should be reachable"

    def test_real_model_listing(self, lmstudio_provider):
        """Test REAL model listing from LM Studio."""
        models = lmstudio_provider.list_models()

        assert isinstance(models, list), "Should return a list of models"
        assert len(models) > 0, "Should have at least one model"

        for model in models:
            assert isinstance(model, ModelInfo), "Each item should be a ModelInfo"
            assert model.id, "Model should have an ID"
            assert model.provider == "lmstudio", "Provider should be 'lmstudio'"
            print(f"✅ Found model: {model.id} ({model.compatibility})")

    def test_real_chat_inference(self, lmstudio_provider, available_model):
        """Test REAL chat inference with actual model."""
        messages = [
            ChatMessage(role="user", content="Say 'Hello from LM Studio!' and nothing else.")
        ]

        print(f"🔥 Testing REAL inference with model: {available_model}")

        response = lmstudio_provider.chat(messages, available_model, max_tokens=50)

        assert isinstance(response, ChatResponse), "Should return ChatResponse"
        assert response.content, "Response should have content"
        assert response.model == available_model, "Response should include correct model"
        assert response.provider == "lmstudio", "Provider should be 'lmstudio'"
        assert response.response_time > 0, "Should have measured response time"

        print(f"✅ REAL RESPONSE: '{response.content.strip()}'")
        print(f"✅ Response time: {response.response_time:.2f}s")
        print(f"✅ Tokens used: {response.tokens_used}")

    @pytest.mark.asyncio
    async def test_real_async_chat(self, lmstudio_provider, available_model):
        """Test REAL async chat with actual model."""
        messages = [
            ChatMessage(role="user", content="Respond with exactly: 'Async test successful!'")
        ]

        print(f"🔥 Testing REAL async inference with model: {available_model}")

        response = await lmstudio_provider.chat_async(messages, available_model, max_tokens=30)

        assert isinstance(response, ChatResponse), "Should return ChatResponse"
        assert response.content, "Response should have content"
        assert "async" in response.content.lower() or "successful" in response.content.lower(), (
            "Should contain expected content"
        )

        print(f"✅ REAL ASYNC RESPONSE: '{response.content.strip()}'")

    @pytest.mark.asyncio
    async def test_real_streaming(self, lmstudio_provider, available_model):
        """Test REAL streaming with actual model."""
        messages = [
            ChatMessage(role="user", content="Count from 1 to 5, each number on a new line.")
        ]

        print(f"🔥 Testing REAL streaming with model: {available_model}")

        chunks = []
        full_content = ""

        async for chunk in lmstudio_provider.chat_streaming(
            messages, available_model, max_tokens=50
        ):
            chunks.append(chunk)
            full_content += chunk.content
            print(f"📦 Chunk: '{chunk.content}'", end="")

            if chunk.is_final:
                print(f"\n✅ Stream completed with {len(chunks)} chunks")
                break

        assert len(chunks) > 0, "Should receive at least one chunk"
        assert full_content, "Should have accumulated content"
        print(f"✅ REAL STREAMED CONTENT: '{full_content.strip()}'")

    def test_real_batch_processing(self, lmstudio_provider, available_model):
        """Test REAL batch processing with actual model."""
        requests = [
            (
                [ChatMessage(role="user", content="Say 'Request 1'")],
                available_model,
                {"max_tokens": 20},
            ),
            (
                [ChatMessage(role="user", content="Say 'Request 2'")],
                available_model,
                {"max_tokens": 20},
            ),
            (
                [ChatMessage(role="user", content="Say 'Request 3'")],
                available_model,
                {"max_tokens": 20},
            ),
        ]

        print(f"🔥 Testing REAL batch processing with {len(requests)} requests")

        responses = lmstudio_provider.batch_chat(requests)

        assert len(responses) == len(requests), "Should get response for each request"

        for i, response in enumerate(responses):
            assert isinstance(response, ChatResponse), f"Response {i} should be ChatResponse"
            assert response.content, f"Response {i} should have content"
            print(f"✅ Batch Response {i + 1}: '{response.content.strip()}'")

    def test_real_model_compatibility_detection(self, lmstudio_provider):
        """Test REAL model compatibility detection."""
        models = lmstudio_provider.list_models()

        compatible_count = 0
        incompatible_count = 0
        unknown_count = 0

        for model in models:
            if model.compatibility == "compatible":
                compatible_count += 1
            elif model.compatibility == "incompatible":
                incompatible_count += 1
            else:
                unknown_count += 1

            print(f"📊 {model.id}: {model.compatibility} - {model.description}")

        print(
            f"✅ Compatibility analysis: {compatible_count} compatible, {incompatible_count} incompatible, {unknown_count} unknown"
        )
        assert compatible_count > 0, "Should find at least one compatible model"

    def test_real_server_info(self, lmstudio_provider):
        """Test REAL server information retrieval."""
        server_info = lmstudio_provider.get_server_info()

        assert isinstance(server_info, dict), "Should return dict"
        assert server_info["status"] == "online", "Server should be online"
        assert server_info["model_count"] > 0, "Should have models"
        assert "localhost:1234" in server_info["server_url"], "Should have correct URL"

        print(f"✅ Server Info: {server_info}")

    def test_real_health_monitoring(self, lmstudio_provider):
        """Test REAL health monitoring."""
        health = lmstudio_provider.get_health_status()

        assert health.is_healthy is True, "Provider should be healthy"
        assert health.response_time > 0, "Should have response time"
        assert health.consecutive_failures == 0, "Should have no failures"

        print(f"✅ Health Status: {health}")

    def test_real_metrics_collection(self, lmstudio_provider, available_model):
        """Test REAL metrics collection during actual usage."""
        # Reset metrics
        lmstudio_provider.reset_metrics()
        initial_metrics = lmstudio_provider.get_metrics()
        assert initial_metrics.total_requests == 0

        # Make a real request
        messages = [ChatMessage(role="user", content="Test metrics")]
        lmstudio_provider.chat(messages, available_model, max_tokens=10)

        # Check metrics were updated
        metrics = lmstudio_provider.get_metrics()
        assert metrics.total_requests > initial_metrics.total_requests
        assert metrics.successful_requests > 0
        assert metrics.average_response_time > 0

        print(f"✅ Metrics after real request: {metrics}")


class TestRealOllamaIntegration:
    """REAL integration tests with actual Ollama server."""

    @pytest.fixture(scope="class")
    def ollama_provider(self):
        """Create Ollama provider if server is running."""
        if not check_server_running("http://localhost:11434/api/tags"):
            pytest.skip("Ollama server not running on localhost:11434")

        config = {
            "base_url": "http://localhost:11434",
            "timeout": 60,
            "connection_pool_size": 5,
            "enable_streaming": True,
            "enable_caching": True,
        }
        return OllamaEnhancedProvider(config)

    @pytest.fixture(scope="class")
    def ollama_model(self, ollama_provider):
        """Get an available Ollama model for testing."""
        model = get_available_model(ollama_provider)
        if not model:
            pytest.skip("No suitable models available in Ollama")
        return model

    def test_real_ollama_connection(self, ollama_provider):
        """Test REAL connection to Ollama server."""
        is_connected = ollama_provider.test_connection()
        assert is_connected is True, "Ollama server should be reachable"

    def test_real_ollama_models(self, ollama_provider):
        """Test REAL model listing from Ollama."""
        models = ollama_provider.list_models()

        assert isinstance(models, list), "Should return a list of models"
        assert len(models) > 0, "Should have at least one model"

        for model in models:
            assert isinstance(model, ModelInfo), "Each item should be a ModelInfo"
            assert model.provider == "ollama", "Provider should be 'ollama'"
            print(f"✅ Found Ollama model: {model.id} ({model.size})")

    def test_real_ollama_chat(self, ollama_provider, ollama_model):
        """Test REAL chat with Ollama."""
        messages = [ChatMessage(role="user", content="Say 'Hello from Ollama!' and nothing else.")]

        print(f"🔥 Testing REAL Ollama inference with model: {ollama_model}")

        response = ollama_provider.chat(messages, ollama_model, max_tokens=50)

        assert isinstance(response, ChatResponse), "Should return ChatResponse"
        assert response.content, "Response should have content"
        assert response.provider == "ollama", "Provider should be 'ollama'"

        print(f"✅ REAL OLLAMA RESPONSE: '{response.content.strip()}'")


class TestRealProviderRegistry:
    """REAL integration tests with the provider registry."""

    def test_real_registry_provider_detection(self):
        """Test REAL provider detection and availability."""
        registry = get_registry()

        # Check which providers are actually available
        health_status = registry.health_check_all()

        available_providers = []
        for provider_name, health in health_status.items():
            if health.is_healthy:
                available_providers.append(provider_name)
                print(f"✅ Provider '{provider_name}' is ONLINE and healthy")
            else:
                print(f"❌ Provider '{provider_name}' is OFFLINE: {health.error_message}")

        assert len(available_providers) > 0, "At least one provider should be available"

    def test_real_optimal_provider_selection(self):
        """Test REAL optimal provider selection with actual servers."""
        registry = get_registry()

        # Test getting optimal provider
        provider = registry.get_optimal_provider(
            ModelRequirements(capabilities=["chat"], compatibility_required=True)
        )

        if provider:
            print(f"✅ Selected optimal provider: {provider.name}")

            # Test that it actually works
            is_healthy = provider.test_connection()
            assert is_healthy, f"Selected provider {provider.name} should be healthy"
        else:
            pytest.skip("No providers available for testing")

    def test_real_model_discovery(self):
        """Test REAL model discovery across all available providers."""
        registry = get_registry()

        all_models = registry.list_all_models(ModelRequirements(compatibility_required=True))

        print(f"🔍 Discovered {len(all_models)} compatible models across all providers:")

        for provider_name, model in all_models:
            print(f"  📋 {provider_name}: {model.id} ({model.performance_tier})")

        assert len(all_models) > 0, "Should discover at least one compatible model"

    def test_real_end_to_end_inference(self):
        """Test REAL end-to-end inference through the registry."""
        registry = get_registry()

        # Get optimal provider
        provider = registry.get_optimal_provider()
        if not provider:
            pytest.skip("No providers available")

        # Get a model
        models = provider.list_models()
        compatible_models = [
            m for m in models if m.compatibility == "compatible" and "embed" not in m.id.lower()
        ]

        if not compatible_models:
            pytest.skip("No compatible models available")

        model = compatible_models[0]

        print(f"🔥 Testing REAL end-to-end: {provider.name} with {model.id}")

        # Make actual inference
        messages = [ChatMessage(role="user", content="Respond with: 'End-to-end test successful!'")]
        response = provider.chat(messages, model.id, max_tokens=30)

        assert isinstance(response, ChatResponse)
        assert response.content

        print(f"✅ REAL END-TO-END SUCCESS: '{response.content.strip()}'")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
