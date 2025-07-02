"""Unit tests for context router functionality."""

from crew_assistant.core.context_engine.context_router import (
    RoutingAction,
    hash_event,
    route_context_event,
)


class TestRoutingAction:
    """Test the RoutingAction enum."""

    def test_routing_action_values(self):
        """Test that routing actions have expected values."""
        assert hasattr(RoutingAction, "IGNORE")
        assert hasattr(RoutingAction, "LOG")
        assert hasattr(RoutingAction, "QUEUE_FOR_SUMMARY")
        assert hasattr(RoutingAction, "EMBED")


class TestHashEvent:
    """Test event hashing functionality."""

    def test_hash_simple_event(self):
        """Test hashing a simple event."""
        event = {"type": "user_input", "content": "Hello world", "agent": "UX"}

        hash1 = hash_event(event)
        hash2 = hash_event(event)

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0

    def test_hash_different_events(self):
        """Test that different events produce different hashes."""
        event1 = {"type": "user_input", "content": "Hello"}
        event2 = {"type": "user_input", "content": "Goodbye"}

        hash1 = hash_event(event1)
        hash2 = hash_event(event2)

        assert hash1 != hash2

    def test_hash_order_independence(self):
        """Test that hash is independent of key order."""
        event1 = {"type": "test", "content": "data", "agent": "UX"}
        event2 = {"agent": "UX", "content": "data", "type": "test"}

        hash1 = hash_event(event1)
        hash2 = hash_event(event2)

        assert hash1 == hash2

    def test_hash_empty_event(self):
        """Test hashing empty event."""
        event = {}
        hash_result = hash_event(event)

        assert isinstance(hash_result, str)
        assert len(hash_result) > 0

    def test_hash_nested_data(self):
        """Test hashing event with nested data."""
        event = {"type": "complex", "data": {"nested": {"deep": "value"}, "list": [1, 2, 3]}}

        hash_result = hash_event(event)
        assert isinstance(hash_result, str)


# Removed outdated test classes that tested non-existent functions


class TestRouteContextEvent:
    """Test the main context routing function."""

    def test_route_ignore_debug(self):
        """Test that debug events are ignored."""
        event = {"type": "debug", "message": "Debug info"}
        action = route_context_event(event)
        assert action == RoutingAction.IGNORE

    def test_route_system_events_to_log(self):
        """Test that system events are logged."""
        event = {"type": "system", "content": "System message here"}
        action = route_context_event(event)
        assert action == RoutingAction.LOG

    def test_route_long_chat_to_summary(self):
        """Test that long chat content is queued for summary."""
        event = {"type": "chat", "content": "x" * 600}
        action = route_context_event(event)
        assert action == RoutingAction.QUEUE_FOR_SUMMARY

    def test_route_normal_content_to_embed(self):
        """Test that normal content is embedded."""
        event = {"type": "user_input", "content": "What is machine learning?"}
        action = route_context_event(event)
        assert action == RoutingAction.EMBED

    def test_route_empty_event(self):
        """Test routing empty event."""
        event = {}
        action = route_context_event(event)
        assert action in [RoutingAction.IGNORE, RoutingAction.LOG]

    def test_route_malformed_event(self):
        """Test routing malformed event."""
        event = {"malformed": True, 123: "invalid"}
        action = route_context_event(event)
        # Should handle gracefully without crashing
        assert isinstance(action, RoutingAction)

    def test_route_ignore_short_content(self):
        """Test that very short content is ignored."""
        event = {"type": "user_input", "content": "Hi"}
        action = route_context_event(event)
        assert action == RoutingAction.IGNORE

    def test_route_ignore_trivial_responses(self):
        """Test that trivial responses are ignored."""
        event = {"type": "user_input", "content": "ok"}
        action = route_context_event(event)
        assert action == RoutingAction.IGNORE
