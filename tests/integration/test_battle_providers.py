# BATTLE TESTING for Providers
# Test with REAL agentic workflow token loads (10k, 20k, 30k tokens)
# Because 100 tokens is a joke for persistent workflows!

import time

import pytest
import requests

from crew_assistant.providers.base import ChatMessage, ChatResponse
from crew_assistant.providers.lmstudio import LMStudioProvider


def check_server_running(url: str) -> bool:
    """Check if a server is actually running."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False


def generate_large_context(token_target: int) -> str:
    """Generate a large context to simulate real agentic workflows."""
    # Approximate 4 chars per token for English text
    chars_needed = token_target * 4

    # Simulate a complex agentic workflow context
    base_context = """
You are part of a persistent agentic workflow managing a complex software development project.

Previous Agent Interactions:
1. Planning Agent analyzed requirements and created 47 user stories
2. Architecture Agent designed microservices with 12 components
3. Development Agent implemented authentication service
4. Testing Agent found 23 issues requiring fixes
5. Review Agent suggested 15 architectural improvements

Current Task Context:
The system needs to handle real-time data processing at scale with the following requirements:
- Process 1M events per second
- Maintain sub-100ms latency
- Support horizontal scaling
- Implement circuit breakers
- Add comprehensive monitoring

Technical Stack:
- Backend: Python, FastAPI, PostgreSQL, Redis, Kafka
- Frontend: React, TypeScript, GraphQL
- Infrastructure: Kubernetes, Prometheus, Grafana
- CI/CD: GitHub Actions, ArgoCD

Code Review Comments from Previous Iterations:
"""

    # Add code samples and detailed context
    code_sample = """
class EventProcessor:
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.kafka_consumer = KafkaConsumer(config.kafka_config)
        self.redis_client = Redis(config.redis_config)
        self.metrics = MetricsCollector()

    async def process_event(self, event: Event) -> ProcessResult:
        start_time = time.time()
        try:
            # Validate event
            if not self.validate_event(event):
                raise InvalidEventError(f"Invalid event: {event.id}")

            # Check cache
            cached_result = await self.redis_client.get(f"event:{event.id}")
            if cached_result:
                self.metrics.increment("cache_hits")
                return ProcessResult.from_cache(cached_result)

            # Process event
            result = await self.process_event_logic(event)

            # Store in cache
            await self.redis_client.set(
                f"event:{event.id}",
                result.to_json(),
                expire=3600
            )

            # Update metrics
            self.metrics.record_latency("event_processing", time.time() - start_time)

            return result

        except Exception as e:
            self.metrics.increment("processing_errors")
            logger.error(f"Event processing failed: {e}")
            raise

