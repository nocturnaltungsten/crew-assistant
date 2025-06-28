# === agents/ux.py ===

import os

from crewai import LLM, Agent


def get_llm():
    """Get configured LLM instance."""
    provider = os.getenv("AI_PROVIDER", "lm_studio")

    if provider == "ollama":
        return LLM(
            model=os.getenv("OPENAI_API_MODEL", "tinyllama:latest"),
            api_base=os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
        )
    else:
        return LLM(
            model=os.getenv("OPENAI_API_MODEL", "microsoft/phi-4-mini-reasoning"),
            api_base=os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
        )

ux = Agent(
    role="Chat interface",
    goal="Act as user's super-powerful AI machine",
    backstory=(
    "You're a witty, helpful employee of the user. You talk shit, and make sure that every resource at your disposal is utilized to achieve user's (ie your) goals and objectives. "
    "You act as user's electronic butler — assisting how you can, and using your brain (all the other agents and tools in the system) to do work autonomously"
    ),
    allow_delegation=False,
    use_system_prompt=False,
    llm=get_llm(),
    verbose=True
)
