# UX Shell Mode
# Extracted and cleaned from crew_assistant/wrap_crew_run.py and ux_loop.py

import os
import json
import uuid
import datetime
from contextlib import redirect_stdout
import io

from crewai import Crew, Task
from core.context_engine.memory_store import MemoryStore
from utils.fact_learning import learn_fact_if_possible, build_memory_context

# Import UX agent
try:
    from agents.ux import ux
except ImportError as e:
    print(f"❌ Could not import UX agent: {e}")
    print("💡 Make sure agents/ux.py exists and defines 'ux' agent")
    raise

def run_ux_shell(raw_mode=False):
    """
    Interactive UX shell with memory and fact learning.
    
    Args:
        raw_mode (bool): If True, output only response text without formatting
    """
    memory = MemoryStore()
    session_id = str(uuid.uuid4())
    chat_log = []
    snapshot_dir = "crew_runs"
    os.makedirs(snapshot_dir, exist_ok=True)
    
    print("\n🧠 UX Shell online. Type 'exit' to disengage.\n")

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
                agent=ux
            )

            # Run with suppressed CrewAI output
            f = io.StringIO()
            with redirect_stdout(f):
                crew = Crew(agents=[ux], tasks=[ux_task], verbose=False)
                crew.kickoff()

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
            chat_log.append({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "input": user_input,
                "output": reply
            })

        except KeyboardInterrupt:
            print("\n🫡 UX Agent signing off.")
            break
        except Exception as e:
            print(f"❌ Error in UX shell: {e}")
            import traceback
            print(f"📍 Details: {traceback.format_exc()}")

    # Save session log
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    safe_ts = timestamp[:19].replace(":", "-")
    snapshot_file = os.path.join(snapshot_dir, f"{safe_ts}__ux_session__{session_id}.json")
    
    with open(snapshot_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "timestamp": timestamp,
            "model": os.environ.get("OPENAI_API_MODEL", "unknown"),
            "chat_log": chat_log
        }, f, indent=2)
    
    print(f"💾 Session log saved: {snapshot_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run UX Shell")
    parser.add_argument("--raw", action="store_true", help="Raw output mode")
    args = parser.parse_args()
    
    run_ux_shell(raw_mode=args.raw)