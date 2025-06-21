import os
import sys
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.context_engine.summary_queue import SummaryQueue, SUMMARY_QUEUE_DIR


def setup_module(module):
    if os.path.isdir(SUMMARY_QUEUE_DIR):
        shutil.rmtree(SUMMARY_QUEUE_DIR)
    os.makedirs(SUMMARY_QUEUE_DIR, exist_ok=True)


def test_queue_and_flush():
    sq = SummaryQueue(flush_limit=2)
    sq.add("one", "source")
    assert sq.pending() == 1
    sq.add("two", "source")
    # flush triggered
    assert sq.pending() == 0
    files = os.listdir(SUMMARY_QUEUE_DIR)
    assert files, "flush file not created"
