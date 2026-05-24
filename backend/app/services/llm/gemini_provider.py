import json
import logging
import re
from typing import Dict, Any
from google.genai import types
from app.core.config import gemini_client, GEMINI_API_KEY
from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    def __init__(self, model: str = "gemini-flash-latest"):
        self.model = model

    async def generate(self, prompt: str) -> str:
        """
        Generate a response from Gemini.
        """
        if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
            raise Exception("Gemini client not configured")

        try:
            config = types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="text/plain"
            )
            
            response = await gemini_client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error communicating with Gemini: {e}")
            raise

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON response from Gemini.
        """
        response_text = await self.generate(prompt)
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                logger.error(f"Response text: {response_text}")
                # Return a default response to avoid breaking the flow
                return {"error": "Failed to parse JSON", "raw_response": response_text}
        else:
            logger.warning(f"No JSON found in Gemini response: {response_text}")
            # Return a default response to avoid breaking the flow
            return {"error": "No JSON found in response", "raw_response": response_text}