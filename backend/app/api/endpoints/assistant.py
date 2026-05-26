from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.assistant_service import get_assistant_response

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@router.post("/projects/{project_id}/chat")
@limiter.limit("30/minute")  # Assistant endpoint - higher cost
async def project_chat(request: Request, project_id: str, chat_request: ChatRequest):
    """Chat with the project assistant."""
    try:
        response = await get_assistant_response(
            project_id=project_id,
            user_message=chat_request.message,
            history=[{"role": m.role, "content": m.content} for m in chat_request.history] if chat_request.history else []
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
