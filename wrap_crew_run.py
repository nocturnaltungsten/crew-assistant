# === FILE: wrap_crew_run.py ===

import os
import sys
import json
import uuid
import datetime
import subprocess
import argparse
import requests
from crewai import Crew, Task
from agents import ux, commander, planner, dev
from core.context_engine.memory_store import MemoryStore

# === CONFIG ===
SNAPSHOT_DIR = "crew_runs"
DEFAULT_MODEL = os.getenv("OPENAI_API_MODEL", "mistral-7b-instruct")
LM_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# === ARGPARSE ===
parser = argparse.ArgumentParser(description="Run UX shell or full Crew")
parser.add_argument("--label", type=str, default=None)
parser.add_argument("--ux", action="store_true")
args = parser.parse_args()

# === MODEL SELECTION ===
def select_model():
    try:
        res = requests.get(f"{LM_API_BASE}/models")
        res.raise_for_status()
        models = res.json().get("data", [])
        if not models:
            print("⚠️ No models found.")
            return DEFAULT_MODEL
        print("\n🧠 Available Models:")
        for i, m in enumerate(models):
            print(f"{i+1}. {m['id']}")
        sel = input("\nSelect a model (or Enter for default): ").strip()
        selected = models[int(sel) - 1]["id"] if sel else DEFAULT_MODEL
        os.environ["OPENAI_API_MODEL"] = selected
        print(f"✅ Using model: {selected}")
        return selected
    except Exception as e:
        print(f"❌ Model selection failed: {e}\nFallback: {DEFAULT_MODEL}")
        os.environ["OPENAI_API_MODEL"] = DEFAULT_MODEL
        return DEFAULT_MODEL

if os.getenv("SELECT_MODEL_ON_START", "true").lower() in ("true", "1", "yes"):
    select_model()
else:
    os.environ["OPENAI_API_MODEL"] = DEFAULT_MODEL

# === UX MODE ===
if args.ux:
    memory = MemoryStore()
    memdir = "memory/memory_store"
    print("🧠 System online. Type 'exit' to disengage.\n")

    while True:
        user_input = input("👤 > ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("🫡 Signing off.")
            break

        # === Get latest memory
        memory_lines = []
        if os.path.isdir(memdir):
            for filename in sorted(os.listdir(memdir))[-10:]:
                try:
                    with open(os.path.join(memdir, filename)) as mf:
                        entry = json.load(mf)
                        memory_lines.append(f"[{entry['agent']}] {entry['input_summary']}: {entry['output_summary']}")
                except Exception:
                    continue
        memory_context = "\n".join(memory_lines)

        # === Build UX Task
        ux_task = Task(
            description=f"""You are the system. The user said: "{user_input}".

Here is your latest memory:\n{memory_context}

Respond as their personal assistant. Reply in JSON with:
- 'reply': what to say to the user
- OPTIONAL 'handoff_to': one of ["Commander", "Planner", "Dev"]
- OPTIONAL 'handoff_description': task for that agent""",
            expected_output="A JSON string with reply and optional delegation fields.",
            agent=ux
        )

        run_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        safe_ts = timestamp[:19].replace(":", "-")
        snapshot_file = os.path.join(SNAPSHOT_DIR, f"{safe_ts}__ux__{run_id}.json")

        crew = Crew(agents=[ux], tasks=[ux_task], verbose=True)
        result = crew.kickoff()

        # === Parse UX JSON Output
        try:
            parsed = json.loads(getattr(ux_task.output, "content", str(ux_task.output)))
        except Exception as e:
            print(f"⚠️ Invalid UX output: {e}")
            parsed = {"reply": str(ux_task.output)}

        final_reply = parsed.get("reply", "[No response generated.]")

        # === Optional Agent Handoff
        agent_lookup = {
            "Commander": commander,
            "Planner": planner,
            "Dev": dev
        }

        delegated_result = None
        if parsed.get("handoff_to") and parsed.get("handoff_description"):
            target = parsed["handoff_to"]
            desc = parsed["handoff_description"]
            if target in agent_lookup:
                print(f"🧠 [Internal thought] Routing to {target}…")
                delegated_task = Task(
                    description=desc,
                    expected_output="A thoughtful response completing the task.",
                    agent=agent_lookup[target]
                )
                subcrew = Crew(agents=[agent_lookup[target]], tasks=[delegated_task], verbose=True)
                delegated_result = subcrew.kickoff()

                # Update final reply with result (but still from UX persona)
                final_reply += f"\n\n{delegated_result}"

                try:
                    memory.save(
                        agent=target,
                        input_summary=desc,
                        output_summary=getattr(delegated_task.output, "content", str(delegated_task.output)),
                        task_id=str(delegated_task.id)
                    )
                except Exception as e:
                    print(f"⚠️ Failed to log delegation: {e}")

        # === Memory Save
        try:
            memory.save(
                agent="UX",
                input_summary=user_input,
                output_summary=final_reply,
                task_id=str(ux_task.id),
            )
        except Exception as e:
            print(f"⚠️ Failed to save memory: {e}")

        # === Output
        print("\n🤖 System:\n")
        print(final_reply)

        # === Snapshot
        with open(snapshot_file, "w") as f:
            json.dump({
                "run_id": run_id,
                "timestamp": timestamp,
                "model": os.environ["OPENAI_API_MODEL"],
                "input": user_input,
                "reply": final_reply,
                "raw": str(result),
                "delegated_result": str(delegated_result) if delegated_result else None
            }, f, indent=2)

    sys.exit(0)

# === FALLBACK: RUN crew_agents.py ===
print(f"\n🚀 Starting CrewAI Run: {args.label or uuid.uuid4()}\n")
process = subprocess.Popen(
    [sys.executable, "crew_agents.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

if process.stdout:
    for line in process.stdout:
        print(line, end="")
