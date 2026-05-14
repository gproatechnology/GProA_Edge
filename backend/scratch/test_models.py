import asyncio
import os
import sys

# Asegurar que el path sea el correcto para poder importar app.core.config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import gemini_client

async def test_models():
    print("Fetching available models...")
    try:
        # The new genai SDK might use client.models.list()
        from google.genai import types
        # Some SDKs don't have list models or it returns a generator
        models = []
        for m in gemini_client.models.list():
            models.append(m.name)
        print("Available models:")
        for m in models:
            print(m)
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
