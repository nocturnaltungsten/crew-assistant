from crewai import Crew, Agent, Task
from litellm import completion
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# === LLM Config ===
def call_llm(prompt):
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
    backstory="An eccentric genius with a passion for teaching computers how to teach coding.",
    verbose=True,
    llm=call_llm  # plug in function directly
)

# === Smoke test ===
print("✅ Commander online. Awaiting orders.")
