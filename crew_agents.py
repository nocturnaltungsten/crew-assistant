# === crew_agents.py ===

from crewai import Crew, Task
from agents import commander, planner, dev
from core.context_engine.memory_store import MemoryStore
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
import uuid
import json
import argparse

# Import utilities
from utils.model_selector import select_model
from utils.ux_shell import run_ux_shell

def run_crew():
    """Run interactive crew workflow with conversation loop."""
    # === Load environment variables ===
    load_dotenv()
    
    # === Initialize Context Store ===
    memory = MemoryStore()
    session_id = str(uuid.uuid4())
    chat_log = []
    deliverables_dir = "deliverables"
    os.makedirs(deliverables_dir, exist_ok=True)
    
    # === Set default model if not specified ===
    if not os.getenv("OPENAI_API_MODEL"):
        os.environ["OPENAI_API_MODEL"] = "microsoft/phi-4-mini-reasoning"
    
    print("\n🚀 CrewAI Interactive Workflow")
    print("💡 UX agent handles chat, delegates complex tasks to Planner → Dev → Commander")
    print("💡 Type 'exit' to end session\n")
    
    while True:
        try:
            user_input = input("👤 > ").strip()
            if user_input.lower() in ("exit", "quit", "q"):
                print("🫡 Crew workflow session ended.")
                break
                
            if not user_input:
                continue
            
            # UX agent determines if this needs task delegation
            response, needs_delegation = handle_user_input_with_ux(user_input, memory)
            
            # Display UX response
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n🤖 UX Agent │ {timestamp}")
            print("─" * 60)
            print(response)
            print("─" * 60 + "\n")
            
            # If complex task, delegate to crew
            deliverable = None
            if needs_delegation:
                print("🔄 Delegating to Planner for task breakdown...")
                deliverable = execute_crew_delegation(user_input, memory, deliverables_dir)
                if deliverable:
                    print(f"📁 Deliverable saved: {deliverable}")
            
            # Log conversation
            chat_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "input": user_input,
                "ux_response": response,
                "delegation": needs_delegation,
                "deliverable": deliverable
            })
            
        except KeyboardInterrupt:
            print("\n🫡 Crew workflow session ended.")
            break
        except Exception as e:
            print(f"❌ Error in crew workflow: {e}")
            import traceback
            print(f"📍 Details: {traceback.format_exc()}")
    
    # Save session log
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_ts = timestamp[:19].replace(":", "-")
    session_file = f"deliverables/{safe_ts}__crew_session__{session_id}.json"
    
    with open(session_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "timestamp": timestamp,
            "model": os.environ.get("OPENAI_API_MODEL", "unknown"),
            "chat_log": chat_log
        }, f, indent=2)
    
    print(f"💾 Session log saved: {session_file}")

def handle_user_input_with_ux(user_input: str, memory: MemoryStore) -> tuple[str, bool]:
    """
    UX agent processes user input and determines if task delegation is needed.
    Returns (response, needs_delegation)
    """
    from agents.ux import ux
    from utils.fact_learning import build_memory_context
    import io
    from contextlib import redirect_stdout
    
    # Build context from memory
    memory_context = build_memory_context()
    
    # Create task for UX agent to analyze user input
    task_description = f"""
The user said: '{user_input}'

Recent memory context:
{memory_context}

Analyze this input and respond appropriately. If this is a complex task that requires:
- Code development
- Project planning  
- Technical implementation
- Multi-step processes

Then indicate delegation is needed by starting your response with "DELEGATE:" 

Otherwise, provide a helpful conversational response.
"""
    
    ux_task = Task(
        description=task_description,
        expected_output="A response to the user, optionally starting with 'DELEGATE:' if task delegation is needed.",
        agent=ux
    )
    
    # Run UX agent with suppressed output
    f = io.StringIO()
    with redirect_stdout(f):
        crew = Crew(agents=[ux], tasks=[ux_task], verbose=False)
        crew.kickoff()
    
    # Extract response
    raw_output = getattr(ux_task.output, "content", str(ux_task.output))
    
    # Check if delegation is needed
    needs_delegation = raw_output.startswith("DELEGATE:")
    if needs_delegation:
        response = raw_output[9:].strip()  # Remove "DELEGATE:" prefix
    else:
        response = raw_output
    
    # Save to memory
    try:
        memory.save(
            agent="UX",
            input_summary=user_input,
            output_summary=response,
            task_id=str(ux_task.id),
        )
    except Exception:
        pass
    
    return response, needs_delegation

