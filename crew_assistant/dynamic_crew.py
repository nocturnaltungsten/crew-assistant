# === FILE: dynamic_crew.py ===

from crewai import Crew, Task
from core.agent_registry import discover_agents

# Dynamically discover agents
agents = discover_agents()

# Define task descriptions
crew_tasks = [
    Task(
        description="Break down the goal 'Build an agent system to teach CS through a useful, engaging project' into 3–5 clearly defined development subtasks.",
        expected_output="A bulleted list of specific subtasks with enough detail to begin implementation.",
        agent=agents.get("Commander")
    ),
    Task(
        description="Implement the first subtask using Python, assuming LM Studio is running at http://localhost:1234/v1.",
        expected_output="A clean, readable Python script with docstrings.",
        agent=agents.get("Dev")
    ),
    Task(
        description="Evaluate the code and provide next steps for development.",
        expected_output="A brief review and a prioritized to-do list.",
        agent=agents.get("Planner")
    )
]

# Create and run the crew
crew = Crew(
    agents=list(agents.values()),
    tasks=crew_tasks,
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n🎯 Final Result:\n")
    print(result)
