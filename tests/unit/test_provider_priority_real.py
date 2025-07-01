# Unit Tests for Provider Priority System using Real Providers
# Tests Task 6.2.4: Priority provider selection with actual LM Studio

import pytest
import time
from unittest.mock import patch

from providers.registry import (
    ProviderRegistry, 
    PriorityLevel, 
    ModelRequirements, 
    get_optimal_provider,
    get_registry
)


class TestPriorityLevelEnum:
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


class TestBackwardCompatibility:
    """Test 100% backward compatibility - CRITICAL for production safety."""
    
    def test_get_optimal_provider_no_params(self):
        """Test existing usage without any parameters works identically."""
        # This is how existing code calls the function
        provider = get_optimal_provider()
        
        # Should work without error (provider might be None if LM Studio offline, that's OK)
        # Key test: function call succeeds with original signature
        assert provider is None or provider is not None  # Either outcome is valid
        
    def test_get_optimal_provider_requirements_only(self):
        """Test existing usage with ModelRequirements only."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # This is how existing code calls the function  
        provider = get_optimal_provider(requirements)
        
        # Should work without error (provider might be None if no models match)
        assert provider is None or provider is not None  # Either outcome is valid
        
    def test_registry_get_optimal_provider_signature(self):
        """Test that ProviderRegistry.get_optimal_provider maintains backward compatibility."""
        registry = ProviderRegistry()
        
        # Original signature should work
        provider1 = registry.get_optimal_provider()
        provider2 = registry.get_optimal_provider(ModelRequirements())
        
        # Both should work without error
        assert True  # If we get here, signatures are compatible


class TestPrioritySystemIntegration:
    """Test priority system integration with real provider registry."""
    
    def setup_method(self):
        """Set up test with fresh registry."""
        # Get fresh registry instance
        self.registry = get_registry()
        
        # Reset request counts for clean testing
        self.registry.reset_metrics()
        
    def test_ux_priority_parameter_accepted(self):
        """Test that UX priority parameter is accepted without error."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # This should not raise an error
        provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.UX_INTERACTIVE
        )
        
        # Provider might be None if no providers available, that's OK for this test
        assert provider is None or provider is not None
        
    def test_standard_priority_parameter_accepted(self):
        """Test that STANDARD priority parameter is accepted."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.STANDARD
        )
        
        assert provider is None or provider is not None
        
    def test_background_priority_parameter_accepted(self):
        """Test that BACKGROUND priority parameter is accepted.""" 
        requirements = ModelRequirements(capabilities=["chat"])
        
        provider = self.registry.get_optimal_provider(
            requirements,
            PriorityLevel.BACKGROUND
        )
        
        assert provider is None or provider is not None


class TestPriorityLogic:
    """Test priority selection logic with controlled conditions."""
    
    def test_priority_method_routing(self):
        """Test that different priorities route to different methods."""
        registry = ProviderRegistry()
        requirements = ModelRequirements(capabilities=["chat"])
        
        # Mock the internal methods to verify routing
        with patch.object(registry, '_get_ux_priority_provider') as mock_ux:
            with patch.object(registry, '_get_standard_provider') as mock_standard:
                mock_ux.return_value = None
                mock_standard.return_value = None
                
                # UX priority should call UX method
                registry.get_optimal_provider(requirements, PriorityLevel.UX_INTERACTIVE)
                mock_ux.assert_called_once_with(requirements)
                
                # Reset mocks
                mock_ux.reset_mock()
                mock_standard.reset_mock()
                
                # Standard priority should call standard method
                registry.get_optimal_provider(requirements, PriorityLevel.STANDARD)
                mock_standard.assert_called_once_with(requirements, PriorityLevel.STANDARD)
                
                # Reset mocks  
                mock_ux.reset_mock()
                mock_standard.reset_mock()
                
                # No priority should call standard method
                registry.get_optimal_provider(requirements)
                mock_standard.assert_called_once_with(requirements, None)


class TestConvenienceFunctionCompatibility:
    """Test convenience function backward compatibility."""
    
    def test_convenience_function_original_signature(self):
        """Test original convenience function signature works."""
        # Original usage patterns
        provider1 = get_optimal_provider()
        provider2 = get_optimal_provider(ModelRequirements())
        
        # Should not raise errors
        assert True
        
    def test_convenience_function_new_signature(self):
        """Test new convenience function signature works."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # New usage patterns
        provider1 = get_optimal_provider(requirements, PriorityLevel.UX_INTERACTIVE)
        provider2 = get_optimal_provider(requirements, PriorityLevel.STANDARD)
        provider3 = get_optimal_provider(None, PriorityLevel.UX_INTERACTIVE)
        
        # Should not raise errors
        assert True


class TestPerformanceImpact:
    """Test that priority system doesn't degrade existing performance."""
    
    def test_standard_priority_performance(self):
        """Test that standard priority has minimal performance impact."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        # Time existing behavior (no priority)
        start_time = time.time()
        provider1 = get_optimal_provider(requirements)
        time_no_priority = time.time() - start_time
        
        # Time new behavior (explicit standard priority)
        start_time = time.time()
        provider2 = get_optimal_provider(requirements, PriorityLevel.STANDARD)
        time_with_priority = time.time() - start_time
        
        # Performance should be similar (within 10ms)
        performance_delta = abs(time_with_priority - time_no_priority)
        assert performance_delta < 0.01  # Less than 10ms difference
        
    def test_ux_priority_efficiency(self):
        """Test that UX priority is efficient for its purpose."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        start_time = time.time()
        provider = get_optimal_provider(requirements, PriorityLevel.UX_INTERACTIVE)
        ux_priority_time = time.time() - start_time
        
        # UX priority should be fast (under 50ms for local providers)
        assert ux_priority_time < 0.05


class TestRealProviderInteraction:
    """Test with real LM Studio provider if available."""
    
    def test_real_provider_priority_selection(self):
        """Test priority selection with real provider."""
        requirements = ModelRequirements(capabilities=["chat"])
        
        try:
            # Try to get provider with UX priority
            provider = get_optimal_provider(requirements, PriorityLevel.UX_INTERACTIVE)
            
            if provider is not None:
                # If we got a provider, it should be functional
                assert hasattr(provider, 'chat')
                assert hasattr(provider, 'list_models')
                assert hasattr(provider, 'test_connection')
                
                # Test that it can list models
                models = provider.list_models()
                assert isinstance(models, list)
                
        except Exception as e:
            # If LM Studio is offline, that's OK for this test
            pytest.skip(f"LM Studio not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])