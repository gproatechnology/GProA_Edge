import httpx
import asyncio
import time

async def test_ollama():
    print("Testing Ollama connection...")
    start = time.time()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://localhost:11434/api/generate',
                json={'model': 'llama3.2', 'prompt': 'Hello', 'stream': False},
                timeout=30.0
            )
            result = response.json()
            elapsed = time.time() - start
            print(f"Response received in {elapsed:.2f}s: {result.get('response', '')[:100]}...")
            return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"Error after {elapsed:.2f}s: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama())
    print("Test passed!" if success else "Test failed!")