# Model Selection Utility with Compatibility Checking
# Extracted from crew_assistant/select_model.py

import requests
import os
from typing import Dict, List, Tuple

LM_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1")
MODELS_ENDPOINT = f"{LM_API_BASE}/models"
CHAT_ENDPOINT = f"{LM_API_BASE}/chat/completions"

# Known compatible model patterns
COMPATIBLE_PATTERNS = [
    "instruct", "chat", "conversational", "dialog",
    "phi-3", "llama-3", "gemma", "mistral", "qwen"
]

INCOMPATIBLE_PATTERNS = [
    "base", "foundation", "embedding", "code-only"
]

def categorize_model_compatibility(model_id: str) -> Tuple[str, str]:
    """Categorize model compatibility based on name patterns."""
    model_lower = model_id.lower()
    
    # Check for known compatible patterns
    for pattern in COMPATIBLE_PATTERNS:
        if pattern in model_lower:
            return "✅ Compatible", "Supports chat completion format"
    
    # Check for known incompatible patterns  
    for pattern in INCOMPATIBLE_PATTERNS:
        if pattern in model_lower:
            return "❌ Incompatible", "Base model - needs fine-tuning for chat"
    
    # Unknown - needs testing
    return "❓ Unknown", "May need testing - try UX mode first"

def test_model_compatibility(model_id: str = None) -> Tuple[bool, str]:
    """Test if a model supports the chat completion format needed by CrewAI."""
    if model_id:
        os.environ["OPENAI_API_MODEL"] = model_id
    
    current_model = os.getenv("OPENAI_API_MODEL", "unknown")
    
    try:
        test_payload = {
            "model": current_model,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'not-needed')}"}
        response = requests.post(CHAT_ENDPOINT, json=test_payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, f"Model '{current_model}' is compatible with CrewAI"
        elif response.status_code == 400 and "jinja template" in response.text:
            return False, f"Model '{current_model}' has incompatible prompt template"
        elif response.status_code == 404:
            return False, f"Model '{current_model}' not found - load it in LM Studio first"
        else:
            return False, f"Model '{current_model}' test failed: {response.status_code}"
            
    except requests.RequestException as e:
        return False, f"Could not connect to LM Studio: {e}"
    except Exception as e:
        return False, f"Model compatibility test failed: {e}"

def get_available_models() -> List[Dict[str, str]]:
    """Get available models with compatibility information."""
    try:
        response = requests.get(MODELS_ENDPOINT, timeout=10)
        response.raise_for_status()
        models_data = response.json().get("data", [])
        
        enhanced_models = []
        for model in models_data:
            model_id = model.get("id", "unknown")
            status, note = categorize_model_compatibility(model_id)
            
            enhanced_models.append({
                "id": model_id,
                "status": status,
                "note": note,
                "raw": model
            })
        
        return enhanced_models
        
    except Exception as e:
        print(f"❌ Could not fetch models: {e}")
        return []

def select_model():
    """
    Interactively select a model with compatibility information.
    Shows compatibility status and tests selected model.
    """
    print("🔍 Fetching available models from LM Studio...")
    models = get_available_models()
    
    if not models:
        print("⚠️ No models found. Make sure LM Studio is running and has models loaded.")
        return None

    print("\n🧠 Available Models with Compatibility:")
    print("─" * 80)
    
    for i, model in enumerate(models):
        print(f"{i+1:2d}. {model['status']} {model['id']}")
        print(f"    📝 {model['note']}")
        print()

    while True:
        choice = input("Select a model by number (or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            return None
            
        if not choice.isdigit():
            print("❌ Please enter a valid number or 'q' to quit")
            continue
            
        try:
            model_index = int(choice) - 1
            if model_index < 0 or model_index >= len(models):
                print(f"❌ Please enter a number between 1 and {len(models)}")
                continue
                
            selected_model = models[model_index]
            model_id = selected_model["id"]
            
            print(f"\n🧪 Testing model '{model_id}'...")
            
            # Test the model
            is_compatible, message = test_model_compatibility(model_id)
            
            if is_compatible:
                print(f"✅ {message}")
                print(f"🎯 Model '{model_id}' is now active!")
                return model_id
            else:
                print(f"❌ {message}")
                retry = input("Try a different model? (y/n): ").strip().lower()
                if retry != 'y':
                    return None
                print()
                continue
                
        except (ValueError, IndexError):
            print(f"❌ Please enter a number between 1 and {len(models)}")
            continue
        except Exception as e:
            print(f"❌ Error testing model: {e}")
            continue

if __name__ == "__main__":
    select_model()