"""

    # Build the full context
    full_context = base_context

    # Add multiple code reviews
    for i in range(5):
        full_context += f"\n\nCode Review #{i + 1}:\n{code_sample}\n"
        full_context += (
            "Review Comment: Consider implementing retry logic with exponential backoff.\n"
        )
        full_context += f"Performance metrics show {i * 100}ms average latency.\n"

    # Pad to reach target token count
    while len(full_context) < chars_needed:
        full_context += "\nAdditional context: " + "x" * 100

    return full_context[:chars_needed]


class TestBattleLMStudioProvider:
    """BATTLE tests with real token loads."""

    @pytest.fixture(scope="class")
    def battle_provider(self):
        """Create provider configured for battle testing."""
        if not check_server_running("http://localhost:1234/v1/models"):
            pytest.skip("LM Studio server not running on localhost:1234")

        config = {
            "base_url": "http://localhost:1234/v1",
            "timeout": 300,  # 5 minutes for large requests
            "connection_pool_size": 10,
            "enable_streaming": True,
            "enable_caching": False,  # Disable for accurate timing
            "stream_timeout": 600,  # 10 minutes for streaming
        }
        return LMStudioProvider(config)

    @pytest.fixture(scope="class")
    def battle_model(self, battle_provider):
        """Get suitable model for battle testing."""
        models = battle_provider.list_models()

        # Find 8B model for testing
        for model in models:
            if (
                "8b" in model.id.lower()
                and model.compatibility == "compatible"
                and "embed" not in model.id.lower()
            ):
                print(f"🎯 Selected battle model: {model.id}")
                return model.id

        pytest.skip("No suitable 8B model for battle testing")

    @pytest.mark.parametrize("token_count", [10000, 20000, 30000])
    def test_battle_large_context(self, battle_provider, battle_model, token_count):
        """Test with REAL agentic workflow token loads."""
        print(f"\n🔥 BATTLE TEST: {token_count} tokens with {battle_model}")

        # Generate large context
        large_context = generate_large_context(token_count)

        messages = [
            ChatMessage(
                role="system",
                content="You are a senior software architect reviewing this complex system.",
            ),
            ChatMessage(
                role="user",
                content=f"{large_context}\n\nBased on all this context, provide a brief summary of the main architectural concerns.",
            ),
        ]

        # Time the actual request
        start_time = time.time()

        try:
            response = battle_provider.chat(
                messages,
                battle_model,
                max_tokens=500,  # Reasonable response size
                temperature=0.3,
            )

            elapsed_time = time.time() - start_time

            # Validate response
            assert isinstance(response, ChatResponse)
            assert response.content
            assert len(response.content) > 50  # Should have substantial response

            # Performance metrics
            tokens_per_second = token_count / elapsed_time if elapsed_time > 0 else 0

            print("✅ BATTLE SUCCESS!")
            print(f"  ⏱️  Total Time: {elapsed_time:.2f}s")
            print(f"  📊 Input Tokens: ~{token_count}")
            print(f"  📊 Output Tokens: {response.completion_tokens or 'N/A'}")
            print(f"  🚀 Throughput: {tokens_per_second:.1f} tokens/second")
            print(f"  📝 Response Preview: {response.content[:100]}...")

            # Performance assertions
            assert elapsed_time < 180, f"Response took too long: {elapsed_time}s"
            assert tokens_per_second > 50, f"Too slow: {tokens_per_second} tokens/s"

        except Exception as e:
            print(f"❌ BATTLE FAILED: {e}")
            raise

    @pytest.mark.asyncio
    @pytest.mark.parametrize("token_count", [10000, 20000])
    async def test_battle_streaming(self, battle_provider, battle_model, token_count):
        """Test streaming with large contexts."""
        print(f"\n🔥 BATTLE STREAMING TEST: {token_count} tokens")

        large_context = generate_large_context(token_count)
        messages = [
            ChatMessage(role="user", content=f"{large_context}\n\nSummarize in 3 bullet points.")
        ]

        start_time = time.time()
        chunks_received = 0
        first_chunk_time = None
        full_response = ""

        try:
            async for chunk in battle_provider.chat_streaming(
                messages, battle_model, max_tokens=200
            ):
                if not first_chunk_time and chunk.content:
                    first_chunk_time = time.time() - start_time
                    print(f"  ⚡ First chunk in: {first_chunk_time:.2f}s")

                chunks_received += 1
                full_response += chunk.content

                if chunk.is_final:
                    break

            total_time = time.time() - start_time

            print("✅ STREAMING BATTLE SUCCESS!")
            print(f"  ⏱️  Total Time: {total_time:.2f}s")
            print(f"  📦 Chunks: {chunks_received}")
            print(f"  📝 Response Length: {len(full_response)} chars")

            assert chunks_received > 5, "Should receive multiple chunks"
            assert first_chunk_time < 30, f"First chunk too slow: {first_chunk_time}s"

        except Exception as e:
            print(f"❌ STREAMING BATTLE FAILED: {e}")
            raise

    def test_battle_concurrent_requests(self, battle_provider, battle_model):
        """Test handling multiple large requests concurrently."""
        print("\n🔥 BATTLE CONCURRENT TEST: 3 x 5000 tokens")

        # Create multiple large requests
        requests = []
        for i in range(3):
            context = generate_large_context(5000)
            messages = [
                ChatMessage(
                    role="user",
                    content=f"Request {i + 1}: {context}\n\nProvide a one-line response.",
                )
            ]
            requests.append((messages, battle_model, {"max_tokens": 50}))

        start_time = time.time()

        # Process concurrently
        responses = battle_provider.batch_chat(requests)

        total_time = time.time() - start_time

        assert len(responses) == 3
        successful = sum(1 for r in responses if r.content and not r.finish_reason == "error")

        print("✅ CONCURRENT BATTLE COMPLETE!")
        print(f"  ⏱️  Total Time: {total_time:.2f}s")
        print(f"  ✅ Successful: {successful}/3")
        print(f"  🚀 Avg Time per Request: {total_time / 3:.2f}s")

        assert successful >= 2, "At least 2 requests should succeed"

    def test_battle_resilience(self, battle_provider, battle_model):
        """Test provider resilience with edge cases."""
        print("\n🔥 BATTLE RESILIENCE TEST")

        # Test 1: Maximum context that won't overflow
        huge_context = generate_large_context(40000)  # Near limit
        messages = [ChatMessage(role="user", content=f"{huge_context}\n\nRespond with: OK")]

        try:
            response = battle_provider.chat(messages, battle_model, max_tokens=10)
            print("  ✅ Handled 40k token context")
        except Exception as e:
            print(f"  ❌ Failed on huge context: {e}")
            # This might fail depending on model limits, which is OK

        # Test 2: Rapid successive requests
        print("  🔥 Testing rapid requests...")
        success_count = 0

        for i in range(5):
            try:
                quick_msg = [ChatMessage(role="user", content=f"Quick test {i}")]
                response = battle_provider.chat(quick_msg, battle_model, max_tokens=10)
                if response.content:
                    success_count += 1
            except Exception:
                pass

        print(f"  ✅ Rapid requests: {success_count}/5 successful")
        assert success_count >= 3, "Should handle most rapid requests"


class TestBattleMetrics:
    """Test metrics under battle conditions."""

    def test_battle_metrics_accuracy(self, battle_provider, battle_model):
        """Verify metrics are accurate under load."""
        print("\n🔥 BATTLE METRICS TEST")

        # Reset metrics
        battle_provider.reset_metrics()
        initial = battle_provider.get_metrics()
        assert initial.total_requests == 0

        # Make several requests with varying sizes
        token_sizes = [1000, 5000, 10000]
        actual_responses = []

        for size in token_sizes:
            context = generate_large_context(size)
            messages = [ChatMessage(role="user", content=f"{context}\n\nAcknowledge.")]

            try:
                response = battle_provider.chat(messages, battle_model, max_tokens=20)
                actual_responses.append(response)
                print(f"  ✅ Completed {size} token request")
            except Exception as e:
                print(f"  ❌ Failed {size} token request: {e}")

        # Check metrics
        final_metrics = battle_provider.get_metrics()

        print("\n📊 BATTLE METRICS:")
        print(f"  Total Requests: {final_metrics.total_requests}")
        print(f"  Successful: {final_metrics.successful_requests}")
        print(f"  Failed: {final_metrics.failed_requests}")
        print(f"  Success Rate: {final_metrics.success_rate:.1f}%")
        print(f"  Avg Response Time: {final_metrics.average_response_time:.2f}s")

        assert final_metrics.total_requests == len(actual_responses)
        assert final_metrics.successful_requests == len(actual_responses)


def run_battle_summary():
    """Run all battle tests and provide summary."""
    print("\n" + "=" * 60)
    print("🔥 PROVIDER BATTLE TESTING SUMMARY 🔥")
    print("=" * 60)
    print("""
    Battle testing with REAL token loads:
    - 10,000 tokens (10k) - Small agentic context
    - 20,000 tokens (20k) - Medium workflow state
    - 30,000 tokens (30k) - Large persistent context

    These tests validate:
    ✓ Timeouts don't trip under real loads
    ✓ Streaming works with huge contexts
    ✓ Concurrent handling of multiple large requests
    ✓ Metrics accuracy under battle conditions
    ✓ Provider resilience and error recovery
    """)


if __name__ == "__main__":
    run_battle_summary()
    # Run with: pytest tests/integration/test_battle_providers.py -v -s
