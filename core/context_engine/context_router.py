# context_router.py
# ✨ The Dispatcher Module of the Context Engine

from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any
import hashlib

# === Action Types the router can take ===
class RoutingAction(Enum):
    IGNORE = auto()
    LOG = auto()
    QUEUE_FOR_SUMMARY = auto()
    EMBED = auto()

## dummy change
# === Main Routing Logic ===
def route_context_event(event: Dict[str, Any]) -> RoutingAction:
    """
    Decide what to do with a given context event.
    Events can be text snippets, interactions, observations, etc.

    Params:
    - event (dict): a dictionary representing one captured context item

    Returns:
    - RoutingAction enum specifying how to handle it
    """

    # === Basic Sanity Filters ===
    if not event or 'type' not in event or 'content' not in event:
        return RoutingAction.IGNORE

    content = event['content'].strip().lower()

    # === Ignore trivial events ===
    if len(content) < 5:
        return RoutingAction.IGNORE

    if content in {"ok", "yeah", "huh", "sure"}:
        return RoutingAction.IGNORE

    # === Log only ===
    if event['type'] in {"system", "meta"}:
        return RoutingAction.LOG

    # === Queue for summarization (long blocks of text, code, or transcripts) ===
    if event['type'] in {"code", "chat", "note"} and len(content) > 500:
        return RoutingAction.QUEUE_FOR_SUMMARY

    # === Embed everything else ===
    return RoutingAction.EMBED


# === Event Hashing ===
def hash_event(event: Dict[str, Any]) -> str:
    """
    Generate a stable hash for an event based on timestamp + content
    Used to deduplicate or track memory entries.
    """
    data = f"{event.get('timestamp')}|{event.get('content')}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


# === Example usage ===
if __name__ == "__main__":
    test_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "chat",
        "content": "Here is a really long transcript of a conversation..."
    }

    decision = route_context_event(test_event)
    print(f"Routing decision: {decision.name}")
    print(f"Event hash: {hash_event(test_event)}")
