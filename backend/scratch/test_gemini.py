import asyncio
import os
import sys

# Asegurar que el path sea el correcto para poder importar app.core.config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import gemini_client, is_dummy_key, DEMO_MODE, GEMINI_API_KEY

async def test_gemini():
    print(f"Testing Gemini Configuration...")
    print(f"API Key Starts With: {GEMINI_API_KEY[:6] if GEMINI_API_KEY else 'None'}")
    print(f"is_dummy_key: {is_dummy_key}, DEMO_MODE: {DEMO_MODE}")

    if not gemini_client:
        print("\nFAIL: Gemini client is NOT initialized.")
        return
        
    print("\nSUCCESS: Gemini client is initialized. Attempting a test prompt to Google servers...")
    
    try:
        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=50
        )
        response = await gemini_client.aio.models.generate_content(
            model="gemini-pro-latest",
            contents="Responde únicamente con la palabra: CONECTADO",
            config=config
        )
        print(f"\nAPI Response: {response.text.strip()}")
        if "CONECTADO" in response.text.upper():
            print("\nSTATUS: 100% OPERATIONAL - API is working perfectly.")
        else:
            print("\nSTATUS: Unexpected response, but API connection succeeded.")
    except Exception as e:
        print(f"\nERROR calling Gemini API: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
