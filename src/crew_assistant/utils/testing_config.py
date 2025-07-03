# Testing Configuration Utilities
# Optimize settings for testing with 8-14GB models

from typing import Any

try:
    from .compute_throttling import print_gpu_status, set_gpu_power_limit
except ImportError:
    # For standalone execution
    from crew_assistant.utils.compute_throttling import print_gpu_status, set_gpu_power_limit


def get_testing_provider_config(provider_type: str = "lmstudio") -> dict[str, Any]:
    """
    Get optimized provider configuration for testing.

    Args:
        provider_type: "lmstudio" or "ollama"

    Returns:
        Optimized config dict for testing
    """

    base_config = {
        "timeout": 30,  # Shorter timeout for testing
        "max_retries": 2,  # Fewer retries for faster failure
        "retry_delay": 0.5,  # Faster retry
        "enable_streaming": True,
        "enable_caching": True,
        "circuit_breaker_threshold": 3,  # Lower threshold for testing
        "connection_pool_size": 3,  # Smaller pool for testing
    }

    if provider_type == "lmstudio":
        return {
            **base_config,
            "base_url": "http://localhost:1234/v1",
            "api_key": "not-needed-for-local",
            "keep_alive_timeout": 15,  # Shorter keep-alive
            "stream_timeout": 60,  # Reasonable stream timeout
        }
    elif provider_type == "ollama":
        return {
            **base_config,
            "base_url": "http://localhost:11434",
            "keep_alive_timeout": 15,
            "stream_timeout": 60,
            "pull_timeout": 300,  # 5 minutes for model pulling
        }
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def get_testing_model_requirements() -> dict[str, Any]:
    """
    Get model requirements optimized for testing.

    Returns:
        ModelRequirements parameters for testing
    """
    return {
        "capabilities": ["chat", "completion"],
        "performance_tier": "fast",  # Prefer fast models for testing
        "compatibility_required": True,
        "streaming_required": False,  # Optional for testing
    }


def get_testing_inference_params() -> dict[str, Any]:
    """
    Get inference parameters optimized for testing.

    Returns:
        Inference parameters for testing
    """
    return {
        "max_tokens": 100,  # Shorter responses for faster testing
        "temperature": 0.3,  # Lower temperature for more predictable results
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }


def setup_testing_environment(gpu_throttle: bool = True, gpu_limit: int = 80) -> dict[str, Any]:
    """
    Set up optimal testing environment.

    Args:
        gpu_throttle: Whether to enable GPU throttling
        gpu_limit: GPU power limit percentage

    Returns:
        Setup status and configuration
    """
    setup_status = {
        "gpu_throttling": False,
        "gpu_info": None,
        "provider_configs": {},
        "model_requirements": get_testing_model_requirements(),
        "inference_params": get_testing_inference_params(),
    }

    # Optional GPU throttling
    if gpu_throttle:
        try:
            throttle_success = set_gpu_power_limit(gpu_limit)
            setup_status["gpu_throttling"] = throttle_success
            if throttle_success:
                print(f"✅ GPU throttling enabled at {gpu_limit}%")
            else:
                print("ℹ️  GPU throttling not available or not needed")
        except Exception as e:
            print(f"⚠️  GPU throttling failed: {e}")

    # Print GPU status for monitoring
    print_gpu_status()

    # Set up provider configurations
    setup_status["provider_configs"] = {
        "lmstudio": get_testing_provider_config("lmstudio"),
        "ollama": get_testing_provider_config("ollama"),
    }

    print("🔧 Testing environment configured:")
    print(f"  📊 Model requirements: {setup_status['model_requirements']}")
    print(f"  ⚙️  Inference params: {setup_status['inference_params']}")
    print(f"  🔌 GPU throttling: {'Enabled' if setup_status['gpu_throttling'] else 'Disabled'}")

    return setup_status


def is_model_suitable_for_testing(model_id: str) -> bool:
    """
    Check if a model is suitable for testing based on size and capabilities.

    Args:
        model_id: Model identifier

    Returns:
        True if model is good for testing
    """
    model_lower = model_id.lower()

    # Preferred sizes for testing (8-14GB range)
    good_sizes = ["7b", "8b", "9b", "10b", "11b", "12b", "13b", "14b"]

    # Avoid large models
    avoid_sizes = ["30b", "32b", "27b", "70b", "65b", "180b"]

    # Avoid embedding models
    if "embed" in model_lower or "embedding" in model_lower:
        return False

    # Check if it's a large model to avoid
    if any(size in model_lower for size in avoid_sizes):
        return False

    # Prefer models with good size indicators
    if any(size in model_lower for size in good_sizes):
        return True

    # Check for tool/function capabilities
    tool_indicators = ["instruct", "chat", "tool", "function", "agent"]
    if any(indicator in model_lower for indicator in tool_indicators):
        return True

    # Default to suitable if no clear indicators
    return True


def print_testing_summary(
    model_used: str, response_time: float, tokens_used: int | None = None
) -> None:
    """
    Print a summary of testing results.

    Args:
        model_used: Model that was used for testing
        response_time: Response time in seconds
        tokens_used: Number of tokens used
    """
    print("\n📊 Testing Summary:")
    print("─" * 50)
    print(f"🤖 Model: {model_used}")
    print(f"⏱️  Response Time: {response_time:.2f}s")
    if tokens_used:
        print(f"🔢 Tokens Used: {tokens_used}")
        print(f"📈 Tokens/Second: {tokens_used / response_time:.1f}")

    # Performance assessment
    if response_time < 1.0:
        print("✅ Excellent performance for testing")
    elif response_time < 3.0:
        print("✅ Good performance for testing")
    elif response_time < 10.0:
        print("⚠️  Acceptable performance for testing")
    else:
        print("❌ Slow performance - consider smaller model")


if __name__ == "__main__":
    """Test the testing configuration utilities."""
    print("🧪 Testing Configuration Utilities")

    # Setup testing environment
    setup_status = setup_testing_environment(gpu_throttle=False)

    print("\n" + "=" * 60)
    print("Testing environment setup complete!")
