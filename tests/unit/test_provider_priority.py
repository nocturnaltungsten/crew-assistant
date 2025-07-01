# Unit Tests for Provider Priority System
# Comprehensive testing for Task 6.2.4: Priority provider selection

import pytest
import time
from unittest.mock import Mock, patch

from providers.registry import (
    ProviderRegistry, 
    PriorityLevel, 
    ModelRequirements, 
    ProviderConfig,
    ProviderStatus,
    get_optimal_provider
)
from providers.base import BaseProvider, ModelInfo


class MockProvider(BaseProvider):
    """Mock provider for testing."""
    
    def __init__(self, config):
        super().__init__(config)
        self._is_available = True
        self.enable_streaming = True
        
    def list_models(self):
        return [
            ModelInfo(
                id="test-model",
                name="Test Model", 
                provider="mock",
                compatibility="compatible",
                description="Test model",
                capabilities=["chat"],
                performance_tier="standard"
            )
        ]
    
    def test_connection(self) -> bool:
        """Test if provider is available and responding."""
        return self._is_available
    
    def chat(self, messages, model: str, **kwargs):
        """Mock chat implementation."""
        from providers.base import ChatResponse
        return ChatResponse(
            content="test response",
            model=model,
            provider="mock",
            tokens_used=10,
            response_time=0.1
        )
    
    @property 
    def display_name(self) -> str:
        """Human-readable provider name."""
        return "Mock Provider"


class TestPriorityLevel:
    """Test PriorityLevel enum functionality."""
    
    def test_priority_level_values(self):
        """Test that priority levels have correct values."""
        assert PriorityLevel.UX_INTERACTIVE.value == 1
        assert PriorityLevel.STANDARD.value == 5  
        assert PriorityLevel.BACKGROUND.value == 10
        
    def test_priority_level_ordering(self):
        """Test that priority levels are correctly ordered."""
        assert PriorityLevel.UX_INTERACTIVE.value < PriorityLevel.STANDARD.value
        assert PriorityLevel.STANDARD.value < PriorityLevel.BACKGROUND.value


class TestProviderRegistryPriority:
    """Test ProviderRegistry priority functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.registry = ProviderRegistry()
        
        # Register test providers with different priorities
        self.registry.register_provider(
            "high_priority",
            MockProvider,
            {"test": True},
            priority=10,
            enabled=True
        )
        
        self.registry.register_provider(
            "medium_priority", 
            MockProvider,
            {"test": True},
            priority=5,
            enabled=True
        )
        
        self.registry.register_provider(
            "low_priority",
            MockProvider, 
            {"test": True},
            priority=1,
            enabled=True
        )
        
        # Set all providers as online
        for name in ["high_priority", "medium_priority", "low_priority"]:
            self.registry._provider_configs[name].status = ProviderStatus.ONLINE
    
    def test_backward_compatibility_no_priority(self):
        """
        Test that existing calls without priority parameter work identically.
        CRITICAL: This ensures 100% backward compatibility.
        """
        # Call without priority parameter (existing usage)
        provider = self.registry.get_optimal_provider()
        
        # Should get highest priority provider (existing behavior)
        assert provider is not None
        # Verify it followed original selection logic
        assert self.registry._request_counts["high_priority"] == 1
        
    def test_backward_compatibility_with_requirements_only(self):
        """Test existing usage with ModelRequirements only."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # Call with requirements only (existing usage)
        provider = self.registry.get_optimal_provider(requirements)
        
        assert provider is not None
        # Should use standard provider selection logic
        assert self.registry._request_counts["high_priority"] == 1
        
    def test_ux_priority_selection(self):
        """Test UX priority selects optimal provider for interactive use."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # Call with UX priority
        provider = self.registry.get_optimal_provider(
            requirements, 
            PriorityLevel.UX_INTERACTIVE
        )
        
        assert provider is not None
        # Should use UX priority logic (speed over load balancing)
        assert self.registry._request_counts["high_priority"] == 1
        
    def test_standard_priority_same_as_no_priority(self):
        """Test that STANDARD priority behaves identically to no priority."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # Reset request counts
        self.registry.reset_metrics()
        
        # Get provider without priority
        provider1 = self.registry.get_optimal_provider(requirements)
        provider1_name = None
        for name, config in self.registry._provider_configs.items():
            if self.registry._request_counts[name] == 1:
                provider1_name = name
                break
        
        # Reset and get provider with STANDARD priority
        self.registry.reset_metrics()
        provider2 = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.STANDARD
        )
        provider2_name = None
        for name, config in self.registry._provider_configs.items():
            if self.registry._request_counts[name] == 1:
                provider2_name = name
                break
        
        # Should be identical behavior
        assert provider1_name == provider2_name
        
    def test_ux_priority_bypasses_load_balancing(self):
        """Test that UX priority bypasses load balancing for speed."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # Simulate high usage on high-priority provider
        self.registry._request_counts["high_priority"] = 100
        self.registry._request_counts["medium_priority"] = 1
        
        # Standard selection would load balance to medium_priority
        standard_provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.STANDARD
        )
        
        # Reset request count for fair comparison
        high_before = self.registry._request_counts["high_priority"]
        medium_before = self.registry._request_counts["medium_priority"]
        
        # UX priority should still select high_priority (bypass load balancing)
        ux_provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.UX_INTERACTIVE  
        )
        
        # UX should have selected high_priority despite load balancing
        assert self.registry._request_counts["high_priority"] == high_before + 1
        
    def test_priority_with_offline_providers(self):
        """Test priority selection handles offline providers correctly."""
        # Set high priority provider offline
        self.registry._provider_configs["high_priority"].status = ProviderStatus.OFFLINE
        
        requirements = ModelRequirements(capabilities=["chat"])
        
        # UX priority should skip offline provider
        provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.UX_INTERACTIVE
        )
        
        assert provider is not None
        # Should have selected next best online provider
        assert self.registry._request_counts["medium_priority"] == 1
        assert self.registry._request_counts["high_priority"] == 0
        
    def test_ux_priority_logging(self):
        """Test that UX priority logs appropriate debug messages."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        with patch('providers.registry.logger') as mock_logger:
            provider = self.registry.get_optimal_provider(
                requirements,
                PriorityLevel.UX_INTERACTIVE
            )
            
            # Should log UX-specific message
            mock_logger.debug.assert_called_once()
            logged_message = mock_logger.debug.call_args[0][0]
            assert "UX priority provider" in logged_message
            assert "interactive request" in logged_message


