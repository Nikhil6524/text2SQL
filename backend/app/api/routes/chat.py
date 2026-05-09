from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, username: str = Depends(get_current_user)) -> ChatResponse:
    _ = username
    result = chat_service.process(message=payload.message, history=payload.history)
    return ChatResponse(**result)
