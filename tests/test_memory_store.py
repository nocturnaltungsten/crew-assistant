import os
import sys
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.context_engine.memory_store import MemoryStore, MEMORY_DIR


def setup_module(module):
    # clean memory dir
    if os.path.isdir(MEMORY_DIR):
        shutil.rmtree(MEMORY_DIR)
    os.makedirs(MEMORY_DIR, exist_ok=True)


def test_save_and_recent():
    store = MemoryStore()
    store.save(agent="Tester", input_summary="in", output_summary="out")
    store.save(agent="Tester", input_summary="in2", output_summary="out2")

    recent = store.recent(agent="Tester", count=2)
    assert len(recent) == 2
    assert recent[0]["agent"] == "Tester"
