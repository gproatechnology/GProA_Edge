import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test():
    with open("scratch/err_out.txt", "w") as f:
        try:
            from google.genai import types
            from app.core.config import gemini_client
            contents = [types.Content(role="user", parts=[types.Part.from_text(text="hola")])]
            config = types.GenerateContentConfig(
                system_instruction="You are a helpful assistant",
                temperature=0.7,
                max_output_tokens=800
            )
            response = await gemini_client.aio.models.generate_content(
                model="gemini-pro-latest",
                contents=contents,
                config=config
            )
            f.write("Response: " + response.text)
        except Exception as e:
            import traceback
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test())
