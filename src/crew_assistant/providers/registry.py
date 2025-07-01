# Enhanced Provider Registry
# Production-grade provider management with health monitoring and load balancing

import asyncio
import time
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger

from .base import BaseProvider, ModelInfo, ProviderHealth, ProviderMetrics
from .lmstudio import LMStudioProvider
from .ollama import OllamaProvider


class ProviderStatus(Enum):
    """Provider status enumeration."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


@dataclass
class ProviderConfig:
    """Configuration for a provider instance."""

    name: str
    provider_class: Type[BaseProvider]
    config: Dict[str, Any]
    priority: int = 1  # Higher number = higher priority
    enabled: bool = True
    auto_failover: bool = True
    health_check_interval: int = 30  # seconds
    last_health_check: float = field(default_factory=time.time)
    status: ProviderStatus = ProviderStatus.OFFLINE


@dataclass
class ModelRequirements:
    """Requirements for model selection."""

    capabilities: List[str] = field(default_factory=list)  # ["chat", "completion", "code"]
    performance_tier: Optional[str] = None  # "fast", "balanced", "capable"
    agent_role: Optional[str] = None  # "ux", "planner", "developer", "reviewer", "commander"
    max_tokens: Optional[int] = None
    streaming_required: bool = False
    compatibility_required: bool = True


class ProviderRegistry:
    """Enhanced provider registry with health monitoring and intelligent routing."""

    def __init__(self):
        self._provider_configs: Dict[str, ProviderConfig] = {}
        self._provider_instances: Dict[str, BaseProvider] = {}
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._health_check_running = False

        # Load balancing and routing
        self._request_counts: Dict[str, int] = {}
        self._last_used: Dict[str, float] = {}

        # Model tier mapping for agent-role optimization
        self._agent_role_tiers = {
            "ux": "fast",  # UX agents benefit from quick responses
            "planner": "balanced",  # Planners need balance of speed and capability
            "developer": "capable",  # Developers need capable models for complex code
            "reviewer": "capable",  # Reviewers need capable models for analysis
            "commander": "balanced",  # Commanders coordinate, need balanced performance
        }

        logger.info("Enhanced Provider Registry initialized")

    def register_provider(
        self,
        name: str,
        provider_class: Type[BaseProvider],
        config: Dict[str, Any],
        priority: int = 1,
        enabled: bool = True,
    ) -> None:
        """Register a provider with configuration."""
        provider_config = ProviderConfig(
            name=name,
            provider_class=provider_class,
            config=config,
            priority=priority,
            enabled=enabled,
        )

        self._provider_configs[name] = provider_config
        self._request_counts[name] = 0
        self._last_used[name] = 0.0

        logger.info(f"Registered provider '{name}' with priority {priority}")

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get or create provider instance."""
        if name not in self._provider_configs:
            logger.error(f"Unknown provider: {name}")
            return None

        config = self._provider_configs[name]
        if not config.enabled:
            logger.warning(f"Provider '{name}' is disabled")
            return None

        # Create instance if it doesn't exist
        if name not in self._provider_instances:
            try:
                instance = config.provider_class(config.config)
                self._provider_instances[name] = instance
                logger.info(f"Created instance for provider '{name}'")
            except Exception as e:
                logger.error(f"Failed to create provider '{name}': {e}")
                return None

        return self._provider_instances[name]

    def get_optimal_provider(
        self, requirements: Optional[ModelRequirements] = None
    ) -> Optional[BaseProvider]:
        """Get the optimal provider based on requirements and health."""
        if not requirements:
            requirements = ModelRequirements()

        # Apply agent-role-specific performance tier mapping
        requirements = self._apply_agent_role_mapping(requirements)

        # Get eligible providers
        eligible = self._get_eligible_providers(requirements)

        if not eligible:
            logger.warning("No eligible providers found")
            return None

        # Sort by priority and health
        eligible.sort(
            key=lambda x: (
                -self._provider_configs[x].priority,  # Higher priority first
                self._provider_configs[x].status != ProviderStatus.ONLINE,  # Online first
                self._request_counts[x],  # Least used first (load balancing)
            )
        )

        provider_name = eligible[0]
        provider = self.get_provider(provider_name)

        if provider:
            self._request_counts[provider_name] += 1
            self._last_used[provider_name] = time.time()
            logger.debug(
                f"Selected provider '{provider_name}' for request (role: {requirements.agent_role}, tier: {requirements.performance_tier})"
            )

        return provider

    def get_provider_with_model(
        self, model_id: str, requirements: Optional[ModelRequirements] = None
    ) -> Optional[tuple[BaseProvider, ModelInfo]]:
        """Get provider that has the specified model."""
        if not requirements:
            requirements = ModelRequirements()

        for provider_name in self._get_eligible_providers(requirements):
            provider = self.get_provider(provider_name)
            if not provider:
                continue

            try:
                models = provider.list_models()
                for model in models:
                    if model.id == model_id:
                        # Check if model meets requirements
                        if self._model_meets_requirements(model, requirements):
                            logger.debug(f"Found model '{model_id}' on provider '{provider_name}'")
                            return provider, model
            except Exception as e:
                logger.error(f"Error checking models on provider '{provider_name}': {e}")

        logger.warning(f"Model '{model_id}' not found on any eligible provider")
        return None

    def list_all_models(
        self, requirements: Optional[ModelRequirements] = None
    ) -> List[tuple[str, ModelInfo]]:
        """List all models from all providers."""
        if not requirements:
            requirements = ModelRequirements()

        all_models = []

        for provider_name in self._get_eligible_providers(requirements):
            provider = self.get_provider(provider_name)
            if not provider:
                continue

            try:
                models = provider.list_models()
                for model in models:
                    if self._model_meets_requirements(model, requirements):
                        all_models.append((provider_name, model))
            except Exception as e:
                logger.error(f"Error listing models from provider '{provider_name}': {e}")

        return all_models

    def health_check_all(self) -> Dict[str, ProviderHealth]:
        """Perform health check on all providers."""
        health_status = {}

        for provider_name, config in self._provider_configs.items():
            if not config.enabled:
                continue

            provider = self.get_provider(provider_name)
            if provider:
                try:
                    health = provider.get_health_status()
                    health_status[provider_name] = health

                    # Update provider status based on health
                    if health.is_healthy:
                        config.status = ProviderStatus.ONLINE
                    elif health.consecutive_failures < 3:
                        config.status = ProviderStatus.DEGRADED
                    else:
                        config.status = ProviderStatus.OFFLINE

                    config.last_health_check = time.time()

                except Exception as e:
                    logger.error(f"Health check failed for provider '{provider_name}': {e}")
                    config.status = ProviderStatus.OFFLINE
                    health_status[provider_name] = ProviderHealth(
                        is_healthy=False,
                        response_time=0.0,
                        last_check=time.time(),
                        error_message=str(e),
                        consecutive_failures=getattr(config, "consecutive_failures", 0) + 1,
                    )

        return health_status

    def get_provider_by_name(self, provider_name: str) -> Optional[BaseProvider]:
        """Get a specific provider by name."""
        return self.get_provider(provider_name)

    def get_provider_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all providers."""
        metrics = {}

        for provider_name, config in self._provider_configs.items():
            provider = self.get_provider(provider_name)
            if provider:
                try:
                    provider_metrics = provider.get_metrics()
                    metrics[provider_name] = {
                        "provider_metrics": provider_metrics,
                        "registry_metrics": {
                            "status": config.status.value,
                            "priority": config.priority,
                            "enabled": config.enabled,
                            "request_count": self._request_counts.get(provider_name, 0),
                            "last_used": self._last_used.get(provider_name, 0.0),
                            "last_health_check": config.last_health_check,
                        },
                    }
                except Exception as e:
                    logger.error(f"Error getting metrics for provider '{provider_name}': {e}")

        return metrics

    def start_health_monitoring(self, interval: int = 30) -> None:
        """Start background health monitoring."""
        if self._health_check_running:
            logger.warning("Health monitoring already running")
            return

        async def health_monitor():
            self._health_check_running = True
            logger.info(f"Started health monitoring with {interval}s interval")

            while self._health_check_running:
                try:
                    health_status = self.health_check_all()
                    healthy_count = sum(1 for h in health_status.values() if h.is_healthy)
                    logger.debug(
                        f"Health check completed: {healthy_count}/{len(health_status)} providers healthy"
                    )
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")

                await asyncio.sleep(interval)

        self._health_monitor_task = asyncio.create_task(health_monitor())

    def stop_health_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._health_monitor_task:
            self._health_check_running = False
            self._health_monitor_task.cancel()
            logger.info("Stopped health monitoring")

    def enable_provider(self, name: str) -> bool:
        """Enable a provider."""
        if name in self._provider_configs:
            self._provider_configs[name].enabled = True
            logger.info(f"Enabled provider '{name}'")
            return True
        return False

    def disable_provider(self, name: str) -> bool:
        """Disable a provider."""
        if name in self._provider_configs:
            self._provider_configs[name].enabled = False
            logger.info(f"Disabled provider '{name}'")
            return True
        return False

    def set_provider_priority(self, name: str, priority: int) -> bool:
        """Set provider priority."""
        if name in self._provider_configs:
            old_priority = self._provider_configs[name].priority
            self._provider_configs[name].priority = priority
            logger.info(f"Changed provider '{name}' priority from {old_priority} to {priority}")
            return True
        return False

    def list_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._provider_configs.keys())

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all providers."""
        status = {}

        for name, config in self._provider_configs.items():
            provider = self.get_provider(name)

            status[name] = {
                "name": name,
                "status": config.status.value,
                "priority": config.priority,
                "enabled": config.enabled,
                "auto_failover": config.auto_failover,
                "last_health_check": config.last_health_check,
                "request_count": self._request_counts.get(name, 0),
                "last_used": self._last_used.get(name, 0.0),
                "available": provider.is_available if provider else False,
            }

        return status

    def reset_metrics(self) -> None:
        """Reset all provider metrics."""
        for name in self._provider_configs:
            self._request_counts[name] = 0
            self._last_used[name] = 0.0

            provider = self.get_provider(name)
            if provider:
                provider.reset_metrics()

        logger.info("Reset all provider metrics")

    def cleanup(self) -> None:
        """Cleanup all providers and stop monitoring."""
        self.stop_health_monitoring()

        for provider in self._provider_instances.values():
            try:
                provider.close()
            except Exception as e:
                logger.error(f"Error closing provider: {e}")

        self._provider_instances.clear()
        logger.info("Cleaned up all providers")

    def _get_eligible_providers(self, requirements: ModelRequirements) -> List[str]:
        """Get list of providers that meet requirements."""
        eligible = []

        for name, config in self._provider_configs.items():
            if not config.enabled:
                continue

            # Skip offline providers unless no alternatives
            if config.status == ProviderStatus.OFFLINE:
                continue

            # Check if provider supports streaming if required
            if requirements.streaming_required:
                provider = self.get_provider(name)
                if provider and not provider.enable_streaming:
                    continue

            eligible.append(name)

        return eligible

    def _apply_agent_role_mapping(self, requirements: ModelRequirements) -> ModelRequirements:
        """Apply agent-role-specific performance tier mapping."""
        # Create a copy to avoid modifying the original
        mapped_requirements = ModelRequirements(
            capabilities=requirements.capabilities.copy(),
            performance_tier=requirements.performance_tier,
            agent_role=requirements.agent_role,
            max_tokens=requirements.max_tokens,
            streaming_required=requirements.streaming_required,
            compatibility_required=requirements.compatibility_required,
        )

        # Apply role-to-tier mapping if agent_role is specified and performance_tier is not
        if mapped_requirements.agent_role and not mapped_requirements.performance_tier:
            mapped_tier = self._agent_role_tiers.get(mapped_requirements.agent_role)
            if mapped_tier:
                mapped_requirements.performance_tier = mapped_tier
                logger.debug(
                    f"Mapped agent role '{mapped_requirements.agent_role}' to performance tier '{mapped_tier}'"
                )

        return mapped_requirements

    def _model_meets_requirements(self, model: ModelInfo, requirements: ModelRequirements) -> bool:
        """Check if a model meets the given requirements."""
        # Check compatibility
        if requirements.compatibility_required and model.compatibility != "compatible":
            return False

        # Check capabilities
        if requirements.capabilities:
            if not all(cap in model.capabilities for cap in requirements.capabilities):
                return False

        # Check performance tier
        if requirements.performance_tier:
            if model.performance_tier != requirements.performance_tier:
                return False

        # Check context length
        if requirements.max_tokens and model.context_length:
            if model.context_length < requirements.max_tokens:
                return False

        return True

    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup()


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get global provider registry singleton."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()

        # Register built-in providers with intelligent defaults
        _registry.register_provider(
            "lmstudio",
            LMStudioProvider,
            {
                "base_url": "http://localhost:1234/v1",
                "timeout": 60,
                "connection_pool_size": 10,
                "enable_streaming": True,
                "enable_caching": True,
            },
            priority=2,  # Higher priority than Ollama by default
            enabled=True,
        )

        _registry.register_provider(
            "ollama",
            OllamaProvider,
            {
                "base_url": "http://localhost:11434",
                "timeout": 60,
                "connection_pool_size": 8,
                "enable_streaming": True,
                "enable_caching": True,
            },
            priority=1,
            enabled=True,
        )

        logger.info("Initialized global provider registry with built-in providers")

    return _registry


def get_provider(name: str) -> Optional[BaseProvider]:
    """Convenience function to get provider instance."""
    return get_registry().get_provider(name)


def get_optimal_provider(
    requirements: Optional[ModelRequirements] = None,
) -> Optional[BaseProvider]:
    """Convenience function to get optimal provider."""
    return get_registry().get_optimal_provider(requirements)


def list_all_models(
    requirements: Optional[ModelRequirements] = None,
) -> List[tuple[str, ModelInfo]]:
    """Convenience function to list all models."""
    return get_registry().list_all_models(requirements)


def health_check_all() -> Dict[str, ProviderHealth]:
    """Convenience function for health check."""
    return get_registry().health_check_all()