class TestConvenienceFunction:
    """Test convenience function with priority parameter."""
    
    def test_convenience_function_backward_compatible(self):
        """Test that convenience function preserves backward compatibility."""
        with patch('providers.registry.get_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_get_registry.return_value = mock_registry
            
            # Call without priority (existing usage)
            get_optimal_provider()
            
            # Should call registry method with None priority
            mock_registry.get_optimal_provider.assert_called_once_with(None, None)
            
    def test_convenience_function_with_priority(self):
        """Test convenience function with priority parameter."""
        with patch('providers.registry.get_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_get_registry.return_value = mock_registry
            
            requirements = ModelRequirements(capabilities=["chat"])
            
            # Call with priority
            get_optimal_provider(requirements, PriorityLevel.UX_INTERACTIVE)
            
            # Should pass through correctly
            mock_registry.get_optimal_provider.assert_called_once_with(
                requirements, 
                PriorityLevel.UX_INTERACTIVE
            )


class TestPerformanceOptimization:
    """Test performance optimizations for UX priority."""
    
    def setup_method(self):
        """Set up performance test environment."""
        self.registry = ProviderRegistry()
        
        # Register providers with different simulated latencies
        self.registry.register_provider("fast_provider", MockProvider, {"test": True}, priority=8)
        self.registry.register_provider("slow_provider", MockProvider, {"test": True}, priority=10)
        
        for name in ["fast_provider", "slow_provider"]:
            self.registry._provider_configs[name].status = ProviderStatus.ONLINE
    
    def test_ux_priority_selection_efficiency(self):
        """Test that UX priority selection is optimized for speed."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        start_time = time.time()
        
        # UX priority should be fast
        provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.UX_INTERACTIVE
        )
        
        selection_time = time.time() - start_time
        
        assert provider is not None
        # Should be very fast (under 1ms for this simple case)
        assert selection_time < 0.001
        
    def test_load_balancing_skip_verification(self):
        """Verify that UX priority actually skips load balancing calculations."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # Create high request count imbalance
        self.registry._request_counts["slow_provider"] = 1000
        self.registry._request_counts["fast_provider"] = 1
        
        # Standard priority would load balance to fast_provider
        standard_provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.STANDARD
        )
        
        assert self.registry._request_counts["fast_provider"] == 2  # Got selected due to load balancing
        
        # Reset for UX test
        self.registry._request_counts["fast_provider"] = 1
        
        # UX priority should select slow_provider (highest priority, ignore load balancing)
        ux_provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.UX_INTERACTIVE
        )
        
        assert self.registry._request_counts["slow_provider"] == 1001  # UX selected high priority despite load imbalance


class TestErrorHandling:
    """Test error handling for priority system."""
    
    def test_no_eligible_providers_ux_priority(self):
        """Test UX priority handling when no providers are eligible."""
        registry = ProviderRegistry()
        
        # No providers registered
        requirements = ModelRequirements(capabilities=["chat"])
        
        provider = registry.get_optimal_provider(
            requirements,
            PriorityLevel.UX_INTERACTIVE
        )
        
        assert provider is None
        
    def test_all_providers_offline_ux_priority(self):
        """Test UX priority when all providers are offline."""
        registry = ProviderRegistry()
        registry.register_provider("test_provider", MockProvider, {"test": True})
        
        # Set provider offline
        registry._provider_configs["test_provider"].status = ProviderStatus.OFFLINE
        
        requirements = ModelRequirements(capabilities=["chat"])
        
        provider = registry.get_optimal_provider(
            requirements,
            PriorityLevel.UX_INTERACTIVE
        )
        
        assert provider is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])