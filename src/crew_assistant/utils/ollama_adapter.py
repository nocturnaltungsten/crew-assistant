# Ollama API Adapter for CrewAI
# Converts OpenAI format calls to Ollama format

import os
from typing import Any

import requests


class OllamaAdapter:
    """Adapter to make Ollama API work with CrewAI's OpenAI format expectations."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def chat_completion(self, **kwargs) -> dict[str, Any]:
        """Convert OpenAI chat completion format to Ollama format."""

        # Extract OpenAI format parameters
        model = kwargs.get("model", "tinyllama:latest")
        messages = kwargs.get("messages", [])
        max_tokens = kwargs.get("max_tokens", 100)
        temperature = kwargs.get("temperature", 0.7)

        # Convert to Ollama format
        ollama_payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }

        try:
            response = requests.post(f"{self.base_url}/api/chat", json=ollama_payload, timeout=30)
            response.raise_for_status()

            ollama_response = response.json()

            # Convert Ollama response to OpenAI format
            openai_response = {
                "id": f"chatcmpl-{hash(str(ollama_response))}",
                "object": "chat.completion",
                "created": int(response.headers.get("date", "0")),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ollama_response.get("message", {}).get("content", ""),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,  # Ollama doesn't provide token counts
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

            return openai_response

        except Exception as e:
            raise Exception(f"Ollama API error: {e}")


def setup_ollama_for_crewai():
    """Set up environment to use Ollama with CrewAI."""
    provider = os.getenv("AI_PROVIDER", "").lower()

    if provider == "ollama":
        # Modify the OpenAI client to use our adapter

        import openai

        adapter = OllamaAdapter(os.getenv("OPENAI_API_BASE", "http://localhost:11434"))

        # Patch the chat completion method
        original_create = openai.ChatCompletion.create

        def ollama_create(*args, **kwargs):
            return adapter.chat_completion(**kwargs)

        openai.ChatCompletion.create = ollama_create

        print("✅ Ollama adapter configured for CrewAI")
        return True

    return False


if __name__ == "__main__":
    # Test the adapter
    adapter = OllamaAdapter()

    try:
        response = adapter.chat_completion(
            model="tinyllama:latest",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10,
        )

        print("✅ Ollama adapter test successful!")
        print(f"Response: {response['choices'][0]['message']['content']}")

    except Exception as e:
        print(f"❌ Ollama adapter test failed: {e}")
