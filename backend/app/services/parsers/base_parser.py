from abc import ABC, abstractmethod
from typing import Dict, Any, TypedDict


class ParserResult(TypedDict, total=False):
    format: str
    error: str
    content_text: str


class BaseParser(ABC):
    """Clase base para todos los parsers determinísticos."""
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Extrae datos estructurados del archivo."""
        pass

    @abstractmethod
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrae metadatos básicos (capas, autores, fechas)."""
        pass
