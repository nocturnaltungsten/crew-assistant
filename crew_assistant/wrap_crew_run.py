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
from agents import ux
from core.context_engine.memory_store import MemoryStore
from contextlib import redirect_stdout
import io

# === CONFIG ===
SNAPSHOT_DIR = "crew_runs"
DEFAULT_MODEL = os.getenv("OPENAI_API_MODEL", "mistral-7b-instruct")
LM_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# === ARGPARSE ===
parser = argparse.ArgumentParser(description="Run UX shell or full Crew")
parser.add_argument("--label", type=str, default=None)
parser.add_argument("--ux", action="store_true")
parser.add_argument("--raw", action="store_true")
args = parser.parse_args()

# === MODEL SELECTION ===
def select_model():
    try:
        res = requests.get(f"{LM_API_BASE}/models")
        res.raise_for_status()
        models = res.json().get("data", [])
        if not models:
            return DEFAULT_MODEL
        for i, m in enumerate(models): 
            print(f"{i+1}. {m['id']}")
        sel = input("\nSelect a model (or Enter for default): ").strip()
        selected = models[int(sel) - 1]["id"] if sel else DEFAULT_MODEL
        os.environ["OPENAI_API_MODEL"] = selected
        return selected
    except Exception:
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
    print("\n🧠 System online. Type 'exit' to disengage.\n")

    while True:
        user_input = input("👤 > ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("🫡 Signing off.")
            break

        # === Construct task with NO formatting in response ===
        task_description = (
            f"You are a sleek, helpful assistant. "
            f"Respond with plain English. No markdown, no JSON, no formatting — just talk."
            f"\n\nUser: {user_input}"
        )

        ux_task = Task(
            description=task_description,
            expected_output="Plain English. No formatting.",
            agent=ux
        )

        # === Silence CrewAI output ===
        capture = io.StringIO()
        with redirect_stdout(capture):
            crew = Crew(agents=[ux], tasks=[ux_task], verbose=False)
            result = crew.kickoff()
        _ = capture.getvalue()

        try:
            parsed = json.loads(getattr(ux_task.output, "content", str(ux_task.output)))
            reply = parsed.get("reply", str(parsed))
        except Exception:
            reply = getattr(ux_task.output, "content", str(ux_task.output))

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        border = "─" * 80

        if args.raw:
            print(reply)
        else:
            print(f"\n System │ {timestamp}\n{border}\n{reply}\n{border}")

        try:
            memory.save(
                agent="UX",
                input_summary=user_input,
                output_summary=reply,
                task_id=str(ux_task.id),
            )
        except Exception:
            # Best-effort memory logging. Continue on failure.
            pass

        run_id = str(uuid.uuid4())
        utc_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        safe_ts = utc_ts[:19].replace(":", "-")
        snapshot_file = os.path.join(SNAPSHOT_DIR, f"{safe_ts}__ux__{run_id}.json")

        with open(snapshot_file, "w") as sf:
            json.dump({
                "run_id": run_id,
                "timestamp": utc_ts,
                "model": os.environ["OPENAI_API_MODEL"],
                "input": user_input,
                "reply": reply,
                "raw": str(result),
            }, sf, indent=2)

    sys.exit(0)

# === FALLBACK: RUN crew_agents.py ===
print(f"\n🚀 Starting CrewAI Run: {args.label or uuid.uuid4()}\n")
process = subprocess.Popen(
    [sys.executable, "crew_agents.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

if process.stdout is not None:
    for line in process.stdout:
        print(line, end="")
