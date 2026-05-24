import asyncio
import time
from app.services.llm.ollama_provider import OllamaProvider

async def time_ollama_call():
    provider = OllamaProvider(timeout=300.0)  # 5 minute timeout
    
    # Test classification prompt
    test_text = "This is a technical specification for an LED lighting fixture with 18 watts and 2000 lumens."
    prompt = f"""
    Return ONLY valid JSON.

    Schema:
    {{
      "category_edge": "string (one of: ENERGY, WATER, MATERIALS, DESIGN)",
      "measure_edge": "string (e.g., EEM22, WEM01, etc.)",
      "doc_type": "string (e.g., ficha_tecnica, plano, etc.)",
      "confidence": 0.0-1.0
    }}

    Input text:
    {test_text}
    """
    
    print(f"Prompt length: {len(prompt)} characters")
    print("Starting classification...")
    
    start = time.time()
    try:
        result = await provider.generate_json(prompt)
        end = time.time()
        print(f"Classification completed in {end - start:.2f} seconds")
        print(f"Result: {result}")
        return True
    except Exception as e:
        end = time.time()
        print(f"Classification failed after {end - start:.2f} seconds: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(time_ollama_call())
    print("Success!" if success else "Failed!")