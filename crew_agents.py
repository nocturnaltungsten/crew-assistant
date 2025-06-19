from crewai import Crew, Agent, Task
import os

# === LM Studio Integration ===
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

def call_llm(prompt: str) -> str:
    response = completion(
        model=os.getenv("OPENAI_API_MODEL"),
        api_base=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048
    )
    return response['choices'][0]['message']['content']

# === Agents ===
commander = Agent(
    role="Commander",
    goal="Direct the crew toward agentic world domination, one Python script at a time.",
    backstory="An eccentric genius with a passion for teaching computers how to think.",
    verbose=True,
    llm=call_llm
)

planner = Agent(
    role="PlannerAgent",
    goal="Break down objectives into clear, well-scoped dev tasks.",
    backstory="An obsessive strategist who dreams in Gantt charts.",
    verbose=True,
    llm=call_llm
)

dev = Agent(
    role="DevAgent",
    goal="Write functional Python code to complete subtasks using LM Studio.",
    backstory="A caffeine-fueled hacker raised on Stack Overflow and Reddit.",
    verbose=True,
    llm=call_llm
)

# === Tasks ===
task1 = Task(
    description="Break down the goal 'Build an agent system to teach CS through a useful, engaging project' into 3–5 executable subtasks.",
    expected_output="A numbered list of 3–5 clearly defined development subtasks.",
    agent=planner
)

task2 = Task(
    description="Implement the first subtask using Python, assuming LM Studio is the LLM backend.",
    expected_output="A complete Python function or script implementing the first subtask.",
    agent=dev
)

task3 = Task(
    description="Evaluate the code and provide next steps for development.",
    expected_output="A critique of the implementation and a proposed next subtask or improvement.",
    agent=commander
)



# === Smoke test ===
print("✅ All agents online. Standing by for mission briefing.")

# === Crew Setup ===
crew = Crew(
    agents=[commander, planner, dev],
    tasks=[task1, task2, task3],
    verbose=2
)

# === Launch ===
result = crew.kickoff()
print("\n🎉 Mission Complete:\n")
print(result)
