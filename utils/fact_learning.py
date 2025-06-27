# Fact Learning Utilities
# Extracted from crew_assistant/ux_loop.py

import re
from core.context_engine.fact_store import FactStore

def learn_fact_if_possible(text, fact_store=None):
    """
    Extract facts from text using regex patterns.
    
    Args:
        text (str): Input text to analyze
        fact_store (FactStore): Optional fact store instance
    
    Returns:
        dict: Extracted facts {key: value}
    """
    if fact_store is None:
        fact_store = FactStore()
    
    patterns = {
        r"(?i)my name is ([a-zA-Z ]{2,})": "name",
        r"(?i)you can call me ([a-zA-Z ]{2,})": "aliases", 
        r"(?i)my partner is ([a-zA-Z ]{2,})": "partner",
        r"(?i)i prefer ([a-zA-Z0-9 \-]+)": "preference"
    }
    
    extracted_facts = {}
    
    for pattern, key in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if key == "preference":
                key = f"preferred_{value.lower().replace(' ', '_')}"
                value = "true"
            
            fact_store.set(key, value)
            extracted_facts[key] = value
            print(f"💾 Learned fact: {key} = {value}")
    
    return extracted_facts

def build_memory_context(memory_dir="memory/memory_store", limit=10):
    """
    Build context string from recent memory entries.
    
    Args:
        memory_dir (str): Path to memory store directory
        limit (int): Max number of recent entries to include
    
    Returns:
        str: Formatted memory context
    """
    import os
    import json
    
    memory_context = []
    if os.path.isdir(memory_dir):
        for filename in sorted(os.listdir(memory_dir))[-limit:]:
            try:
                with open(os.path.join(memory_dir, filename)) as mf:
                    entry = json.load(mf)
                    memory_context.append(
                        f"[{entry['agent']}] {entry['input_summary']}: {entry['output_summary']}"
                    )
            except Exception:
                continue
    
    return "\n".join(memory_context)