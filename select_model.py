# === select_model.py ===
import requests
import os
import json

LM_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
MODELS_ENDPOINT = f"{LM_API_BASE}/models"

def select_model():
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
        selected = models[int(choice) - 1]["id"]
        print(f"\n✅ Selected model: {selected}")

        # Set for runtime use
        os.environ["OPENAI_API_MODEL"] = selected

        return selected

    except Exception as e:
        print(f"❌ Model selection failed: {e}")
        return None

# Usage
if __name__ == "__main__":
    select_model()
