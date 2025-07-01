# Provider Selection Utility
# Supports LM Studio and Ollama backends

import os
from enum import Enum

import requests


class Provider(Enum):
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"


# Provider configurations
PROVIDER_CONFIGS = {
    Provider.LM_STUDIO: {
        "name": "LM Studio",
        "default_base": "http://localhost:1234/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "description": "Local LM Studio server with OpenAI-compatible API",
    },
    Provider.OLLAMA: {
        "name": "Ollama",
        "default_base": "http://localhost:11434",
        "models_endpoint": "/api/tags",
        "chat_endpoint": "/api/chat",
        "description": "Local Ollama server with native API",
    },
}

# Known compatible model patterns
COMPATIBLE_PATTERNS = [
    "instruct",
    "chat",
    "conversational",
    "dialog",
    "phi-3",
    "llama-3",
    "gemma",
    "mistral",
    "qwen",
]

INCOMPATIBLE_PATTERNS = ["base", "foundation", "embedding", "code-only"]


def select_provider() -> Provider | None:
    """Interactive provider selection."""
    print("\n🔧 Select AI Provider:")
    print("─" * 40)

    for i, provider in enumerate(Provider):
        config = PROVIDER_CONFIGS[provider]
        print(f"{i + 1}. {config['name']}")
        print(f"   📍 {config['default_base']}")
        print(f"   📝 {config['description']}")
        print()

    while True:
        choice = input("Select provider (1-2) or 'q' to quit: ").strip()

        if choice.lower() == "q":
            return None

        if not choice.isdigit():
            print("❌ Please enter a valid number or 'q' to quit")
            continue

        try:
            provider_index = int(choice) - 1
            providers = list(Provider)

            if provider_index < 0 or provider_index >= len(providers):
                print(f"❌ Please enter a number between 1 and {len(providers)}")
                continue

            selected_provider = providers[provider_index]
            print(f"✅ Selected: {PROVIDER_CONFIGS[selected_provider]['name']}")
            return selected_provider

        except (ValueError, IndexError):
            print(f"❌ Please enter a number between 1 and {len(providers)}")
            continue


def get_available_models(provider: Provider, base_url: str | None = None) -> list[dict]:
    """Get available models from the specified provider."""
    config = PROVIDER_CONFIGS[provider]
    api_base = (base_url or config["default_base"]).rstrip("/")
    models_endpoint = f"{api_base}{config['models_endpoint']}"

    try:
        response = requests.get(models_endpoint, timeout=10)
        response.raise_for_status()

        if provider == Provider.LM_STUDIO:
            # LM Studio uses OpenAI format
            models_data = response.json().get("data", [])
            return [
                {"id": model.get("id", "unknown"), "provider": provider.value}
                for model in models_data
            ]

        elif provider == Provider.OLLAMA:
            # Ollama uses different format
            models_data = response.json().get("models", [])
            return [
                {"id": model.get("name", "unknown"), "provider": provider.value}
                for model in models_data
            ]

    except Exception as e:
        print(f"❌ Could not fetch models from {config['name']}: {e}")
        return []


def categorize_model_compatibility(model_id: str) -> tuple[str, str]:
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


def test_model_compatibility(
    provider: Provider, model_id: str, base_url: str | None = None
) -> tuple[bool, str]:
    """Test if a model supports the chat completion format."""
    config = PROVIDER_CONFIGS[provider]
    api_base = (base_url or config["default_base"]).rstrip("/")
    chat_endpoint = f"{api_base}{config['chat_endpoint']}"

    try:
        if provider == Provider.LM_STUDIO:
            # LM Studio uses OpenAI format
            test_payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1,
            }
            headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'not-needed')}"}

        elif provider == Provider.OLLAMA:
            # Ollama uses different format
            test_payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False,
            }
            headers = {"Content-Type": "application/json"}

        response = requests.post(chat_endpoint, json=test_payload, headers=headers, timeout=10)

        if response.status_code == 200:
            return True, f"Model '{model_id}' is compatible with CrewAI"
        elif response.status_code == 400:
            return False, f"Model '{model_id}' has incompatible format"
        elif response.status_code == 404:
            return False, f"Model '{model_id}' not found - check if it's loaded"
        else:
            return False, f"Model '{model_id}' test failed: {response.status_code}"

    except requests.RequestException as e:
        return False, f"Could not connect to {config['name']}: {e}"
    except Exception as e:
        return False, f"Model compatibility test failed: {e}"


def select_model_from_provider(
    provider: Provider, base_url: str | None = None
) -> tuple[str, Provider] | None:
    """Select a model from the specified provider."""
    config = PROVIDER_CONFIGS[provider]
    print(f"\n🔍 Fetching available models from {config['name']}...")

    models = get_available_models(provider, base_url)

    if not models:
        print(f"⚠️ No models found. Make sure {config['name']} is running and has models loaded.")
        return None

    print(f"\n🧠 Available Models from {config['name']}:")
    print("─" * 80)

    enhanced_models = []
    for model in models:
        model_id = model["id"]
        status, note = categorize_model_compatibility(model_id)
        enhanced_models.append(
            {"id": model_id, "status": status, "note": note, "provider": provider}
        )

    for i, model in enumerate(enhanced_models):
        print(f"{i + 1:2d}. {model['status']} {model['id']}")
        print(f"    📝 {model['note']}")
        print()

    while True:
        choice = input("Select a model by number (or 'q' to quit): ").strip()

        if choice.lower() == "q":
            return None

        if not choice.isdigit():
            print("❌ Please enter a valid number or 'q' to quit")
            continue

        try:
            model_index = int(choice) - 1
            if model_index < 0 or model_index >= len(enhanced_models):
                print(f"❌ Please enter a number between 1 and {len(enhanced_models)}")
                continue

            selected_model = enhanced_models[model_index]
            model_id = selected_model["id"]

            print(f"\n🧪 Testing model '{model_id}'...")

            # Test the model
            is_compatible, message = test_model_compatibility(provider, model_id, base_url)

            if is_compatible:
                print(f"✅ {message}")
                print(f"🎯 Model '{model_id}' is now active!")
                return model_id, provider
            else:
                print(f"❌ {message}")
                retry = input("Try a different model? (y/n): ").strip().lower()
                if retry != "y":
                    return None
                print()
                continue

        except (ValueError, IndexError):
            print(f"❌ Please enter a number between 1 and {len(enhanced_models)}")
            continue
        except Exception as e:
            print(f"❌ Error testing model: {e}")
            continue


def interactive_setup() -> tuple[str, Provider, str] | None:
    """Interactive setup flow for provider and model selection."""
    print("🚀 Crew Assistant - Provider & Model Setup")
    print("=" * 50)

    # Step 1: Select provider
    provider = select_provider()
    if not provider:
        print("👋 Setup cancelled.")
        return None

    # Step 2: Select model from provider
    result = select_model_from_provider(provider)
    if not result:
        print("👋 Setup cancelled.")
        return None

    model_id, selected_provider = result

    # Step 3: Set environment variables
    config = PROVIDER_CONFIGS[provider]
    api_base = config["default_base"]

    print("\n🎉 Setup complete!")
    print(f"Provider: {config['name']}")
    print(f"Model: {model_id}")
    print(f"API Base: {api_base}")

    return model_id, provider, api_base


if __name__ == "__main__":
    result = interactive_setup()
    if result:
        model_id, provider, api_base = result
        print("\nTo use this configuration, set:")
        print(f"export OPENAI_API_MODEL='{model_id}'")
        print(f"export OPENAI_API_BASE='{api_base}'")
        print(f"export AI_PROVIDER='{provider.value}'")
