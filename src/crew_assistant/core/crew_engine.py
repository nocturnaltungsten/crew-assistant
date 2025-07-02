# Crew Engine
# Main orchestrator for the enhanced crew system

import datetime
import json
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from crew_assistant.providers.registry import get_registry

from ..agents import create_crew
from ..providers import get_provider
from ..workflows import SequentialWorkflow, WorkflowResult
from .context_engine.memory_store import MemoryStore


@dataclass
class CrewConfig:
    """Configuration for crew engine."""

    provider: str
    model: str
    max_iterations: int = 3
    verbose: bool = True
    save_sessions: bool = True
    memory_enabled: bool = True


class CrewEngine:
    """Main orchestrator for the enhanced crew system."""

    def __init__(self, config: CrewConfig):
        """Initialize crew engine with configuration."""
        self.config = config
        self.session_id = str(uuid.uuid4())

        # Initialize provider
        self.provider = get_provider(config.provider)

        # Initialize crew
        self.crew = create_crew(provider=self.provider, model=config.model, verbose=config.verbose)

        # Initialize workflow
        self.workflow = SequentialWorkflow(agents=self.crew, max_iterations=config.max_iterations)

        # Initialize memory (if enabled)
        self.memory = MemoryStore() if config.memory_enabled else None

        # Session tracking
        self.session_history = []

        if config.verbose:
            print("🚀 Crew Engine initialized")
            print(f"   Provider: {config.provider}")
            print(f"   Model: {config.model}")
            print(f"   Agents: {list(self.crew.keys())}")

    def execute_task(self, user_request: str, context: str = "") -> WorkflowResult:
        """Execute a task using the crew workflow."""
        if self.config.verbose:
            print(f"\n🎯 Executing task: {user_request}")

        # Add memory context if available
        if self.memory and context:
            try:
                memory_context = self._build_memory_context()
                if memory_context:
                    context = f"{context}\n\nMemory Context:\n{memory_context}"
            except Exception as e:
                if self.config.verbose:
                    print(f"⚠️ Memory context failed: {e}")

        # No pre-validation - let the crew handle any request
        if self.config.verbose:
            print("🚀 Deploying crew to handle your request...")

        # Execute workflow
        result = self.workflow.execute(user_request)

        # Store in memory
        if self.memory and result.success:
            try:
                self.memory.save("CrewEngine", user_request, result.final_output)
            except Exception as e:
                if self.config.verbose:
                    print(f"⚠️ Memory storage failed: {e}")

        # Save session
        if self.config.save_sessions:
            self._save_session(user_request, result)

        # Track in history
        self.session_history.append(
            {"request": user_request, "result": result, "timestamp": datetime.datetime.now()}
        )

        if self.config.verbose:
            status_emoji = "✅" if result.success else "❌"
            print(f"{status_emoji} Task completed in {result.total_execution_time:.2f}s")
            print(f"   Iterations: {result.iterations_count}")
            print(f"   Status: {result.status.value}")

        return result

    def _get_provider_config(self) -> dict[str, Any]:
        """Get provider configuration from environment."""
        if self.config.provider == "ollama":
            return {
                "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:11434").replace(
                    "/v1", ""
                ),
                "timeout": 180,  # 3 minutes for complex development tasks
            }
        elif self.config.provider == "lmstudio":
            return {
                "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1"),
                "api_key": os.getenv("OPENAI_API_KEY", "not-needed-for-local"),
                "timeout": 180,  # 3 minutes for complex development tasks
            }
        else:
            return {}

    def _build_memory_context(self, limit: int = 5) -> str:
        """Build context from recent memory entries."""
        try:
            # Use existing memory context building from fact_learning
            from utils.fact_learning import build_memory_context

            return build_memory_context(limit=limit)
        except Exception:
            return ""

    def _save_session(self, user_request: str, result: WorkflowResult):
        """Save session data to file."""
        try:
            # Create session directory
            session_dir = "crew_runs"
            os.makedirs(session_dir, exist_ok=True)

            # Create session data
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            session_data = {
                "session_id": self.session_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "config": asdict(self.config),
                "request": user_request,
                "result": {
                    "status": result.status.value,
                    "success": result.success,
                    "final_output": result.final_output,
                    "execution_time": result.total_execution_time,
                    "iterations": result.iterations_count,
                    "error_message": result.error_message,
                    "review_ratings": {
                        "completeness": result.review_ratings.completeness
                        if result.review_ratings
                        else 0,
                        "quality": result.review_ratings.quality if result.review_ratings else 0,
                        "clarity": result.review_ratings.clarity if result.review_ratings else 0,
                        "feasibility": result.review_ratings.feasibility
                        if result.review_ratings
                        else 0,
                        "alignment": result.review_ratings.alignment
                        if result.review_ratings
                        else 0,
                        "average_rating": result.review_ratings.average_rating
                        if result.review_ratings
                        else 0.0,
                    },
                    "steps": [
                        {
                            "agent_role": step.agent_role,
                            "task_description": step.task_description,
                            "iteration": step.iteration,
                            "success": step.result.success if step.result else False,
                            "content": step.result.content if step.result else "",
                            "execution_time": step.result.execution_time if step.result else 0,
                        }
                        for step in result.steps
                    ],
                },
            }

            # Save to file
            filename = f"{timestamp}__crew_session__{self.session_id}.json"
            filepath = os.path.join(session_dir, filename)

            with open(filepath, "w") as f:
                json.dump(session_data, f, indent=2)

            if self.config.verbose:
                print(f"📝 Session saved: {filepath}")

        except Exception as e:
            if self.config.verbose:
                print(f"⚠️ Session save failed: {e}")

    @property
    def stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        return {
            "session_id": self.session_id,
            "tasks_executed": len(self.session_history),
            "success_rate": sum(1 for h in self.session_history if h["result"].success)
            / len(self.session_history)
            if self.session_history
            else 0,
            "workflow_stats": self.workflow.stats,
            "crew_stats": {role: agent.stats for role, agent in self.crew.items()},
        }

    def get_available_providers(self) -> list:
        """Get list of available providers."""
        return get_registry().list_providers()

    def switch_model(self, new_model: str):
        """Switch to a different model (recreates crew)."""
        self.config.model = new_model

        # Recreate crew with new model
        self.crew = create_crew(
            provider=self.provider, model=new_model, verbose=self.config.verbose
        )

        # Recreate workflow
        self.workflow = SequentialWorkflow(
            agents=self.crew, max_iterations=self.config.max_iterations
        )

        if self.config.verbose:
            print(f"🔄 Switched to model: {new_model}")


def create_crew_engine(provider: str, model: str, **kwargs) -> CrewEngine:
    """Convenience function to create crew engine."""
    config = CrewConfig(provider=provider, model=model, **kwargs)
    return CrewEngine(config)
