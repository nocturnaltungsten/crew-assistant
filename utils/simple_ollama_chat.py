# Simple Ollama Chat - Direct API Integration
# Bypasses CrewAI for direct Ollama communication

import json
import os

import requests


class SimpleOllamaChat:
    """Direct Ollama chat interface."""

    def __init__(self, model="mistral:latest", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, message: str, system_prompt: str = None) -> str:
        """Send a chat message to Ollama and get response."""

        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add user message
        messages.append({
            "role": "user",
            "content": message
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result.get("message", {}).get("content", "No response")

        except Exception as e:
            return f"Error: {e}"

def run_simple_ollama_ux():
    """Simple UX shell using direct Ollama integration."""
    import datetime
    import uuid

    from core.context_engine.memory_store import MemoryStore
    from utils.fact_learning import build_memory_context, learn_fact_if_possible

    memory = MemoryStore()
    session_id = str(uuid.uuid4())
    chat_log = []

    # Get configuration
    model = os.getenv("OPENAI_API_MODEL", "mistral:latest")
    base_url = os.getenv("OPENAI_API_BASE", "http://localhost:11434").replace("/v1", "")

    chat = SimpleOllamaChat(model=model, base_url=base_url)

    print(f"\n🧠 Simple Ollama UX online using {model}")
    print("Type 'exit' to disengage.\n")

    # Agent personality with delegation capability
    system_prompt = """You're a witty, helpful employee of the user. You talk shit, and make sure that every resource at your disposal is utilized to achieve user's (ie your) goals and objectives. You act as user's electronic butler — assisting how you can, and using your brain (all the other agents and tools in the system) to do work autonomously.

When the user asks for complex tasks that require planning, development, or evaluation, respond with: "🚀 DELEGATE_TO_CREW: [task description]" to hand off to the specialized agent team.

Examples of tasks to delegate:
- Building applications or scripts
- Project planning and implementation  
- Code review and evaluation
- Multi-step technical workflows

For simple questions and conversations, respond normally as a helpful assistant."""

    while True:
        try:
            user_input = input("👤 > ").strip()
            if user_input.lower() in ("exit", "quit", "q"):
                print("🫡 UX Agent signing off.")
                break

            # Build context from memory
            try:
                memory_context = build_memory_context()
                if not isinstance(memory_context, str):
                    memory_context = "No recent context available"
            except Exception:
                memory_context = "No recent context available"

            # Create full prompt with context
            full_message = f"""User said: '{user_input}'

Recent memory context:
{memory_context}

Respond helpfully to the user's request."""

            print("🤖 ", end="", flush=True)
            response = chat.chat(full_message, system_prompt)

            # Check if delegation is requested
            if "🚀 DELEGATE_TO_CREW:" in response:
                task_description = response.split("🚀 DELEGATE_TO_CREW:")[1].strip()
                print(f"🔄 Delegating to crew: {task_description}")

                # Switch to crew mode for this task
                try:
                    crew_result = run_ollama_crew_task(task_description, model, base_url)
                    print("\n✅ Crew completed task!")
                    print(f"📋 Result: {crew_result}")
                    response = f"I delegated your task to the specialized crew team. Here's what they accomplished:\n\n{crew_result}"
                except Exception as e:
                    print(f"❌ Crew delegation failed: {e}")
                    response = "I tried to delegate this to the crew, but encountered an issue. Let me try a simpler approach..."
                    response = chat.chat(f"Provide a simpler response to: {user_input}", system_prompt.replace("🚀 DELEGATE_TO_CREW:", ""))

            print(response)

            # Store in memory
            try:
                memory.store("UX", user_input, response)
            except Exception:
                # Skip memory storage if it fails
                pass

            # Learn facts
            try:
                learn_fact_if_possible(user_input)
                learn_fact_if_possible(response)
            except Exception:
                # Skip fact learning if it fails
                pass

            # Update chat log
            chat_log.append({
                "timestamp": str(datetime.datetime.now()),
                "user": user_input,
                "assistant": response
            })

        except KeyboardInterrupt:
            print("\n🫡 UX Agent signing off.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    # Save session
    snapshot_dir = "crew_runs"
    os.makedirs(snapshot_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    session_file = f"{snapshot_dir}/{timestamp}__ux_session__{session_id}.json"

    session_data = {
        "session_id": session_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model,
        "chat_log": chat_log
    }

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)

    print(f"📝 Session log saved: {session_file}")

def run_ollama_crew_task(task_description: str, model: str, base_url: str) -> str:
    """Run a task using the crew system with Ollama models."""
    from crewai import LLM, Agent, Crew, Task

    # Create Ollama-compatible LLM
    llm = LLM(
        model=model,
        api_base=f"{base_url}/v1"  # Use OpenAI-compatible endpoint
    )

    # Create specialized agents with Ollama LLM
    planner = Agent(
        role='Planner',
        goal='Break down high-level goals into manageable sub-tasks.',
        backstory='A strategic thinker who turns visions into roadmaps.',
        allow_delegation=False,
        use_system_prompt=False,
        llm=llm,
        verbose=False
    )

    dev = Agent(
        role='Dev',
        goal='Implement and test individual Python subtasks.',
        backstory='A passionate engineer who loves shipping working code.',
        allow_delegation=False,
        use_system_prompt=False,
        llm=llm,
        verbose=False
    )

    commander = Agent(
        role='Commander',
        goal='Oversee the agent system and ensure proper planning and execution.',
        backstory='A seasoned systems architect, you ensure the agents work in harmony.',
        allow_delegation=True,
        use_system_prompt=False,
        llm=llm,
        verbose=False
    )

    # Create tasks
    planner_task = Task(
        description=f"Plan this task: {task_description}",
        expected_output="A clear plan with 3-5 actionable steps",
        agent=planner
    )

    dev_task = Task(
        description="Implement the planned solution with working code and documentation",
        expected_output="Complete implementation with code, documentation, and usage instructions",
        agent=dev
    )

    commander_task = Task(
        description="Review the implementation and provide evaluation and next steps",
        expected_output="Technical review with recommendations and suggested next actions",
        agent=commander
    )

    # Execute crew workflow
    crew = Crew(
        agents=[planner, dev, commander],
        tasks=[planner_task, dev_task, commander_task],
        verbose=False
    )

    result = crew.kickoff()
    return str(result)

if __name__ == "__main__":
    run_simple_ollama_ux()
