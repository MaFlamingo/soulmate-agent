"""Chat & Conversation API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    SendMessageRequest, SendMessageResponse,
    ConversationResponse, ConversationListItem,
)
from app.services.chat_service import ChatService
from app.agents.profile_mining import ProfileMiningAgent

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    body: ChatSessionCreate = ChatSessionCreate(),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Create a new conversation session."""
    result = chat_service.create_session(user_id=body.user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ChatSessionResponse(**result)


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: int,
    body: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Send a message and get agent reply."""
    result = await chat_service.process_message(session_id, body.content)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return SendMessageResponse(**result)


@router.get("/sessions/{session_id}", response_model=ConversationResponse)
async def get_session(
    session_id: int,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get full conversation history."""
    result = chat_service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(**result)


@router.get("/sessions")
async def list_sessions(
    user_id: int = 1,
    page: int = 1,
    limit: int = 20,
    chat_service: ChatService = Depends(get_chat_service),
):
    """List user's conversation sessions."""
    return chat_service.list_sessions(user_id, page=page, limit=limit)
