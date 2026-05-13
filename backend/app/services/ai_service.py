import json
import logging
import os
from app.core.config import gemini_client, GEMINI_API_KEY
from app.services.edge_rules import EDGE_WBS
from app.db.database import udb

# Deterministic Parsers
from app.services.parsers.cad_parser import CADParser
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.excel_parser import ExcelParser
from app.services.parsers.docx_parser import DocxParser
from app.services.parsers.image_processor import ImageProcessor

cad_parser = CADParser()
pdf_parser = PDFParser()
excel_parser = ExcelParser()
docx_parser = DocxParser()
image_processor = ImageProcessor()

logger = logging.getLogger(__name__)

# In-memory job tracker for batch progress
processing_jobs = {}

# ── MOCK AI FUNCTIONS (Demo Mode) ───────────────────────────────────────

def classify_file_mock(content: str, filename: str = "") -> dict:
    """Return deterministic mock classification based on filename/content patterns."""
    text = (filename + " " + content).lower()
    
    # ENERGY - Lighting
    if any(k in text for k in ["lumin", "led", "lm", "luz", "iluminacion", "watt", "foco"]):
        return {"category_edge": "ENERGY", "measure_edge": "EEM22", "doc_type": "ficha_tecnica", "confidence": 0.99}
    
    # ENERGY - HVAC
    elif any(k in text for k in ["hvac", "aire", "acondicionado", "split", "vrf", "chiller", "refrigerante"]):
        return {"category_edge": "ENERGY", "measure_edge": "EEM09", "doc_type": "ficha_tecnica", "confidence": 0.98}
    
    # WATER
    elif any(k in text for k in ["agua", "grifo", "ducha", "inodoro", "wc", "sanitario", "riego", "pluvial"]):
        measure = "WEM01" if "grifo" in text or "ducha" in text else "WEM02" if "inodoro" in text else "WEM08"
        return {"category_edge": "WATER", "measure_edge": measure, "doc_type": "ficha_tecnica", "confidence": 0.97}
    
    # DESIGN / PLANS / IMAGES
    elif any(k in text for k in ["plano", "floor", "architectural", "arquitectonico", "dwg", "dxf", "pdf", "jpg", "png", "jpeg"]):
        doc_type = "plano" if any(k in text for k in ["dwg", "dxf", "pdf"]) else "fotografia"
        return {"category_edge": "DESIGN", "measure_edge": "DESIGN", "doc_type": doc_type, "confidence": 0.90}
    
    # MATERIALS
    elif any(k in text for k in ["concreto", "acero", "madera", "reciclado", "pintura", "voc", "fsc", "material"]):
        return {"category_edge": "MATERIALS", "measure_edge": "MEM01", "doc_type": "ficha_tecnica", "confidence": 0.90}
    
    # Default fallback
    return {"category_edge": "ENERGY", "measure_edge": "EEM01", "doc_type": "ficha_tecnica", "confidence": 0.50}

def extract_data_mock(content: str, measure: str = "") -> dict:
    """Extract mock technical data with realistic values for demo."""
    import random
    data = {
        "watts": None,
        "lumens": None,
        "tipo_equipo": "Equipo Generico",
        "marca": random.choice(["Eosis Tech", "GProA Solutions", "EcoFlow"]),
        "modelo": f"MOD-{random.randint(100,999)}X"
    }
    if measure in ["EEM22", "EEM23"]:
        data["watts"] = random.choice([9, 12, 18, 24])
        data["lumens"] = data["watts"] * 110 
        data["tipo_equipo"] = "Luminaria LED"
    return data

# ── AI Processing Functions ─────────────────────────────────────────────

