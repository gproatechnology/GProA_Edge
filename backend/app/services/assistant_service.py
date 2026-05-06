import json
import logging
from app.core.config import openai_client
from app.db.database import udb
from app.services.edge_rules import validate_project_wbs

logger = logging.getLogger(__name__)

async def get_assistant_response(project_id: str, user_message: str, history: list = None) -> str:
    """Generate a context-aware response for the EDGE project assistant."""
    
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
- Responde de forma profesional, clara y directa.
- Si el usuario pregunta por cumplimiento, menciona los documentos faltantes especificos.
- Usa terminologia tecnica de EDGE (EEM, WEM, MEM).
- Si no sabes algo, admítelo y sugiere como obtener la informacion.
- Eres parte de la plataforma GProA, no menciones que eres un modelo de lenguaje.
"""

    if not openai_client:
        return f"MODO DEMO: Hola! Estoy analizando el proyecto '{project['name']}'. Veo que tienes {len(files)} documentos procesados. ¿En qué puedo ayudarte?"

    # 3. Prepare messages for OpenAI
    messages = [{"role": "system", "content": context_prompt}]
    
    if history:
        for msg in history[-5:]: # Keep last 5 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": user_message})

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in assistant response: {e}")
        return "Hubo un error al conectar con el servicio de IA. Por favor, intenta de nuevo más tarde."
