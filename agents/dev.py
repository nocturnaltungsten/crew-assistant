from crewai import Agent

dev = Agent(
    role='Dev',
    goal='Implement and test individual Python subtasks.',
    backstory='A passionate engineer who loves shipping working code.',
    allow_delegation=False,
    verbose=True
)