async def classify_file(content: str, filename: str = "") -> dict:
    """Classify file using Gemini or mock."""
    if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
        return classify_file_mock(content, filename)
    
    try:
        from google.genai import types
        # Prompt mejorado para considerar medidas específicas de EDGE
        prompt = f"""Clasifica este archivo técnico de construcción para certificación EDGE.
        Nombre del archivo: {filename}
        
        Categorías EDGE: ENERGY, WATER, MATERIALS, DESIGN.
        Tipos de documento: ficha_tecnica, plano, memoria, factura, fotografia.
        
        Responde ÚNICAMENTE en JSON:
        {{
            "category_edge": "string",
            "measure_edge": "EEMXX/WEMXX/etc",
            "doc_type": "string",
            "confidence": 0.0-1.0
        }}
        """
        
        config = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json"
        )
        
        response = await gemini_client.aio.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt + "\n\nContenido parcial:\n" + content[:2000],
            config=config
        )
        
        return json.loads(response.text.strip())
    except Exception as e:
        logger.error(f"Gemini classify error: {e}")
        return classify_file_mock(content, filename)

async def extract_data(content: str, measure: str = "") -> dict:
    """Extract specialized data using AI based on the detected measure."""
    if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
        return extract_data_mock(content, measure)
    
    try:
        from app.services.edge_rules import get_rule
        rule = get_rule(measure)
        fields = rule.get("campos_extraccion", []) if rule else []
        
        prompt = f"""Extrae los siguientes parámetros técnicos del texto para la medida EDGE {measure}:
        Campos requeridos: {", ".join(fields)}
        
        Responde ÚNICAMENTE en JSON con los valores encontrados (usa null si no se encuentra).
        """
        
        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
        
        response = await gemini_client.aio.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt + "\n\nTexto:\n" + content[:4000],
            config=config
        )
        
        return json.loads(response.text.strip())
    except Exception as e:
        logger.error(f"Gemini extract error: {e}")
        return extract_data_mock(content, measure)

