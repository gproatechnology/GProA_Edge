import httpx
import asyncio

async def test_ollama():
    print("Testing Ollama connection...")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                'http://localhost:11434/api/generate',
                json={'model': 'llama3.2', 'prompt': 'Hello', 'stream': False}
            )
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Response: {result.get('response', '')[:100]}...")
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama())
    print("Success!" if success else "Failed!")