import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.agent_registry import discover_agents


def test_discover_agents():
    agents = discover_agents()
    assert "Planner" in agents
    assert "Dev" in agents
    assert "Commander" in agents
