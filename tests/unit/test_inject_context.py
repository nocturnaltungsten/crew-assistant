"""Unit tests for context injection functionality."""

from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from core.context_engine.inject_context import ContextInjector
from core.context_engine.memory_store import MemoryStore
from core.context_engine.fact_store import FactStore


class TestContextInjector:
    """Test the ContextInjector class."""
    
    def test_initialization_default(self):
        """Test context injector initialization with defaults."""
        injector = ContextInjector()
        
        assert injector.memory_dir == Path("memory/memory_store")
        assert injector.facts_dir == Path("memory/facts")
    
    def test_initialization_custom_paths(self, temp_dir: Path):
        """Test context injector initialization with custom paths."""
        memory_dir = temp_dir / "custom_memory"
        facts_dir = temp_dir / "custom_facts"
        
        injector = ContextInjector(memory_dir=memory_dir, facts_dir=facts_dir)
        
        assert injector.memory_dir == memory_dir
        assert injector.facts_dir == facts_dir
    
    @patch('core.context_engine.inject_context.MemoryStore')
    @patch('core.context_engine.inject_context.FactStore')
    def test_get_context_ux_agent(self, mock_fact_store, mock_memory_store, temp_dir: Path):
        """Test getting context for UX agent."""
        # Setup mocks
        mock_memory = MagicMock()
        mock_facts = MagicMock()
        
        mock_memory_store.return_value = mock_memory
        mock_fact_store.return_value = mock_facts
        
        mock_memory.recent.return_value = [
            {
                "timestamp": "2024-01-01 10:00:00",
                "agent": "UX",
                "input_summary": "User asked about Python",
                "output_summary": "Explained Python basics"
            }
        ]
        mock_facts.as_text.return_value = "user_name: Alice\nfavorite_language: Python"
        
        injector = ContextInjector(memory_dir=temp_dir, facts_dir=temp_dir)
        context = injector.get_context(agent="UX", max_items=5)
        
        assert isinstance(context, str)
        assert "Recent memories" in context
        assert "Known facts" in context
        assert "User asked about Python" in context
        assert "user_name: Alice" in context
        
        mock_memory.recent.assert_called_once_with(agent="UX", count=5)
        mock_facts.as_text.assert_called_once()
    
    @patch('core.context_engine.inject_context.MemoryStore')
    @patch('core.context_engine.inject_context.FactStore')
    def test_get_context_no_memories(self, mock_fact_store, mock_memory_store):
        """Test getting context when no memories exist."""
        mock_memory = MagicMock()
        mock_facts = MagicMock()
        
        mock_memory_store.return_value = mock_memory
        mock_fact_store.return_value = mock_facts
        
        mock_memory.recent.return_value = []
        mock_facts.as_text.return_value = ""
        
        injector = ContextInjector()
        context = injector.get_context(agent="UX")
        
        assert isinstance(context, str)
        assert "No recent memories" in context or "Recent memories:" in context
        assert "No known facts" in context or "Known facts:" in context
    
    @patch('core.context_engine.inject_context.MemoryStore')
    @patch('core.context_engine.inject_context.FactStore')
    def test_get_context_specific_agent(self, mock_fact_store, mock_memory_store):
        """Test getting context for specific agent."""
        mock_memory = MagicMock()
        mock_facts = MagicMock()
        
        mock_memory_store.return_value = mock_memory
        mock_fact_store.return_value = mock_facts
        
        mock_memory.recent.return_value = [
            {
                "timestamp": "2024-01-01 11:00:00",
                "agent": "Planner",
                "input_summary": "Break down web scraping task",
                "output_summary": "Created 5 subtasks"
            }
        ]
        mock_facts.as_text.return_value = "project_type: web_scraping"
        
        injector = ContextInjector()
        context = injector.get_context(agent="Planner", max_items=3)
        
        mock_memory.recent.assert_called_once_with(agent="Planner", count=3)
        assert "Break down web scraping task" in context
    
    @patch('core.context_engine.inject_context.MemoryStore')
    @patch('core.context_engine.inject_context.FactStore')
    def test_get_context_multiple_memories(self, mock_fact_store, mock_memory_store):
        """Test getting context with multiple memories."""
        mock_memory = MagicMock()
        mock_facts = MagicMock()
        
        mock_memory_store.return_value = mock_memory
        mock_fact_store.return_value = mock_facts
        
        mock_memory.recent.return_value = [
            {
                "timestamp": "2024-01-01 10:00:00",
                "agent": "UX",
                "input_summary": "First question",
                "output_summary": "First answer"
            },
            {
                "timestamp": "2024-01-01 10:05:00",
                "agent": "UX",
                "input_summary": "Second question",
                "output_summary": "Second answer"
            },
            {
                "timestamp": "2024-01-01 10:10:00",
                "agent": "UX",
                "input_summary": "Third question",
                "output_summary": "Third answer"
            }
        ]
        mock_facts.as_text.return_value = "session_count: 3"
        
        injector = ContextInjector()
        context = injector.get_context(agent="UX", max_items=10)
        
        assert "First question" in context
        assert "Second question" in context
        assert "Third question" in context
        assert "session_count: 3" in context
    
    @patch('core.context_engine.inject_context.MemoryStore')
    @patch('core.context_engine.inject_context.FactStore')
    def test_get_context_with_task_ids(self, mock_fact_store, mock_memory_store):
        """Test getting context with task IDs in memories."""
        mock_memory = MagicMock()
        mock_facts = MagicMock()
        
        mock_memory_store.return_value = mock_memory
        mock_fact_store.return_value = mock_facts
        
        mock_memory.recent.return_value = [
            {
                "timestamp": "2024-01-01 10:00:00",
                "agent": "Dev",
                "input_summary": "Implement feature X",
                "output_summary": "Feature X implemented",
                "task_id": "task_123"
            }
        ]
        mock_facts.as_text.return_value = ""
        
        injector = ContextInjector()
        context = injector.get_context(agent="Dev")
        
        assert "Implement feature X" in context
        assert "task_123" in context or "task_id" in context
    
    @patch('core.context_engine.inject_context.MemoryStore')
    def test_memory_store_error_handling(self, mock_memory_store):
        """Test handling of memory store errors."""
        mock_memory_store.side_effect = Exception("Memory store error")
        
        injector = ContextInjector()
        
        # Should handle error gracefully
        context = injector.get_context(agent="UX")
        assert isinstance(context, str)
        # Should return minimal context when memory fails
        assert len(context) > 0
    
    @patch('core.context_engine.inject_context.FactStore')
    def test_fact_store_error_handling(self, mock_fact_store):
        """Test handling of fact store errors."""
        mock_fact_store.side_effect = Exception("Fact store error")
        
        injector = ContextInjector()
        
        # Should handle error gracefully
        context = injector.get_context(agent="UX")
        assert isinstance(context, str)
        # Should return minimal context when facts fail
        assert len(context) > 0
    
    def test_context_formatting(self):
        """Test that context is properly formatted."""
        with patch('core.context_engine.inject_context.MemoryStore') as mock_memory_store, \
             patch('core.context_engine.inject_context.FactStore') as mock_fact_store:
            
            mock_memory = MagicMock()
            mock_facts = MagicMock()
            
            mock_memory_store.return_value = mock_memory
            mock_fact_store.return_value = mock_facts
            
            mock_memory.recent.return_value = [
                {
                    "timestamp": "2024-01-01 10:00:00",
                    "agent": "UX",
                    "input_summary": "Test input",
                    "output_summary": "Test output"
                }
            ]
            mock_facts.as_text.return_value = "test_fact: test_value"
            
            injector = ContextInjector()
            context = injector.get_context()
            
            # Check that context has proper structure
            lines = context.split('\n')
            assert len(lines) > 1
            assert any("Recent memories" in line or "memories" in line.lower() for line in lines)
            assert any("facts" in line.lower() for line in lines)
    
    def test_max_items_parameter(self):
        """Test that max_items parameter is properly used."""
        with patch('core.context_engine.inject_context.MemoryStore') as mock_memory_store, \
             patch('core.context_engine.inject_context.FactStore') as mock_fact_store:
            
            mock_memory = MagicMock()
            mock_facts = MagicMock()
            
            mock_memory_store.return_value = mock_memory
            mock_fact_store.return_value = mock_facts
            
            mock_memory.recent.return_value = []
            mock_facts.as_text.return_value = ""
            
            injector = ContextInjector()
            
            # Test different max_items values
            injector.get_context(max_items=1)
            mock_memory.recent.assert_called_with(agent="UX", count=1)
            
            injector.get_context(max_items=10)
            mock_memory.recent.assert_called_with(agent="UX", count=10)
    
    def test_unicode_in_context(self):
        """Test handling of unicode characters in context."""
        with patch('core.context_engine.inject_context.MemoryStore') as mock_memory_store, \
             patch('core.context_engine.inject_context.FactStore') as mock_fact_store:
            
            mock_memory = MagicMock()
            mock_facts = MagicMock()
            
            mock_memory_store.return_value = mock_memory
            mock_fact_store.return_value = mock_facts
            
            mock_memory.recent.return_value = [
                {
                    "timestamp": "2024-01-01 10:00:00",
                    "agent": "UX",
                    "input_summary": "Question about café ☕",
                    "output_summary": "Answer about café culture 🎉"
                }
            ]
            mock_facts.as_text.return_value = "favorite_emoji: 😀\nlocation: naïve_café"
            
            injector = ContextInjector()
            context = injector.get_context()
            
            assert "café ☕" in context
            assert "😀" in context
            assert "naïve_café" in context