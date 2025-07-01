# UX Shell Mode
# Extracted and cleaned from crew_assistant/wrap_crew_run.py and ux_loop.py

import datetime
import json
import os
import uuid

from crewai import Crew, Task

from core.context_engine.memory_store import MemoryStore
from utils.fact_learning import build_memory_context, learn_fact_if_possible


# Import UX agent creation function
def get_ux_agent():
    """Get UX agent with current configuration."""
    try:
        from crewai import Agent

        from agents.ux import get_llm

        return Agent(
            role="Chat interface",
            goal="Act as user's super-powerful AI machine",
            backstory=(
                "You're a witty, helpful employee of the user. You talk shit, and make sure that every resource at your disposal is utilized to achieve user's (ie your) goals and objectives. "
                "You act as user's electronic butler — assisting how you can, and using your brain (all the other agents and tools in the system) to do work autonomously"
            ),
            allow_delegation=False,
            use_system_prompt=False,
            llm=get_llm(),
            verbose=True,
        )
    except ImportError as e:
        print(f"❌ Could not import UX agent: {e}")
        print("💡 Make sure agents/ux.py exists and defines 'get_llm' function")
        raise


def run_ux_shell(raw_mode=False):
    """
    Interactive UX shell with memory and fact learning.

    Args:
        raw_mode (bool): If True, output only response text without formatting
    """
    # Check if provider is configured, if not, prompt for setup
    if not os.getenv("AI_PROVIDER") or not os.getenv("OPENAI_API_MODEL"):
        print("🔧 No AI provider configured. Let's set one up!")
        from utils.provider_selector import interactive_setup

        result = interactive_setup()
        if result:
            model_id, provider, api_base = result
            os.environ["OPENAI_API_MODEL"] = model_id
            os.environ["OPENAI_API_BASE"] = api_base
            os.environ["AI_PROVIDER"] = provider.value
            print("✅ Provider configured!")
        else:
            print("❌ Setup cancelled. Using defaults.")
            return

    provider = os.getenv("AI_PROVIDER", "lm_studio")
    model = os.getenv("OPENAI_API_MODEL", "unknown")

    # Use direct Ollama integration for Ollama provider
    if provider == "ollama":
        print("🔄 Using direct Ollama integration (bypassing CrewAI)...")
        from utils.simple_ollama_chat import run_simple_ollama_ux

        run_simple_ollama_ux()
        return

    # Continue with CrewAI for LM Studio
    memory = MemoryStore()
    session_id = str(uuid.uuid4())
    chat_log = []
    snapshot_dir = "crew_runs"
    os.makedirs(snapshot_dir, exist_ok=True)

    print(f"\n🧠 UX Shell online using {provider} with {model}")
    print("Type 'exit' to disengage.\n")

    # Create UX agent with current configuration
    ux = get_ux_agent()

    while True:
        try:
            user_input = input("👤 > ").strip()
            if user_input.lower() in ("exit", "quit", "q"):
                print("🫡 UX Agent signing off.")
                break

            # Build context
            memory_context = build_memory_context()

            # Create task with context
            task_description = f"""
The user said: '{user_input}'.

Recent memory context:
{memory_context}

Respond as a helpful assistant. Speak clearly and helpfully.
"""

            ux_task = Task(
                description=task_description,
                expected_output="A helpful response in plain English.",
                agent=ux,
            )

            # Run with debugging
            print("🔍 Creating crew...")
            crew = Crew(agents=[ux], tasks=[ux_task], verbose=True)

            print("🔍 Starting inference...")
            try:
                result = crew.kickoff()
                print(f"🔍 Got result: {result}")
            except Exception as e:
                print(f"❌ Error during inference: {e}")
                import traceback

                traceback.print_exc()
                continue

            # Extract response
            raw_output = getattr(ux_task.output, "content", str(ux_task.output))

            try:
                # Try to parse as JSON first
                parsed = json.loads(raw_output)
                if isinstance(parsed, dict):
                    reply = parsed.get("reply", str(parsed))
                else:
                    reply = str(parsed)
            except (json.JSONDecodeError, AttributeError):
                # If not JSON, use raw output
                reply = raw_output or "No response generated"

            # Display response
            if raw_mode:
                print(reply)
            else:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                border = "─" * 80
                print(f"\n System │ {timestamp}\n{border}\n{reply}\n{border}")

            # Save to memory
            try:
                memory.save(
                    agent="UX",
                    input_summary=user_input,
                    output_summary=reply,
                    task_id=str(ux_task.id),
                )
            except Exception:
                pass

            # Learn facts
            learn_fact_if_possible(user_input)
            learn_fact_if_possible(reply)

            # Log session
            chat_log.append(
                {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "input": user_input,
                    "output": reply,
                }
            )

        except KeyboardInterrupt:
            print("\n🫡 UX Agent signing off.")
            break
        except Exception as e:
            print(f"❌ Error in UX shell: {e}")
            import traceback

            print(f"📍 Details: {traceback.format_exc()}")

    # Save session log
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    safe_ts = timestamp[:19].replace(":", "-")
    snapshot_file = os.path.join(snapshot_dir, f"{safe_ts}__ux_session__{session_id}.json")

    with open(snapshot_file, "w") as f:
        json.dump(
            {
                "session_id": session_id,
                "timestamp": timestamp,
                "model": os.environ.get("OPENAI_API_MODEL", "unknown"),
                "chat_log": chat_log,
            },
            f,
            indent=2,
        )

    print(f"💾 Session log saved: {snapshot_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run UX Shell")
    parser.add_argument("--raw", action="store_true", help="Raw output mode")
    args = parser.parse_args()

    run_ux_shell(raw_mode=args.raw)
