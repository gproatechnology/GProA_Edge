import base64
import logging
import json
from typing import Dict, Any
from app.core.config import openai_client, OPENAI_API_KEY

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Procesador de imágenes técnicas mediante IA (OpenAI Vision)."""

    async def process(self, file_path: str, hint_measure: str = "") -> Dict[str, Any]:
        """Analiza una imagen y extrae parámetros técnicos."""
        if not openai_client or OPENAI_API_KEY == "sk-your-key-here":
            return {
                "error": "OpenAI API Key not configured",
                "status": "mock_required"
            }

        try:
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = f"""Analiza esta imagen técnica para certificación EDGE (Medida: {hint_measure}).
            Extrae toda la información técnica relevante (Watts, Lumens, Eficiencia, Marca, Modelo, Flujo, etc.).
            Si es un plano, identifica áreas mencionadas.
            Responde ÚNICAMENTE en formato JSON con esta estructura:
            {{
                "classification": {{
                    "category_edge": "ENERGY/WATER/MATERIALS/DESIGN",
                    "measure_edge": "EEMXX/WEMXX/etc",
                    "doc_type": "ficha_tecnica/fotografia/plano",
                    "confidence": 0.0-1.0
                }},
                "extracted_parameters": {{
                    "watts": null,
                    "lumens": null,
                    "marca": "string",
                    "modelo": "string",
                    "flujo_lpm": null
                }},
                "detected_text": "Resumen del texto detectado",
                "message": "Descripción de lo encontrado"
            }}"""

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ],
                    }
                ],
                max_tokens=1000,
            )

            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            return json.loads(result_text)

        except Exception as e:
            logger.error(f"Error procesando imagen {file_path}: {e}")
            return {"error": str(e)}
