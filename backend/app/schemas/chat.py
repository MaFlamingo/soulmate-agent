"""Chat & conversation Pydantic schemas."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    """Request to create a new conversation session."""
    user_id: Optional[int] = Field(default=None, description="Existing user ID (optional, creates anonymous session if none)")


class ChatSessionResponse(BaseModel):
    """Response after creating a session."""
    session_id: int
    greeting_message: str
    phase: str = "interest_gathering"
    user_id: Optional[int] = None


class SendMessageRequest(BaseModel):
    """Send a message in a conversation."""
    content: str = Field(..., min_length=1, max_length=4096, description="User's message text")


class ExtractedTag(BaseModel):
    """A single tag extracted from conversation."""
    type: str  # "interest", "personality", "social_need"
    category: Optional[str] = None
    sub_category: Optional[str] = None
    value: Optional[Any] = None
    weight: float = 0.5
    confidence: float = 0.5
    source_quote: Optional[str] = None
    tentative: bool = False


class ProfileUpdate(BaseModel):
    """Profile changes triggered by the last message."""
    added_interests: list[dict] = Field(default_factory=list)
    updated_personality: Optional[dict] = None
    updated_social_need: Optional[dict] = None
    new_version: Optional[int] = None


class SendMessageResponse(BaseModel):
    """Response after processing a user message."""
    message_id: int
    role: str = "assistant"
    content: str = Field(..., description="Agent's reply text")
    phase: str = Field(..., description="Current conversation phase")
    extracted_tags: list[ExtractedTag] = Field(default_factory=list)
    profile_updates: Optional[ProfileUpdate] = None
    tokens_used: int = 0
    latency_ms: float = 0.0


class MessageResponse(BaseModel):
    """A single message in conversation history."""
    id: int
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationState(BaseModel):
    """Current state of the conversation state machine."""
    phase: str
    collected_fields: list[str] = Field(default_factory=list)
    questions_asked: int = 0
    last_topic: Optional[str] = None


class ConversationResponse(BaseModel):
    """Full conversation detail."""
    id: int
    user_id: int
    state: ConversationState
    status: str
    messages: list[MessageResponse] = Field(default_factory=list)
    started_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    """Summary item for conversation list."""
    id: int
    status: str
    message_count: int
    phase: Optional[str] = None
    started_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
