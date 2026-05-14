import json
import logging
from app.core.config import gemini_client, GEMINI_API_KEY
from app.db.database import udb
from app.services.edge_rules import validate_project_wbs

logger = logging.getLogger(__name__)

async def get_assistant_response(project_id: str, user_message: str, history: list = None) -> str:
    """Generate a context-aware response for the EDGE project assistant using Gemini."""
    
    # 1. Fetch Project Context
    project = await udb.projects_find_one({"id": project_id})
    if not project:
        return "Lo siento, no pude encontrar la información de este proyecto."

    files = await udb.files_find({"project_id": project_id, "status": "processed"}, {"content_text": 0})
    validation = validate_project_wbs(files)
    
    # 2. Build a summary of the project status for the AI
    measures_summary = []
    for m, data in validation.items():
        status = "COMPLETO" if data["estado"] == "completo" else f"INCOMPLETO (faltan: {', '.join(data['faltantes'])})"
        measures_summary.append(f"- {m} ({data['nombre']}): {status}")

    context_prompt = f"""Eres el Asistente Experto de GProA EDGE. 
Estas ayudando en el proyecto: "{project['name']}" (Tipologia: {project['typology']}).

Estado actual del proyecto:
{chr(10).join(measures_summary) if measures_summary else "No hay documentos procesados aun."}

Instrucciones:
- Eres un asistente técnico estricto.
- Tus respuestas NUNCA deben exceder las 2 oraciones. Ve directo al grano.
- Si el usuario pregunta por cumplimiento, menciona los documentos faltantes especificos de forma ultra concisa.
- Usa terminologia tecnica de EDGE (EEM, WEM, MEM).
- Si no sabes algo, admítelo en una sola frase.
- No menciones que eres un modelo de lenguaje ni saludes con cortesías innecesarias.
"""

    if not gemini_client or GEMINI_API_KEY == "sk-your-key-here":
        return f"MODO DEMO: Hola! Estoy analizando el proyecto '{project['name']}'. Veo que tienes {len(files)} documentos procesados. ¿En qué puedo ayudarte?"

    try:
        from google.genai import types
        
        # 3. Prepare messages for Gemini
        contents = []
        if history:
            for msg in history[-5:]: # Keep last 5 messages for context
                role = "user" if msg["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
                
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        config = types.GenerateContentConfig(
            system_instruction=context_prompt,
            temperature=0.7,
            max_output_tokens=4096
        )

        response = await gemini_client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents=contents,
            config=config
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in assistant response: {e}")
        return "Hubo un error al conectar con el servicio de Inteligencia Artificial (Gemini). Por favor, intenta de nuevo más tarde."
