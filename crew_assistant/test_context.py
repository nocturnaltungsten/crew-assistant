# === FILE: test_context.py ===
from core.context_engine import MemoryStore

store = MemoryStore()
store.save_entry(
    agent="DevAgent",
    input_summary="Build memory_store with context saving and loading",
    output_summary="Successfully created and tested save/load"
)
print("🧠 Last memory entries:")
for entry in store.latest(2):
    print(entry)
