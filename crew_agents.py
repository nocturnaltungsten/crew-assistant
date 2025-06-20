# === crew_agents.py ===

from crewai import Crew, Task
from agents import commander, planner, dev
from core.context_engine.memory_store import MemoryStore
from dotenv import load_dotenv
from datetime import datetime
import os
import uuid
import json

# === Load environment variables ===
load_dotenv()

# === Initialize Context Store ===
memory = MemoryStore()

# === Create unique run ID and timestamp ===
run_id = str(uuid.uuid4())
run_timestamp = datetime.utcnow().isoformat()

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

# === Create Crew ===
crew = Crew(
    agents=[commander, planner, dev],
    tasks=[task1, task2, task3],
    verbose=True,
)

# === Run Crew and collect results ===
result = crew.kickoff()

# === Save memory snapshots ===
for task in crew.tasks:
    memory.save(
        agent=task.agent.__class__.__name__,
        input_summary=task.description,
        output_summary=task.output or "No output",
        task_id=task.id
    )

# === Save full-cycle JSON log ===
log_data = {
    "run_id": run_id,
    "timestamp": run_timestamp,
    "crew_name": crew.name,
    "results": [
        {
            "task_id": task.id,
            "agent": task.agent.__class__.__name__,
            "description": task.description,
            "output": task.output
        } for task in crew.tasks
    ]
}

# Create output directory if needed
os.makedirs("snapshots", exist_ok=True)

with open(f"snapshots/{run_timestamp}__first_full_cycle.json", "w") as f:
    json.dump(log_data, f, indent=2)

# === Report final result to terminal ===
print("\n✅ Mission Complete:\n")
print(result)

# === Optional LLM Fallback Function ===
def call_llm(prompt: str) -> str:
    import requests

    url = os.getenv("OPENAI_API_BASE") + "/chat/completions"
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
