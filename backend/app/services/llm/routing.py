import logging
from enum import Enum
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

class TaskType(Enum):
    CLASSIFICATION = "classification"
    SUMMARY = "summary"
    RELATIONSHIP = "relationship"
    MULTIMODAL = "multimodal"

class FallbackProvider:
    """
    A provider that tries the primary provider first, and falls back to the secondary
    if the primary raises an exception.
    """
    def __init__(self, primary, secondary, primary_name: str, secondary_name: str):
        self.primary = primary
        self.secondary = secondary
        self.primary_name = primary_name
        self.secondary_name = secondary_name

    async def generate(self, prompt: str) -> str:
        try:
            return await self.primary.generate(prompt)
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_name} failed for generate, falling back to {self.secondary_name}: {e}")
            return await self.secondary.generate(prompt)

    async def generate_json(self, prompt: str) -> dict:
        try:
            return await self.primary.generate_json(prompt)
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_name} failed for generate_json, falling back to {self.secondary_name}: {e}")
            return await self.secondary.generate_json(prompt)

    async def classify(self, text: str):
        try:
            return await self.primary.classify(text)
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_name} failed for classify, falling back to {self.secondary_name}: {e}")
            return await self.secondary.classify(text)

    async def summarize(self, text: str):
        try:
            return await self.primary.summarize(text)
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_name} failed for summarize, falling back to {self.secondary_name}: {e}")
            return await self.secondary.summarize(text)

    async def infer_relationship(self, context: dict):
        try:
            return await self.primary.infer_relationship(context)
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_name} failed for infer_relationship, falling back to {self.secondary_name}: {e}")
            return await self.secondary.infer_relationship(context)

class LLMRouter:
    def __init__(self):
        self.gemini_provider = GeminiProvider()

    def route(self, task_type: TaskType):
        """
        Route all tasks to Gemini only (no Ollama fallback).
        """
        return self.gemini_provider