from pydantic import BaseModel
from typing import Dict, Any, Optional
import hashlib
import time

class LLMResult(BaseModel):
    provider: str
    model: str
    prompt_hash: str
    response: Dict[str, Any]
    confidence: float
    latency_ms: int

    @classmethod
    def create(
        cls,
        provider: str,
        model: str,
        prompt: str,
        response: Dict[str, Any],
        confidence: float,
        latency_ms: Optional[int] = None
    ):
        if latency_ms is None:
            latency_ms = int(time.time() * 1000)  # placeholder, actual latency should be measured
        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        return cls(
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            response=response,
            confidence=confidence,
            latency_ms=latency_ms
        )