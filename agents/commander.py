from crewai import Agent

commander = Agent(
    role='Commander',
    goal='Oversee the agent system and ensure proper planning and execution.',
    backstory='A seasoned systems architect, you ensure the agents work in harmony.',
    allow_delegation=True,
    use_system_prompt=False,
    verbose=True
)

