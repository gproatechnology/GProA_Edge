from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        pass

    async def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify text using the LLM. Returns a dictionary with classification results.
        Expected format: {"category_edge": str, "measure_edge": str, "doc_type": str, "confidence": float}
        """
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
        {text}
        """
        return await self.generate_json(prompt)

    async def summarize(self, text: str) -> str:
        """
        Summarize text using the LLM.
        """
        prompt = f"""
        Provide a concise technical summary of the following text:

        {text}

        Summary:
        """
        return await self.generate(prompt)

    async def infer_relationship(self, context: dict) -> dict:
        """
        Infer relationships from context using the LLM.
        Expected to return a dictionary with relationship information.
        """
        import json
        prompt = f"""
        Based on the following context, infer any technical or semantic relationships.
        Return ONLY valid JSON with the inferred relationships.

        Context:
        {json.dumps(context, indent=2)}

        Example output format:
        {{
          "related_entities": ["entity1", "entity2"],
          "relationship_type": "string",
          "confidence": 0.0-1.0
        }}
        """
        return await self.generate_json(prompt)