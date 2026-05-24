import httpx
import json
import logging
import re
from typing import Dict, Any, Optional
from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2", timeout: float = 60.0):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str) -> str:
        """
        Generate a response from Ollama.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
            except httpx.RequestError as e:
                logger.error(f"Error communicating with Ollama: {e}")
                raise
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Error parsing Ollama response: {e}")
                raise

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON response from Ollama.
        """
        response_text = await self.generate(prompt)
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Ollama response: {e}")
                logger.error(f"Response text: {response_text}")
                # Return a default response to avoid breaking the flow
                return {"error": "Failed to parse JSON", "raw_response": response_text}
        else:
            logger.warning(f"No JSON found in Ollama response: {response_text}")
            # Return a default response to avoid breaking the flow
            return {"error": "No JSON found in response", "raw_response": response_text}