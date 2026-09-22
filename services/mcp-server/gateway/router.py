"""Multi-LLM Gateway Router for FastMCP."""

import abc
import asyncio
import time
from typing import Optional, Dict, Any, Literal
from enum import Enum

# Provider types
class Provider(Enum):
    GEMINI = "gemini"
    NVIDIA = "nvidia"
    CLOUDFLARE = "cloudflare"
    OLLAMA = "ollama"
    VLLM = "vllm"
    ANOTHER = "another"


# Provider health status
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# Abstract base provider
class BaseProvider(abc.ABC):
    """Base class for LLM providers."""
    
    def __init__(self, name: Provider, model: str, api_key: str | None = None):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.health = HealthStatus.UNKNOWN
        self.latency_history: list[float] = []
        self.error_count = 0
        self.success_count = 0
        self.last_health_check = 0
    
    @abc.abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Complete a prompt generation request."""
        pass
    
    @abc.abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check provider health."""
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available for requests."""
        return self.health in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
    
    @property
    def cost_per_token(self) -> float:
        """Return cost per 1K tokens (override in subclass)."""
        return 0.0


# Concrete provider implementations would go here
# For now, placeholder implementations


class ProviderRouter:
    """Router that manages provider fallback cascade."""
    
    def __init__(self, preferred: list[Provider] = None, fallback: list[Provider] = None):
        self.preferred = preferred or [Provider.GEMINI, Provider.NVIDIA]
        self.fallback = fallback or [Provider.OLLAMA, Provider.VLLM]
        self.providers: dict[Provider, BaseProvider] = {}
        self.provider_order: list[Provider] = self.preferred + self.fallback
        self.default_budget_usd = 10.0  # Monthly budget ceiling
        self.latency_ceiling_ms = 5000  # Max acceptable latency
        self.token_budget_remaining = self.default_budget_usd * 1000  # Rough tokens
    
    def add_provider(self, provider: BaseProvider) -> None:
        """Add a provider to the router."""
        self.providers[provider.name] = provider
    
    def get_provider(self, provider_name: Provider | None = None) -> Optional[BaseProvider]:
        """Get a provider, trying preferred first, then fallback."""
        candidates = [provider_name] if provider_name else self.provider_order
        
        for name in candidates:
            provider = self.providers.get(name)
            if provider and provider.is_available:
                return provider
        
        # Try any provider even if unhealthy (last resort)
        for name in candidates:
            provider = self.providers.get(name)
            if provider:
                return provider
        
        return None
    
    async def route_complete(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Route a completion request through the fallback cascade."""
        last_error: Exception | None = None
        
        # Try preferred providers
        for provider_name in self.preferred:
            provider = self.get_provider(provider_name)
            if not provider:
                continue
            
            try:
                start = time.time()
                result = await provider.complete(prompt, **kwargs)
                latency = (time.time() - start) * 1000
                
                # Update metrics
                provider.success_count += 1
                provider.latency_history.append(latency)
                if len(provider.latency_history) > 100:
                    provider.latency_history = provider.latency_history[-100:]
                provider.health = HealthStatus.HEALTHY
                
                return {
                    "provider": provider.name.value,
                    "model": provider.model,
                    "result": result,
                    "latency_ms": round(latency, 2),
                    "fallback": False,
                }
            except Exception as e:
                last_error = e
                provider.error_count += 1
                if provider.error_count >= 3:
                    provider.health = HealthStatus.UNHEALTHY
                continue
        
        # Try fallback providers
        for provider_name in self.fallback:
            provider = self.get_provider(provider_name)
            if not provider:
                continue
            
            try:
                start = time.time()
                result = await provider.complete(prompt, **kwargs)
                latency = (time.time() - start) * 1000
                
                # Update metrics
                provider.success_count += 1
                provider.latency_history.append(latency)
                if len(provider.latency_history) > 100:
                    provider.latency_history = provider.latency_history[-100:]
                provider.health = HealthStatus.DEGRADED
                
                return {
                    "provider": provider.name.value,
                    "model": provider.model,
                    "result": result,
                    "latency_ms": round(latency, 2),
                    "fallback": True,
                }
            except Exception as e:
                last_error = e
                provider.error_count += 1
                provider.health = HealthStatus.UNHEALTHY
                continue
        
        # All providers failed
        return {
            "error": "All LLM providers unavailable",
            "last_error": str(last_error) if last_error else None,
            "fallback": False,
        }
    
    def health_check_all(self) -> dict[str, dict]:
        """Check health of all providers."""
        results = {}
        for name, provider in self.providers.items():
            results[name] = {
                "status": provider.health.value,
                "success_count": provider.success_count,
                "error_count": provider.error_count,
                "last_health_check": provider.last_health_check,
            }
        return results
    
    def reset_budget(self, usd: float = None) -> None:
        """Reset the monthly budget."""
        self.default_budget_usd = usd or self.default_budget_usd
        self.token_budget_remaining = self.default_budget_usd * 1000


# Global router instance
router = ProviderRouter()


def create_router(preferred: list[str] | None = None, fallback: list[str] | None = None) -> ProviderRouter:
    """Create and configure the LLM provider router."""
    p = [Provider(p) for p in (preferred or ["gemini", "nvidia"])]
    f = [Provider(p) for p in (fallback or ["ollama", "vllm"])]
    return ProviderRouter(preferred=p, fallback=f)