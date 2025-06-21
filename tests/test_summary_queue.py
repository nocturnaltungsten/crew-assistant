from crew_assistant.context import summary
from crew_assistant.context.summary import SummaryQueue


def test_queue_flush(tmp_path, monkeypatch):
    queue_dir = tmp_path / "summary"
    queue_dir.mkdir()
    monkeypatch.setattr(summary, "SUMMARY_QUEUE_DIR", str(queue_dir))
    flushed = []
    q = SummaryQueue(flush_limit=2, on_flush=lambda data: flushed.extend(data))
    q.add("hello", "user1")
    assert q.pending() == 1
    q.add("world", "user2")
    assert q.pending() == 0
    assert len(flushed) == 2
