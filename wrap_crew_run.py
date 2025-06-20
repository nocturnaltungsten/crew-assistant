# === FILE: wrap_crew_run.py ===

import os
import sys
import json
import uuid
import datetime
import subprocess
import argparse
import requests
import re

# === CONFIGURATION ===
SNAPSHOT_DIR = "crew_runs"
DEFAULT_MODEL = os.getenv("OPENAI_API_MODEL", "mistral-7b-instruct")  # fallback if selection disabled
LM_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")

# Ensure snapshot directory exists
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# === ARGUMENT PARSING ===
parser = argparse.ArgumentParser(description="Wrap a CrewAI run and snapshot the output")
parser.add_argument("--label", type=str, default=None, help="Optional run label for readability")
args = parser.parse_args()

# === MODEL SELECTION (if enabled) ===
def select_model():
    try:
        response = requests.get(f"{LM_API_BASE}/models")
        response.raise_for_status()
        models = response.json().get("data", [])
        if not models:
            print("⚠️ No models returned from LM Studio.")
            return DEFAULT_MODEL

        print("\n🧠 Available Models:")
        for i, model in enumerate(models):
            print(f"{i+1}. {model['id']}")

        choice = input("\nSelect a model by number (or press Enter for default): ").strip()
        selected = models[int(choice) - 1]["id"] if choice else DEFAULT_MODEL
        os.environ["OPENAI_API_MODEL"] = selected
        print(f"✅ Using model: {selected}")
        return selected

    except Exception as e:
        print(f"❌ Model selection failed: {e}")
        print(f"⚙️  Falling back to default model: {DEFAULT_MODEL}")
        os.environ["OPENAI_API_MODEL"] = DEFAULT_MODEL
        return DEFAULT_MODEL

if os.getenv("SELECT_MODEL_ON_START", "true").lower() in ("true", "1", "yes"):
    select_model()
else:
    print(f"📦 Model selection disabled. Using: {DEFAULT_MODEL}")
    os.environ["OPENAI_API_MODEL"] = DEFAULT_MODEL

# === SNAPSHOT METADATA ===
run_id = str(uuid.uuid4())
label = args.label or ""
timestamp = datetime.datetime.now().isoformat()
snapshot_file = os.path.join(SNAPSHOT_DIR, f"{timestamp[:19].replace(':','-')}__{label or run_id}.json")

# === IMPORT SummaryQueue ===
try:
    from summary_queue import SummaryQueue
    summary_queue = SummaryQueue(flush_limit=5)
except ImportError:
    summary_queue = None
    print("⚠️  summary_queue module not available. Summarization disabled.")

# === EXECUTE CREW RUN ===
print(f"\n🚀 Starting CrewAI Run: {label or run_id}\n")

process = subprocess.Popen(
    [sys.executable, "crew_agents.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

output_lines = []
current_agent = None
current_task_id = None
current_output = []

agent_pattern = re.compile(r"# Agent:\s*\x1b\[.*?m(.*?)\x1b\[")
task_pattern = re.compile(r"Task:\s*([0-9a-f\-]+)")
final_answer_pattern = re.compile(r"# Final Answer:", re.IGNORECASE)

while True:
    line = process.stdout.readline()
    if not line and process.poll() is not None:
        break
    if line:
        print(line, end="")
        output_lines.append(line)

        # Track agent and task info
        agent_match = agent_pattern.search(line)
        if agent_match:
            if current_agent and current_output and summary_queue:
                # Flush previous agent's output to summary
                summary_queue.add(current_agent, current_task_id, "".join(current_output))
                current_output = []

            current_agent = agent_match.group(1).strip()
            current_task_id = None  # reset on new agent

        task_match = task_pattern.search(line)
        if task_match:
            current_task_id = task_match.group(1)

        if current_agent:
            current_output.append(line)

if summary_queue and current_agent and current_output:
    summary_queue.add(current_agent, current_task_id, "".join(current_output))

returncode = process.poll()

# === SNAPSHOT OUTPUT ===
snapshot_data = {
    "run_id": run_id,
    "label": label,
    "timestamp": timestamp,
    "model": os.environ.get("OPENAI_API_MODEL"),
    "returncode": returncode,
    "output": output_lines,
}

with open(snapshot_file, "w") as f:
    json.dump(snapshot_data, f, indent=2)

print(f"\n✅ CrewAI run complete. Snapshot saved to: {snapshot_file}\n")
