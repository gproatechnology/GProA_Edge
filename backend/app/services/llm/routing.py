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

    # If there are other methods like generate, generate_json, they can be added similarly.
    # For now we only need the three main methods used in BaseLLMProvider.

class LLMRouter:
    def __init__(self):
        self.ollama_provider = OllamaProvider()
        self.gemini_provider = GeminiProvider()

    def route(self, task_type: TaskType):
        """
        Route the task to the appropriate provider with fallback.
        
        NOTA: Después de pruebas (24 Mayo 2026), Ollama (llama3.2) es muy lento (~4.5 min)
        y no devuelve JSON estructurado correctamente. Gemini es más rápido y confiable.
        
        Por defecto: Gemini primary, Ollama fallback.
        """
        # Todas las tareas usan Gemini como primary, Ollama como fallback
        return FallbackProvider(
            primary=self.gemini_provider,
            secondary=self.ollama_provider,
            primary_name="Gemini",
            secondary_name="Ollama"
        )