async def process_single_file_pipeline(file_doc: dict, job_id: str = None) -> dict:
    """Full processing pipeline for a single file."""
    content = file_doc.get("content_text", "")
    filename = file_doc.get("filename", "")
    file_id = file_doc["id"]
    file_path = file_doc.get("file_path")
    
    # Path resolution
    if not file_path:
        ext = filename.split('.')[-1].lower() if '.' in filename else ""
        id_path = os.path.join("uploads", f"{file_id}.{ext}")
        name_path = os.path.join("uploads", filename)
        file_path = id_path if os.path.exists(id_path) else name_path if os.path.exists(name_path) else None

    update = {}
    ext = filename.split('.')[-1].lower() if '.' in filename else ""

    try:
        # 1. DETERMINISTIC PARSING & IMAGE ANALYSIS
        det_data = None
        if file_path and os.path.exists(file_path):
            if ext in ['dxf', 'dwg']:
                det_data = cad_parser.parse(file_path)
            elif ext == 'pdf':
                det_data = pdf_parser.parse(file_path)
                # FALLBACK: Si el PDF no tiene texto (escaneado), usar Vision API
                text_len = det_data.get("text_summary", {}).get("total_chars", 0)
                if text_len < 50:
                    logger.info(f"PDF {filename} seems scanned (text len: {text_len}). Using Vision API.")
                    vision_data = await image_processor.process(file_path)
                    if vision_data:
                        # Fusionar datos de visión (especialmente parámetros extraídos)
                        if "extracted_parameters" in vision_data:
                            if "extracted_parameters" not in det_data: det_data["extracted_parameters"] = {}
                            det_data["extracted_parameters"].update(vision_data["extracted_parameters"])
                        if "areas" in vision_data:
                            det_data["areas"] = vision_data["areas"]
                        if "classification" in vision_data:
                            update.update(vision_data["classification"])
            elif ext in ['xlsx', 'xls', 'csv']:
                det_data = excel_parser.parse(file_path)
            elif ext == 'docx':
                det_data = docx_parser.parse(file_path)
            elif ext in ['jpg', 'jpeg', 'png']:
                # Las imágenes requieren análisis visual (IA)
                det_data = await image_processor.process(file_path)
                # Si la imagen ya fue clasificada por el procesador visual, usamos eso
                if "classification" in det_data:
                    classification = det_data["classification"]
                    update.update(classification)

        # 2. CLASSIFICATION (if not already done by image processor)
        if "category_edge" not in update:
            classification = await classify_file(content, filename)
            update.update({
                "category_edge": classification.get("category_edge"),
                "measure_edge": classification.get("measure_edge"),
                "doc_type": classification.get("doc_type"),
                "confidence": classification.get("confidence"),
            })

        # 3. DATA EXTRACTION
        measure = update.get("measure_edge", "")
        final_params = {}
        
        if det_data:
            # Error handling from parser
            if "error" in det_data:
                update["specialized_data"] = {
                    "tipo": "Error de Análisis",
                    "mensaje": det_data.get("message") or det_data["error"],
                    "status": "fail"
                }
            
            # Transfer areas (Geometric + Text)
            all_areas = det_data.get("areas", [])
            text_areas = det_data.get("text_summary", {}).get("detected_areas_from_text", [])
            if text_areas:
                # Evitar duplicados simples por valor
                existing_vals = [a["area_m2"] for a in all_areas]
                for ta in text_areas:
                    if ta["area_m2"] not in existing_vals:
                        all_areas.append(ta)
            
            if all_areas:
                update["areas"] = all_areas
            
            # Transfer technical parameters from deterministic parser if any
            if "extracted_parameters" in det_data:
                final_params.update(det_data["extracted_parameters"])

        # AI Extraction (from content_text or deterministic text)
        # Solo si no es imagen (las imágenes ya fueron procesadas arriba)
        if ext not in ['jpg', 'jpeg', 'png']:
            ai_text = det_data.get("content_text") if det_data and det_data.get("content_text") else content
            if ai_text:
                ai_params = await extract_data(ai_text, measure)
                final_params.update(ai_params)

        # Update file document with extracted fields
        if final_params:
            update["watts"] = final_params.get("watts")
            update["lumens"] = final_params.get("lumens")
            update["marca"] = final_params.get("marca")
            update["modelo"] = final_params.get("modelo")
            update["tipo_equipo"] = final_params.get("tipo_equipo")
            update["cost"] = final_params.get("costo") or final_params.get("cost")
            update["consumption_kwh"] = final_params.get("consumo_kwh") or final_params.get("consumption_kwh")
            
        # Build specialized data for CAD/PDF (Geometry info)
        if det_data and ("geometry" in det_data or "entities" in det_data):
                geom_info = det_data.get("geometry", [])
                total_shapes = sum(g.get("vector_shapes", 0) for g in geom_info) if isinstance(geom_info, list) else 0
                detected_areas = det_data.get("areas", [])
                text_areas = det_data.get("text_summary", {}).get("detected_areas_from_text", [])
                
                # Si logramos extraer algo real, sobreescribimos el specialized_data
                update["specialized_data"] = {
                    "tipo": "Plano Técnico / Ingeniería",
                    "total_formas": total_shapes or det_data.get("entities", {}).get("polylines", 0),
                    "areas_detectadas": detected_areas,
                    "areas_texto": text_areas,
                    "mensaje": f"Análisis técnico completado con {len(detected_areas) + len(text_areas)} áreas detectadas."
                }
                update["doc_type"] = "plano"
                
                # Si el análisis fue vacío pero sin error, avisar al usuario
                if not detected_areas and not text_areas:
                    update["specialized_data"]["mensaje"] = "El plano no contiene áreas cerradas o texto de medidas reconocible."
                    update["specialized_data"]["status"] = "warning"

        # 4. FALLBACK MOCK (ONLY if not already set by parsers)
        if "specialized_data" not in update and not gemini_client:
            if measure == "EEM22":
                update["specialized_data"] = {"total_watts": 10, "total_lumens": 1100, "eficacia": 110}
            elif measure == "DESIGN":
                update["specialized_data"] = {"tipo": "Análisis de Diseño", "mensaje": "Datos de diseño general procesados."}

        update["status"] = "processed"
        await udb.files_update_one({"id": file_id}, {"$set": update})
        return {"file_id": file_id, "status": "processed", "deterministic": bool(det_data)}

    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")
        await udb.files_update_one({"id": file_id}, {"$set": {"status": "error", "error_msg": str(e)}})
        return {"file_id": file_id, "status": "error", "error": str(e)}
