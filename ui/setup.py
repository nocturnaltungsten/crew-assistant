# Enhanced Provider Setup
# Updated for new modular architecture

import os

from providers import get_provider, list_available_providers


def interactive_provider_setup() -> tuple[str, str, str] | None:
    """Interactive setup for provider and model selection."""
    print("🚀 Enhanced Crew Assistant - Provider & Model Setup")
    print("=" * 60)

    # Step 1: Select provider
    provider_name = select_provider()
    if not provider_name:
        print("👋 Setup cancelled.")
        return None

    # Step 2: Select model from provider
    result = select_model_from_provider(provider_name)
    if not result:
        print("👋 Setup cancelled.")
        return None

    model_id, provider_name = result

    # Step 3: Get provider config
    provider_config = _get_provider_config(provider_name)
    api_base = provider_config.get("base_url", "Unknown")

    print("\n🎉 Setup complete!")
    print(f"Provider: {provider_name.title()}")
    print(f"Model: {model_id}")
    print(f"API Base: {api_base}")

    return model_id, provider_name, api_base


def select_provider() -> str | None:
    """Interactive provider selection."""
    print("\n🔧 Select AI Provider:")
    print("─" * 40)

    providers = list_available_providers()
    available_providers = [p for p in providers if p["status"] == "online"]

    if not available_providers:
        print("❌ No providers are currently online.")
        print("Please start LM Studio or Ollama and try again.")
        return None

    for i, provider in enumerate(available_providers):
        status_emoji = "🟢" if provider["status"] == "online" else "🔴"
        print(f"{i+1}. {status_emoji} {provider['display_name']}")
        print(f"   📍 {provider['base_url']}")
        print(f"   📝 {provider['description']}")
        print()

    while True:
        choice = input(f"Select provider (1-{len(available_providers)}) or 'q' to quit: ").strip()

        if choice.lower() == 'q':
            return None

        if not choice.isdigit():
            print("❌ Please enter a valid number or 'q' to quit")
            continue

        try:
            provider_index = int(choice) - 1

            if provider_index < 0 or provider_index >= len(available_providers):
                print(f"❌ Please enter a number between 1 and {len(available_providers)}")
                continue

            selected_provider = available_providers[provider_index]
            provider_name = selected_provider["name"]
            print(f"✅ Selected: {selected_provider['display_name']}")
            return provider_name

        except (ValueError, IndexError):
            print(f"❌ Please enter a number between 1 and {len(available_providers)}")
            continue


def select_model_from_provider(provider_name: str) -> tuple[str, str] | None:
    """Select a model from the specified provider."""
    print(f"\n🔍 Fetching available models from {provider_name.title()}...")

    # Get provider instance
    provider_config = _get_provider_config(provider_name)
    provider = get_provider(provider_name, provider_config)

    try:
        models = provider.list_models()
    except Exception as e:
        print(f"❌ Failed to fetch models: {e}")
        return None

    if not models:
        print(f"⚠️ No models found. Make sure {provider_name.title()} has models loaded.")
        return None

    print(f"\n🧠 Available Models from {provider_name.title()}:")
    print("─" * 80)

    for i, model in enumerate(models):
        status_emoji = {"compatible": "✅", "incompatible": "❌", "unknown": "❓"}[model.compatibility]
        print(f"{i+1:2d}. {status_emoji} {model.compatibility.title()} {model.id}")
        print(f"    📝 {model.description}")
        if model.size:
            print(f"    💾 {model.size}")
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
            model_id = selected_model.id

            print(f"\n🧪 Testing model '{model_id}'...")

            # Test the model
            is_compatible, message = provider.test_model(model_id)

            if is_compatible:
                print(f"✅ {message}")
                print(f"🎯 Model '{model_id}' is now active!")
                return model_id, provider_name
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


def _get_provider_config(provider_name: str) -> dict:
    """Get provider configuration."""
    if provider_name == "ollama":
        return {
            "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:11434").replace("/v1", ""),
            "timeout": 60
        }
    elif provider_name == "lmstudio":
        return {
            "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1"),
            "api_key": os.getenv("OPENAI_API_KEY", "not-needed-for-local"),
            "timeout": 60
        }
    else:
        return {}
