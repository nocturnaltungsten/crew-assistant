"""Main crew run logic reused by CLI wrappers."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from crewai import Crew, Task

from agents import commander, planner, dev
from core.context_engine.memory_store import MemoryStore
from core.context_engine.summary_queue import SummaryQueue


memory = MemoryStore()
summary_queue = SummaryQueue()


def build_tasks() -> list[Task]:
    return [
        Task(
            description="Break down the goal 'Build an agent system to teach CS through a useful, engaging project' into 3–5 clearly defined development subtasks.",
            expected_output="A numbered list of clear subtasks.",
            agent=planner,
        ),
        Task(
            description="Implement the first subtask using Python, assuming LM Studio is running at http://localhost:1234/v1.",
            expected_output="A Python script implementing the first subtask.",
            agent=dev,
        ),
        Task(
            description="Evaluate the code and provide next steps for development.",
            expected_output="A critique of the implementation and proposed next task.",
            agent=commander,
        ),
    ]


def run_crew() -> str:
    run_id = str(uuid.uuid4())
    run_timestamp = datetime.now(timezone.utc).isoformat()

    tasks = build_tasks()

    for task in tasks:
        memory.save(
            agent=task.agent.__class__.__name__,
            input_summary=task.description,
            output_summary="(Task queued)",
            task_id=str(task.id),
        )

    crew = Crew(agents=[commander, planner, dev], tasks=tasks, verbose=True)
    result = crew.kickoff()

    log_data = {
        "run_id": run_id,
        "timestamp": run_timestamp,
        "crew_name": crew.name,
        "results": [],
    }

    os.makedirs("snapshots", exist_ok=True)

    for task in crew.tasks:
        output = getattr(task.output, "content", str(task.output)) if task.output else "No output"
        memory.save(
            agent=task.agent.__class__.__name__,
            input_summary=task.description,
            output_summary=output,
            task_id=str(task.id),
        )
        summary_queue.add(content=output, source=task.agent.__class__.__name__)
        log_data["results"].append({
            "task_id": str(task.id),
            "agent": task.agent.__class__.__name__,
            "description": task.description,
            "output": output,
        })

    safe_ts = run_timestamp.replace(":", "-")
    with open(f"snapshots/{safe_ts}__run.json", "w") as f:
        json.dump(log_data, f, indent=2)

    summary_queue.flush()
    return result


if __name__ == "__main__":
    print(run_crew())
