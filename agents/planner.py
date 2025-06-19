from crewai import Agent

planner = Agent(
    role='Planner',
    goal='Break down high-level goals into manageable sub-tasks.',
    backstory='A strategic thinker who turns visions into roadmaps.',
    allow_delegation=False,
    verbose=True
)