def execute_crew_delegation(user_input: str, memory: MemoryStore, deliverables_dir: str) -> str:
    """
    Execute full crew delegation: Planner → Dev → Commander
    Returns path to saved deliverable file.
    """
    from agents import planner, dev, commander
    
    # Step 1: Planner breaks down the task
    planner_task = Task(
        description=f"Break down this user request into specific, actionable development tasks: '{user_input}'",
        expected_output="A numbered list of specific development tasks with technical details.",
        agent=planner
    )
    
    # Step 2: Dev implements the plan
    dev_task = Task(
        description="Implement the planned tasks using appropriate technology. Provide complete, working code.",
        expected_output="Complete implementation with code, documentation, and usage instructions.",
        agent=dev
    )
    
    # Step 3: Commander reviews and provides next steps
    commander_task = Task(
        description="Review the implementation and provide evaluation, improvements, and next steps.",
        expected_output="Technical review with recommendations and suggested next actions.",
        agent=commander
    )
    
    # Execute crew workflow
    crew = Crew(
        agents=[planner, dev, commander],
        tasks=[planner_task, dev_task, commander_task],
        verbose=True
    )
    
    result = crew.kickoff()
    
    # Save deliverable
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deliverable_file = f"{deliverables_dir}/{timestamp}_crew_deliverable.md"
    
    deliverable_content = f"""# Crew Deliverable - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## User Request
{user_input}

## Planner Output
{getattr(planner_task.output, 'content', str(planner_task.output))}

## Dev Implementation  
{getattr(dev_task.output, 'content', str(dev_task.output))}

## Commander Review
{getattr(commander_task.output, 'content', str(commander_task.output))}

## Full Result
{result}
"""
    
    with open(deliverable_file, 'w') as f:
        f.write(deliverable_content)
    
    # Save to memory
    try:
        for task in [planner_task, dev_task, commander_task]:
            memory.save(
                agent=task.agent.__class__.__name__,
                input_summary=task.description,
                output_summary=getattr(task.output, 'content', str(task.output)),
                task_id=str(task.id)
            )
    except Exception as e:
        print(f"⚠️ Memory save failed: {e}")
    
    return deliverable_file

def call_llm(prompt: str) -> str:
    """Optional LLM fallback function for direct API calls."""
    import requests

    url = os.environ["OPENAI_API_BASE"] + "/chat/completions"
    model = os.getenv("OPENAI_API_MODEL")
    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2048
    }

    timeout = int(os.environ.get("LM_TIMEOUT", 60))

    try:
        response = requests.post(url, headers=headers, json=body, timeout=timeout)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, ValueError) as e:
        raise ValueError(f"Invalid response from LLM call: {e}")

def check_model_compatibility() -> tuple[bool, str]:
    """Check if the current model is compatible with CrewAI."""
    from utils.model_selector import test_model_compatibility
    
    try:
        is_compatible, message = test_model_compatibility()
        return is_compatible, message
    except Exception as e:
        return False, f"Could not check model compatibility: {e}"

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Crew AI Assistant - Local AI orchestration platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # CrewAI UX shell mode (default)
  %(prog)s --crew             # Run full crew workflow
  %(prog)s --select-model     # Select and test model compatibility
        """
    )
    parser.add_argument("--crew", action="store_true", help="Run full crew workflow")
    parser.add_argument("--select-model", action="store_true", help="Interactively select model")
    parser.add_argument("--raw", action="store_true", help="Raw output mode (for UX)")
    args = parser.parse_args()
    
    # === Load environment variables ===
    load_dotenv()
    
    # === Set default model if not specified ===
    if not os.getenv("OPENAI_API_MODEL"):
        os.environ["OPENAI_API_MODEL"] = "microsoft/phi-4-mini-reasoning"
    
    # === Model selection ===
    if args.select_model:
        select_model()
        return
    
    # === Check model compatibility for crew mode ===
    if args.crew:
        print("🔍 Checking model compatibility...")
        is_compatible, message = check_model_compatibility()
        
        if not is_compatible:
            print(f"⚠️  {message}")
            print("💡 Try: python crew_agents.py --select-model")
            print("💡 Default mode is UX shell")
            return
        
        print(f"✅ {message}")
        run_crew()
        return
    
    # === Default to UX mode ===
    print("🧠 Starting CrewAI UX mode (default)")
    print("💡 For full crew workflow, use: python crew_agents.py --crew")
    print("💡 For model selection, use: python crew_agents.py --select-model")
    print()
    
    run_ux_shell(raw_mode=args.raw)

if __name__ == "__main__":
    main()