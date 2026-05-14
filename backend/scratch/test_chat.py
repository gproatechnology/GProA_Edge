import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.assistant_service import get_assistant_response

async def test():
    try:
        # Use a dummy project id or the one from the image: ceaebf11-b317-4d41-86cc-d64edcd1fbe3
        res = await get_assistant_response("ceaebf11-b317-4d41-86cc-d64edcd1fbe3", "hola")
        print("Response:", res)
    except Exception as e:
        print("Exception caught in script:", e)

if __name__ == "__main__":
    asyncio.run(test())
