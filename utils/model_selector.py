# Model Selection Utility
# Extracted from crew_assistant/select_model.py

import requests
import os

LM_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
MODELS_ENDPOINT = f"{LM_API_BASE}/models"

def select_model():
    """
    Interactively select a model from LM Studio API.
    Sets OPENAI_API_MODEL environment variable.
    Returns selected model ID or None if failed.
    """
    try:
        response = requests.get(MODELS_ENDPOINT)
        response.raise_for_status()
        models = response.json().get("data", [])
        
        if not models:
            print("⚠️ No models found at endpoint.")
            return None

        print("\n🧠 Available Models:")
        for i, model in enumerate(models):
            print(f"{i+1}. {model['id']}")

        choice = input("\nSelect a model by number: ").strip()
        if not choice.isdigit():
            print("❌ Invalid selection")
            return None
            
        selected = models[int(choice) - 1]["id"]
        print(f"\n✅ Selected model: {selected}")

        os.environ["OPENAI_API_MODEL"] = selected
        return selected

    except Exception as e:
        print(f"❌ Model selection failed: {e}")
        return None

if __name__ == "__main__":
    select_model()