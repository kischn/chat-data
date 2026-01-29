"""Conversation schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base message schema."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    code_execution: bool = True


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    code_result: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: Optional[str] = Field(None, max_length=500)
    dataset_id: Optional[UUID] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: UUID
    user_id: UUID
    messages: list[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1)
    code_execution: bool = True


class ChatResponse(BaseModel):
    """Schema for chat response."""
    message: MessageResponse
