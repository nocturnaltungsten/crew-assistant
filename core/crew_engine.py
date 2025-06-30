# Crew Engine
# Main orchestrator for the enhanced crew system

import datetime
import json
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from agents import create_crew
from providers import get_provider, list_all_models
from workflows import SequentialWorkflow, WorkflowResult
from workflows.base import ValidationResult

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
        self.crew = create_crew(
            provider=self.provider,
            model=config.model,
            verbose=config.verbose
        )

        # Initialize workflow
        self.workflow = SequentialWorkflow(
            agents=self.crew,
            max_iterations=config.max_iterations
        )

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

        # Pre-workflow validation: Review task specification quality
        validation_result = self._validate_task_specification(user_request)
        if not validation_result.approved:
            if self.config.verbose:
                print(f"📋 Task specification needs refinement:")
                print(f"   {validation_result.feedback}")
            
            # Return early with validation feedback
            from workflows.base import WorkflowResult, WorkflowStatus
            return WorkflowResult(
                status=WorkflowStatus.NEEDS_CLARIFICATION,
                success=False,
                final_output=validation_result.feedback,
                error_message="Task specification needs clarification",
                steps=[],
                iterations_count=0,
                total_execution_time=0.0
            )

        if self.config.verbose:
            print("✅ Task specification approved - proceeding with crew workflow")

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
        self.session_history.append({
            "request": user_request,
            "result": result,
            "timestamp": datetime.datetime.now()
        })

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
                "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:11434").replace("/v1", ""),
                "timeout": 180  # 3 minutes for complex development tasks
            }
        elif self.config.provider == "lmstudio":
            return {
                "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1"),
                "api_key": os.getenv("OPENAI_API_KEY", "not-needed-for-local"),
                "timeout": 180  # 3 minutes for complex development tasks
            }
        else:
            return {}

    def _validate_task_specification(self, user_request: str):
        """Validate task specification quality using Reviewer agent."""
        from agents.base import TaskContext
        
        try:
            # Create validation task for Reviewer agent
            reviewer = self.crew.get("Reviewer")
            if not reviewer:
                # If no reviewer available, approve by default
                return ValidationResult(
                    approved=True,
                    feedback="No reviewer available - proceeding with task"
                )
            
            validation_context = TaskContext(
                task_description=f"""TASK SPECIFICATION REVIEW
                
Evaluate this user request for clarity, completeness, and actionability:

USER REQUEST: "{user_request}"

Review criteria:
1. CLARITY: Is the request clear and unambiguous?
2. SCOPE: Is the scope well-defined and reasonable?
3. ACTIONABILITY: Can this be effectively implemented by a development team?
4. COMPLETENESS: Are there missing critical details?

Special Override Guidelines:
- If user indicates they want to proceed with limited information (phrases like "JUST BUILD IT", "do the best you can", "work with what I've given you", "proceed anyway", etc.), then APPROVE the task
- For simple, well-understood tasks (basic algorithms, simple utilities, common programming tasks), be more lenient and APPROVE if the core request is clear
- Tasks like "create a sorting algorithm", "build a calculator", "write a password generator" are standard programming tasks that should generally be approved
- In such cases, note that the UX Agent and Planner Agent are responsible for extrapolating the limited requirements into a clear execution plan
- The development team is expected to make reasonable assumptions and fill gaps based on best practices

Respond with:
- **DECISION: APPROVE** if the task is ready for crew execution OR if user explicitly wants to proceed
- **DECISION: NEEDS_CLARIFICATION** if the task needs refinement AND user hasn't indicated to proceed anyway

If NEEDS_CLARIFICATION, provide specific guidance on what needs to be clarified or refined.""",
                expected_output="Task specification validation with APPROVE or NEEDS_CLARIFICATION decision and specific feedback",
                user_input=user_request
            )
            
            # Execute validation
            validation_result = reviewer.execute_task(validation_context)
            
            if validation_result.success:
                response_content = validation_result.content
                
                # Check reviewer decision
                if "**DECISION: APPROVE**" in response_content:
                    return ValidationResult(
                        approved=True,
                        feedback="Task specification approved by reviewer"
                    )
                elif "**DECISION: NEEDS_CLARIFICATION**" in response_content:
                    return ValidationResult(
                        approved=False,
                        feedback=response_content
                    )
                else:
                    # Default to needing clarification if unclear
                    return ValidationResult(
                        approved=False,
                        feedback=f"Reviewer feedback: {response_content}"
                    )
            else:
                # If validation failed, approve by default to avoid blocking
                return ValidationResult(
                    approved=True,
                    feedback="Validation failed - proceeding with task"
                )
                
        except Exception as e:
            if self.config.verbose:
                print(f"⚠️ Validation error: {e}")
            # If validation fails, approve by default
            return ValidationResult(
                approved=True,
                feedback="Validation error - proceeding with task"
            )

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
                    "steps": [
                        {
                            "agent_role": step.agent_role,
                            "task_description": step.task_description,
                            "iteration": step.iteration,
                            "success": step.result.success if step.result else False,
                            "content": step.result.content if step.result else "",
                            "execution_time": step.result.execution_time if step.result else 0
                        }
                        for step in result.steps
                    ]
                }
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
            "success_rate": sum(1 for h in self.session_history if h["result"].success) / len(self.session_history) if self.session_history else 0,
            "workflow_stats": self.workflow.stats,
            "crew_stats": {role: agent.stats for role, agent in self.crew.items()}
        }

    def get_available_providers(self) -> list:
        """Get list of available providers."""
        return list_available_providers()

    def switch_model(self, new_model: str):
        """Switch to a different model (recreates crew)."""
        self.config.model = new_model

        # Recreate crew with new model
        self.crew = create_crew(
            provider=self.provider,
            model=new_model,
            verbose=self.config.verbose
        )

        # Recreate workflow
        self.workflow = SequentialWorkflow(
            agents=self.crew,
            max_iterations=self.config.max_iterations
        )

        if self.config.verbose:
            print(f"🔄 Switched to model: {new_model}")


def create_crew_engine(provider: str, model: str, **kwargs) -> CrewEngine:
    """Convenience function to create crew engine."""
    config = CrewConfig(provider=provider, model=model, **kwargs)
    return CrewEngine(config)
