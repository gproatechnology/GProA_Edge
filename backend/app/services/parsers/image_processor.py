import os
import json
import logging
import fitz # PyMuPDF para convertir PDF a imagen
from typing import Dict, Any, List
from google.genai import types
from app.core.config import gemini_client, GEMINI_API_KEY

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Procesador de imágenes técnicas mediante IA (Gemini Multimodal)."""

    async def process(self, file_path: str, hint_measure: str = "") -> Dict[str, Any]:
        """Procesa una imagen o PDF (como imagen) usando Gemini API."""
        if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
            logger.warning("Vision API skip: No API Key or Demo Mode")
            return {"error": "No API Key for Vision"}

        try:
            ext = file_path.split('.')[-1].lower()
            temp_image_path = None

            if ext == 'pdf':
                # Convertir primera página de PDF a imagen temporal para análisis visual
                logger.info(f"Converting PDF {file_path} to image for Vision analysis")
                doc = fitz.open(file_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom 2x para mejor resolución
                temp_image_path = file_path + ".temp.png"
                pix.save(temp_image_path)
                process_path = temp_image_path
                doc.close()
            else:
                process_path = file_path

            with open(process_path, "rb") as image_file:
                image_bytes = image_file.read()

            # Eliminar temporal si existe
            if temp_image_path and os.path.exists(temp_image_path):
                os.remove(temp_image_path)

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

            image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png')
            
            config = types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )

            response = await gemini_client.aio.models.generate_content(
                model="gemini-1.5-pro",
                contents=[prompt, image_part],
                config=config
            )

            result_text = response.text.strip()
            return json.loads(result_text)

        except Exception as e:
            logger.error(f"Error procesando imagen {file_path} con Gemini: {e}")
            return {"error": str(e)}
