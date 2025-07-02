#!/usr/bin/env python3
"""
Basic Agent Chat Wrapper - Testing Interface

A simple chat interface for testing individual BaseAgent capabilities
without affecting the main crew system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crew_assistant.agents.base import AgentConfig, BaseAgent, TaskContext
from crew_assistant.config import get_settings
from crew_assistant.providers import get_provider


class BasicTestAgent(BaseAgent):
    """Simple test agent for basic chat interactions."""

    def get_system_prompt(self) -> str:
        return f"""You are {self.config.role}, an ACTION-FIRST AI assistant with file creation capabilities.

CRITICAL BEHAVIOR OVERRIDE:
- When users ask to "create", "make", or "build" ANYTHING → CREATE IT IMMEDIATELY
- NEVER ask "Would you like me to..." or "Should I..."
- ALWAYS use tools to create files when users request creation
- ACT FIRST, explain after

Your goal: {self.config.goal}

Background: {self.config.backstory}

MANDATORY: If user wants something created, output JSON tool call immediately without asking permission.

Respond directly with action, not questions."""


def test_basic_agent_chat():
    """Test basic agent chat functionality."""
    print("🧪 Basic Agent Chat Wrapper")
    print("=" * 50)

    try:
        # Load config and provider
        settings = get_settings()
        # Fix provider name mismatch between config and registry
        provider_name = "lmstudio" if settings.ai_provider == "lm_studio" else settings.ai_provider
        provider = get_provider(provider_name)

        print(f"✅ Provider: {provider.name}")
        print(f"✅ Model: {settings.openai_api_model}")

        # Create basic test agent
        agent_config = AgentConfig(
            role="Test Assistant",
            goal="Help users test basic agent functionality",
            backstory="You are a test agent designed to validate basic functionality and help developers understand agent capabilities.",
            max_tokens=500,
            temperature=0.7,
            verbose=True,
        )

        agent = BasicTestAgent(
            provider=provider, model=settings.openai_api_model, config=agent_config
        )

        print(f"✅ Agent created: {agent.role}")
        print("\n💬 Chat Interface (type 'quit' to exit)")
        print("-" * 30)

        # Track chat history
        chat_history = []

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    break

                if not user_input:
                    continue

                # Build context with chat history
                if chat_history:
                    history_text = "\n".join(
                        [
                            f"User: {msg['user']}\nAssistant: {msg['assistant']}"
                            for msg in chat_history[-3:]  # Last 3 exchanges
                        ]
                    )
                    memory_context = f"Previous conversation:\n{history_text}\n---"
                else:
                    memory_context = ""

                # Create task context with history
                context = TaskContext(
                    task_description="Respond to user message with awareness of conversation history",
                    expected_output="Helpful response that considers previous context",
                    user_input=user_input,
                    memory_context=memory_context,
                )

                # Execute task
                print(f"\n🤖 {agent.role}: ", end="", flush=True)
                result = agent.execute_task(context)

                if result.success:
                    print(result.content)
                    print(f"\n📊 Stats: {result.execution_time:.2f}s, {result.tokens_used} tokens")

                    # Add to chat history
                    chat_history.append({"user": user_input, "assistant": result.content})

                    # Keep history manageable (last 10 exchanges)
                    if len(chat_history) > 10:
                        chat_history = chat_history[-10:]

                else:
                    print(f"❌ Error: {result.error_message}")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")

        print(f"\n📈 Final Stats: {agent.stats}")

    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        return False

    return True


if __name__ == "__main__":
    success = test_basic_agent_chat()
    sys.exit(0 if success else 1)
