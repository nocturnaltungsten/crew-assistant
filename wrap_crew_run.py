"""
wrap_crew_run.py

A wrapper script for executing crew_agents.py with full observability and snapshotting.
Captures all stdout, agent output, and timestamps into a structured JSON file
for replay, debugging, or performance review.

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

# === Constants ===
SNAPSHOT_DIR = "crew_runs"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Wrap a CrewAI run and snapshot the output")
parser.add_argument("--label", type=str, default=None, help="Optional run label for readability")
args = parser.parse_args()

# === Generate Snapshot Metadata ===
run_id = str(uuid.uuid4())
label = args.label or ""
timestamp = datetime.datetime.now().isoformat()
snapshot_file = os.path.join(SNAPSHOT_DIR, f"{timestamp[:19].replace(':','-')}__{label or run_id}.json")

# === Capture Crew Output ===
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

# === Store Snapshot ===
snapshot_data = {
    "run_id": run_id,
    "label": label,
    "timestamp": timestamp,
    "returncode": returncode,
    "output": output_lines,
}

with open(snapshot_file, "w") as f:
    json.dump(snapshot_data, f, indent=2)

print(f"\n✅ CrewAI run complete. Snapshot saved to: {snapshot_file}\n")
