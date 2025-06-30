"""Unit tests for summary queue functionality."""

import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

import pytest

from core.context_engine.summary_queue import SummaryQueue


class TestSummaryQueue:
    """Test the SummaryQueue class."""
    
    def test_initialization_default(self):
        """Test summary queue initialization with defaults."""
        queue = SummaryQueue()
        
        assert queue.queue_dir == Path("snapshots")
        assert queue.pending_items == []
    
    def test_initialization_custom_dir(self, temp_dir: Path):
        """Test summary queue initialization with custom directory."""
        custom_dir = temp_dir / "custom_summaries"
        queue = SummaryQueue(queue_dir=custom_dir)
        
        assert queue.queue_dir == custom_dir
        assert queue.pending_items == []
    
    def test_add_simple_content(self, temp_dir: Path):
        """Test adding simple content to queue."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        queue.add(content="Test content", source="test")
        
        assert len(queue.pending_items) == 1
        item = queue.pending_items[0]
        assert item["content"] == "Test content"
        assert item["source"] == "test"
        assert "timestamp" in item
        assert item["metadata"] is None
    
    def test_add_content_with_metadata(self, temp_dir: Path):
        """Test adding content with metadata."""
        queue = SummaryQueue(queue_dir=temp_dir)
        metadata = {"agent": "UX", "task_id": "123", "priority": "high"}
        
        queue.add(
            content="Important message", 
            source="user_input",
            metadata=metadata
        )
        
        assert len(queue.pending_items) == 1
        item = queue.pending_items[0]
        assert item["content"] == "Important message"
        assert item["source"] == "user_input"
        assert item["metadata"] == metadata
    
    def test_add_multiple_items(self, temp_dir: Path):
        """Test adding multiple items to queue."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        queue.add("First item", "source1")
        queue.add("Second item", "source2")
        queue.add("Third item", "source3")
        
        assert len(queue.pending_items) == 3
        assert queue.pending_items[0]["content"] == "First item"
        assert queue.pending_items[1]["content"] == "Second item"
        assert queue.pending_items[2]["content"] == "Third item"
    
    def test_pending_count(self, temp_dir: Path):
        """Test getting pending item count."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        assert queue.pending() == 0
        
        queue.add("Item 1", "source")
        assert queue.pending() == 1
        
        queue.add("Item 2", "source")
        assert queue.pending() == 2
    
    def test_flush_empty_queue(self, temp_dir: Path):
        """Test flushing empty queue."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        # Should not create any files
        queue.flush()
        
        assert len(list(temp_dir.glob("*.jsonl"))) == 0
        assert queue.pending() == 0
    
    def test_flush_with_items(self, temp_dir: Path):
        """Test flushing queue with items."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        queue.add("First content", "source1")
        queue.add("Second content", "source2", {"key": "value"})
        
        queue.flush()
        
        # Check that queue is empty
        assert queue.pending() == 0
        assert len(queue.pending_items) == 0
        
        # Check that file was created
        jsonl_files = list(temp_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 1
        
        # Check file content
        with open(jsonl_files[0]) as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        item1 = json.loads(lines[0])
        item2 = json.loads(lines[1])
        
        assert item1["content"] == "First content"
        assert item1["source"] == "source1"
        assert item2["content"] == "Second content"
        assert item2["metadata"]["key"] == "value"
    
    def test_flush_filename_format(self, temp_dir: Path):
        """Test that flush creates properly formatted filenames."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        queue.add("Test content", "test")
        
        with patch('core.context_engine.summary_queue.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 30, 45)
            mock_datetime.strftime = datetime.strftime
            
            queue.flush()
        
        expected_filename = "summary_20240101_123045.jsonl"
        expected_path = temp_dir / expected_filename
        
        assert expected_path.exists()
    
    def test_multiple_flushes(self, temp_dir: Path):
        """Test multiple flush operations."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        # First flush
        queue.add("First batch item 1", "source")
        queue.add("First batch item 2", "source")
        queue.flush()
        
        # Second flush
        queue.add("Second batch item", "source")
        queue.flush()
        
        # Check that two files were created
        jsonl_files = list(temp_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 2
        
        # Check content of files
        for file_path in jsonl_files:
            with open(file_path) as f:
                lines = f.readlines()
                assert len(lines) > 0
    
    def test_flush_creates_directory(self, temp_dir: Path):
        """Test that flush creates directory if it doesn't exist."""
        non_existent_dir = temp_dir / "non_existent" / "deep" / "path"
        queue = SummaryQueue(queue_dir=non_existent_dir)
        
        queue.add("Test content", "test")
        queue.flush()
        
        assert non_existent_dir.exists()
        assert non_existent_dir.is_dir()
        
        jsonl_files = list(non_existent_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 1
    
    def test_timestamp_format(self, temp_dir: Path):
        """Test that timestamps are properly formatted."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        queue.add("Test content", "test")
        
        item = queue.pending_items[0]
        timestamp = item["timestamp"]
        
        # Should be in ISO format
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        
        # Should be parseable as datetime
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)
    
    def test_unicode_handling(self, temp_dir: Path):
        """Test handling of unicode content."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        unicode_content = "Test with émojis 😀🎉 and spëcial chars"
        queue.add(unicode_content, "unicode_test")
        queue.flush()
        
        # Check that file was created and contains unicode
        jsonl_files = list(temp_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 1
        
        with open(jsonl_files[0], encoding='utf-8') as f:
            content = f.read()
            assert "émojis 😀🎉" in content
            assert "spëcial" in content
    
    def test_large_content(self, temp_dir: Path):
        """Test handling of large content."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        # Create large content (10KB)
        large_content = "x" * 10000
        queue.add(large_content, "large_test")
        queue.flush()
        
        jsonl_files = list(temp_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 1
        
        with open(jsonl_files[0]) as f:
            data = json.load(f)
            assert len(data["content"]) == 10000
    
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_flush_permission_error(self, mock_file, temp_dir: Path):
        """Test handling of permission errors during flush."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        queue.add("Test content", "test")
        
        # Should handle permission error gracefully
        with pytest.raises(PermissionError):
            queue.flush()
        
        # Items should still be in queue after failed flush
        assert queue.pending() == 1
    
    def test_edge_case_empty_content(self, temp_dir: Path):
        """Test adding empty content."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        queue.add("", "empty_content")
        queue.add("   ", "whitespace_content")
        
        assert queue.pending() == 2
        
        queue.flush()
        
        jsonl_files = list(temp_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 1
        
        with open(jsonl_files[0]) as f:
            lines = f.readlines()
            assert len(lines) == 2
    
    def test_metadata_types(self, temp_dir: Path):
        """Test different metadata types."""
        queue = SummaryQueue(queue_dir=temp_dir)
        
        # Test various metadata types
        metadata_list = [
            {"string": "value", "number": 42, "boolean": True},
            {"nested": {"deep": {"value": "test"}}},
            {"list": [1, 2, 3, "four"]},
            None
        ]
        
        for i, metadata in enumerate(metadata_list):
            queue.add(f"Content {i}", f"source_{i}", metadata)
        
        queue.flush()
        
        jsonl_files = list(temp_dir.glob("*.jsonl"))
        assert len(jsonl_files) == 1
        
        with open(jsonl_files[0]) as f:
            lines = f.readlines()
            assert len(lines) == len(metadata_list)
            
            for i, line in enumerate(lines):
                data = json.loads(line)
                assert data["metadata"] == metadata_list[i]