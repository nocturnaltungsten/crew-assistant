# === crew_agents.py ===

from crewai import Crew, Task
from agents import commander, planner, dev
from crew_assistant.context.memory import MemoryStore
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
import uuid
import json

# === Load environment variables ===
load_dotenv()

# === Initialize Context Store ===
memory = MemoryStore()

# === Create unique run ID and timestamp ===
run_id = str(uuid.uuid4())
run_timestamp = datetime.now(timezone.utc).isoformat()

# === Define Tasks ===
task1 = Task(
    description="Break down the goal 'Build an agent system to teach CS through a useful, engaging project' into 3–5 clearly defined development subtasks.",
    expected_output="A numbered list of 3–5 clearly defined development subtasks.",
    agent=planner
)

task2 = Task(
    description="Implement the first subtask using Python, assuming LM Studio is running at http://localhost:1234/v1.",
    expected_output="A complete Python function or script implementing the first subtask.",
    agent=dev
)

task3 = Task(
    description="Evaluate the code and provide next steps for development.",
    expected_output="A critique of the implementation and a proposed next subtask.",
    agent=commander
)

# === Save initial memory context ===
for task in [task1, task2, task3]:
    memory.save(
        agent=task.agent.__class__.__name__,
        input_summary=task.description,
        output_summary="(Task queued)",
        task_id=str(task.id)
    )

# === Create and run Crew ===
crew = Crew(
    agents=[commander, planner, dev],
    tasks=[task1, task2, task3],
    verbose=True,
)

result = crew.kickoff()

# === Save memory snapshots after run ===
for task in crew.tasks:
    try:
        output_summary = getattr(task.output, "content", None)
        if not output_summary:
            output_summary = str(task.output) if task.output else "No output"

        memory.save(
            agent=task.agent.__class__.__name__,
            input_summary=task.description,
            output_summary=output_summary,
            task_id=str(task.id),
        )
    except Exception as e:
        print(f"⚠️ Memory save failed for task {task.id}: {e}")

# === Save full-cycle JSON log ===
log_data = {
    "run_id": run_id,
    "timestamp": run_timestamp,
    "crew_name": crew.name,
    "results": []
}

for task in crew.tasks:
    try:
        log_data["results"].append({
            "task_id": str(task.id),
            "agent": task.agent.__class__.__name__,
            "description": task.description,
            "output": getattr(task.output, "content", str(task.output)) if task.output else "No output"
        })
    except Exception as e:
        log_data["results"].append({
            "task_id": str(task.id),
            "agent": task.agent.__class__.__name__,
            "description": task.description,
            "output": f"[ERROR serializing output: {e}]"
        })

# Create output directory if needed
os.makedirs("snapshots", exist_ok=True)

safe_ts = run_timestamp.replace(":", "-")
with open(f"snapshots/{safe_ts}__first_full_cycle.json", "w") as f:
    json.dump(log_data, f, indent=2)

# === Final output to terminal ===
print("\n✅ Mission Complete:\n")
print(result)

# === Optional LLM Fallback Function ===
def call_llm(prompt: str) -> str:
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

    response = requests.post(url, headers=headers, json=body)
    return response.json()["choices"][0]["message"]["content"]
