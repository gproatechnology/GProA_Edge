from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.assistant_service import get_assistant_response

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@router.post("/projects/{project_id}/chat")
async def project_chat(project_id: str, request: ChatRequest):
    """Chat with the project assistant."""
    try:
        response = await get_assistant_response(
            project_id=project_id,
            user_message=request.message,
            history=[{"role": m.role, "content": m.content} for m in request.history] if request.history else []
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
