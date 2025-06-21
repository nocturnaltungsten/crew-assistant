# === FILE: core/agent_registry.py ===

import importlib
from pathlib import Path
from crewai import Agent

# Agents should be in 'agents/' dir and end with .py (excluding __init__.py)
AGENT_DIR = Path(__file__).parent.parent / "agents"


def discover_agents():
    agents = {}
    for py_file in AGENT_DIR.glob("*.py"):
        if py_file.name.startswith("__") or py_file.name == "__init__.py":
            continue

        mod_name = f"agents.{py_file.stem}"
        try:
            module = importlib.import_module(mod_name)
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, Agent) and hasattr(obj, "role"):
                    agents[obj.role] = obj
        except Exception as e:
            print(f"⚠️ Failed to import {mod_name}: {e}")

    return agents


# === Usage ===
if __name__ == "__main__":
    found = discover_agents()
    print("\n🧠 Agent Registry:")
    for role, agent in found.items():
        print(f"- {role} ({agent})")
