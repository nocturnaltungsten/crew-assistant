# === crew_agents.py ===

from crewai import Crew, Task
from agents import commander, planner, dev
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# === Tasks ===
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

# === Crew Setup ===
crew = Crew(
    agents=[commander, planner, dev],
    tasks=[task1, task2, task3],
    verbose=True,
)

# === Launch ===
result = crew.kickoff()
print("\n✅ Mission Complete:\n")
print(result)

# === LLM Debug Fallback (Optional) ===
def call_llm(prompt: str) -> str:
    import requests
    import os

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
