# === FILE: ux_loop.py ===

import os
import json
import uuid
import datetime
import re

from agents import ux
from core.context_engine.memory_store import MemoryStore
from core.context_engine.fact_store import FactStore
from crewai import Crew, Task

# === SETUP ===
DEFAULT_MODEL = os.getenv("OPENAI_API_MODEL", "mistral-7b-instruct")
print("🧠 System Online. Type 'exit' to disengage.\n")

# === STATE ===
memory = MemoryStore()
facts = FactStore()
chat_log = []
session_id = str(uuid.uuid4())
timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
snapshot_dir = "crew_runs"
os.makedirs(snapshot_dir, exist_ok=True)
snapshot_file = os.path.join(snapshot_dir, f"{timestamp[:19].replace(':','-')}__uxloop__{session_id}.json")

# === FACT LEARNING ===
def learn_fact_if_possible(text):
    patterns = {
        r"(?i)my name is ([a-zA-Z ]{2,})": "name",
        r"(?i)you can call me ([a-zA-Z ]{2,})": "aliases",
        r"(?i)my partner is ([a-zA-Z ]{2,})": "partner",
        r"(?i)i prefer ([a-zA-Z0-9 \-]+)": "preference"
    }
    for pattern, key in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if key == "preference":
                key = f"preferred_{value.lower().replace(' ', '_')}"
                value = "true"
            facts.set(key, value)
            print(f"💾 Learned fact: {key} = {value}")

# === LOOP ===
while True:
    try:
        user_input = input("👤 > ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            print("🫡 UX Agent signing off.")
            break

        # === Build memory context ===
        memory_dir = "memory/memory_store"
        memory_context = []
        if os.path.isdir(memory_dir):
            for filename in sorted(os.listdir(memory_dir))[-10:]:
                try:
                    with open(os.path.join(memory_dir, filename)) as mf:
                        entry = json.load(mf)
                        memory_context.append(f"[{entry['agent']}] {entry['input_summary']}: {entry['output_summary']}")
                except Exception:
                    continue
        memory_text = "\n".join(memory_context)
        fact_text = facts.as_text()

        # === Build task ===
        ux_task = Task(
            description=f"""
The user said: '{user_input}'.

Your known facts:
{fact_text}

Recent memory:
{memory_text}

Respond as the system's voice. You are Avery's assistant and brain. Speak clearly, helpfully, and with subtle confidence.
""",
            expected_output="A helpful and irreverent response. You may act on the user's behalf.",
            agent=ux
        )

        ux_crew = Crew(agents=[ux], tasks=[ux_task], verbose=False)
        result = ux_crew.kickoff()

        result_text = getattr(ux_task.output, "content", str(ux_task.output))

        print(f"\n🤖 UX Agent Says:\n\n{result_text}\n")

        # === Store memory ===
        memory.save(
            agent="UX",
            input_summary=user_input,
            output_summary=result_text,
            task_id=str(ux_task.id),
        )

        learn_fact_if_possible(user_input)
        learn_fact_if_possible(result_text)

        chat_log.append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "input": user_input,
            "output": result_text
        })

    except KeyboardInterrupt:
        print("\n🫡 UX Agent signing off.")
        break
    except Exception as e:
        print(f"❌ Error: {e}")

# === Final snapshot ===
with open(snapshot_file, "w") as f:
    json.dump({
        "session_id": session_id,
        "timestamp": timestamp,
        "model": DEFAULT_MODEL,
        "chat_log": chat_log
    }, f, indent=2)

print(f"💾 Session log saved: {snapshot_file}")