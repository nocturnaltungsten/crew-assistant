"""
wrap_crew_run.py

A wrapper script for executing crew_agents.py with full observability and snapshotting.
Captures all stdout, agent output, and timestamps into a structured JSON file
for replay, debugging, or performance review. Now includes dynamic model selection.

Location: root or /core/tools/
Usage: python wrap_crew_run.py [--label optional_run_name]
"""

import os
import sys
import json
import uuid
import datetime
import subprocess
import argparse
import requests

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

# === EXECUTE CREW RUN ===
print(f"\n🚀 Starting CrewAI Run: {label or run_id}\n")

process = subprocess.Popen(
    [sys.executable, "crew_agents.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

output_lines = []
while True:
    line = process.stdout.readline()
    if not line and process.poll() is not None:
        break
    if line:
        print(line, end="")
        output_lines.append(line)

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
