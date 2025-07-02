#!/usr/bin/env python3
"""
Basic Agent Chat Wrapper - Testing Interface

A simple chat interface for testing individual BaseAgent capabilities
without affecting the main crew system.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crew_assistant.agents.base import BaseAgent, AgentConfig, TaskContext
from crew_assistant.providers import get_provider
from crew_assistant.config import get_settings


class BasicTestAgent(BaseAgent):
    """Simple test agent for basic chat interactions."""
    
    def get_system_prompt(self) -> str:
        return f"""You are {self.config.role}, a helpful AI assistant.

Your goal: {self.config.goal}

Background: {self.config.backstory}

Instructions:
- Be helpful, accurate, and concise
- If you need to perform actions, describe what you would do
- Stay focused on the user's request
- If something is unclear, ask for clarification

Respond directly to the user's request."""


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
            verbose=True
        )
        
        agent = BasicTestAgent(
            provider=provider,
            model=settings.openai_api_model,
            config=agent_config
        )
        
        print(f"✅ Agent created: {agent.role}")
        print("\n💬 Chat Interface (type 'quit' to exit)")
        print("-" * 30)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if not user_input:
                    continue
                
                # Create task context
                context = TaskContext(
                    task_description="Respond to user message",
                    expected_output="Helpful response to user query",
                    user_input=user_input
                )
                
                # Execute task
                print(f"\n🤖 {agent.role}: ", end="", flush=True)
                result = agent.execute_task(context)
                
                if result.success:
                    print(result.content)
                    print(f"\n📊 Stats: {result.execution_time:.2f}s, {result.tokens_used} tokens")
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