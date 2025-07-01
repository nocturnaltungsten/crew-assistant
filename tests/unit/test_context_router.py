"""Unit tests for context router functionality."""

from enum import auto
from unittest.mock import patch, MagicMock

import pytest

from src.crew_assistant.core.context_engine.context_router import (
    RoutingAction,
    route_context_event,
    hash_event,
    should_log_event,
    should_queue_for_summary,
    should_embed_event,
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


class TestShouldLogEvent:
    """Test event logging decision logic."""

    def test_should_log_user_input(self):
        """Test that user input events should be logged."""
        event = {"type": "user_input", "content": "Hello"}
        assert should_log_event(event) is True

    def test_should_log_agent_response(self):
        """Test that agent response events should be logged."""
        event = {"type": "agent_response", "agent": "UX", "content": "Response"}
        assert should_log_event(event) is True

    def test_should_not_log_heartbeat(self):
        """Test that heartbeat events should not be logged."""
        event = {"type": "heartbeat", "timestamp": "2024-01-01"}
        assert should_log_event(event) is False

    def test_should_not_log_debug(self):
        """Test that debug events should not be logged."""
        event = {"type": "debug", "message": "Debug info"}
        assert should_log_event(event) is False

    def test_should_log_unknown_type(self):
        """Test that unknown event types default to logging."""
        event = {"type": "unknown_type", "data": "something"}
        assert should_log_event(event) is True


class TestShouldQueueForSummary:
    """Test summary queue decision logic."""

    def test_should_queue_long_content(self):
        """Test that long content should be queued for summary."""
        event = {"type": "user_input", "content": "x" * 1000}
        assert should_queue_for_summary(event) is True

    def test_should_not_queue_short_content(self):
        """Test that short content should not be queued."""
        event = {"type": "user_input", "content": "Hello"}
        assert should_queue_for_summary(event) is False

    def test_should_queue_conversation_end(self):
        """Test that conversation end events should be queued."""
        event = {"type": "conversation_end", "content": "Short"}
        assert should_queue_for_summary(event) is True

    def test_should_not_queue_system_events(self):
        """Test that system events should not be queued."""
        event = {"type": "system", "content": "x" * 1000}
        assert should_queue_for_summary(event) is False


class TestShouldEmbedEvent:
    """Test embedding decision logic."""

    def test_should_embed_user_input(self):
        """Test that user input should be embedded."""
        event = {"type": "user_input", "content": "What is Python?"}
        assert should_embed_event(event) is True

    def test_should_embed_agent_response(self):
        """Test that agent responses should be embedded."""
        event = {"type": "agent_response", "content": "Python is a programming language"}
        assert should_embed_event(event) is True

    def test_should_not_embed_system_events(self):
        """Test that system events should not be embedded."""
        event = {"type": "system", "content": "System message"}
        assert should_embed_event(event) is False

    def test_should_not_embed_debug_events(self):
        """Test that debug events should not be embedded."""
        event = {"type": "debug", "content": "Debug information"}
        assert should_embed_event(event) is False

    def test_should_not_embed_empty_content(self):
        """Test that events with empty content should not be embedded."""
        event = {"type": "user_input", "content": ""}
        assert should_embed_event(event) is False

        event = {"type": "user_input", "content": "   "}
        assert should_embed_event(event) is False


class TestRouteContextEvent:
    """Test the main context routing function."""

    def test_route_ignore_debug(self):
        """Test that debug events are ignored."""
        event = {"type": "debug", "message": "Debug info"}
        action = route_context_event(event)
        assert action == RoutingAction.IGNORE

    def test_route_log_user_input(self):
        """Test that user input is logged."""
        event = {"type": "user_input", "content": "Hello"}
        action = route_context_event(event)
        assert action == RoutingAction.LOG

    def test_route_queue_long_content(self):
        """Test that long content is queued for summary."""
        event = {"type": "user_input", "content": "x" * 1000}
        action = route_context_event(event)
        assert action == RoutingAction.QUEUE_FOR_SUMMARY

    def test_route_embed_meaningful_content(self):
        """Test that meaningful content is embedded."""
        event = {"type": "user_input", "content": "What is machine learning?"}
        action = route_context_event(event)
        assert action == RoutingAction.EMBED

    def test_route_priority_order(self):
        """Test that routing actions follow priority order."""
        # Debug events are ignored regardless of content
        event = {"type": "debug", "content": "x" * 1000}
        assert route_context_event(event) == RoutingAction.IGNORE

        # Long content is queued before embedding
        event = {"type": "user_input", "content": "x" * 1000}
        action = route_context_event(event)
        assert action in [RoutingAction.QUEUE_FOR_SUMMARY, RoutingAction.EMBED]

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

    @patch("core.context_engine.context_router.should_log_event")
    @patch("core.context_engine.context_router.should_queue_for_summary")
    @patch("core.context_engine.context_router.should_embed_event")
    def test_route_with_mocked_decisions(self, mock_embed, mock_queue, mock_log):
        """Test routing with mocked decision functions."""
        event = {"type": "test", "content": "test"}

        # Test IGNORE path
        mock_log.return_value = False
        mock_queue.return_value = False
        mock_embed.return_value = False

        action = route_context_event(event)
        assert action == RoutingAction.IGNORE

        # Test LOG path
        mock_log.return_value = True
        mock_queue.return_value = False
        mock_embed.return_value = False

        action = route_context_event(event)
        assert action == RoutingAction.LOG

        # Test QUEUE_FOR_SUMMARY path
        mock_log.return_value = True
        mock_queue.return_value = True
        mock_embed.return_value = False

        action = route_context_event(event)
        assert action == RoutingAction.QUEUE_FOR_SUMMARY

        # Test EMBED path
        mock_log.return_value = True
        mock_queue.return_value = False
        mock_embed.return_value = True

        action = route_context_event(event)
        assert action == RoutingAction.EMBED
