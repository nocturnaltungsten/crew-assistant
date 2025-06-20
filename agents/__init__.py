# agents/__init__.py

from .commander import commander
from .planner import planner
from .dev import dev

# Optional: registry for dynamic access
AGENT_REGISTRY = {
    "Commander": commander,
    "Planner": planner,
    "Dev": dev,
}

__all__ = ["commander", "planner", "dev", "AGENT_REGISTRY"]

from .ux import ux
