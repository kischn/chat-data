"""AI Chat endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Conversation
from app.schemas import (
    ConversationCreate,
    ConversationResponse,
    ChatRequest,
    ChatResponse,
)
from app.services import AIChatService

router = APIRouter(prefix="/conversations", tags=["Chat"])


async def get_current_user_id(token: str) -> UUID:
    """Extract user ID from token."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return UUID(payload.get("sub"))


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate | None = None,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Create a new conversation."""
    user_id = await get_current_user_id(token)
    service = AIChatService(db)

    conversation = await service.create_conversation(
        user_id=user_id,
        dataset_id=conversation_data.dataset_id if conversation_data else None,
        title=conversation_data.title if conversation_data else None,
    )

    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Get conversation by ID with messages."""
    user_id = await get_current_user_id(token)
    service = AIChatService(db)

    conversation = await service.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation


@router.post("/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Send a message to the AI assistant."""
    user_id = await get_current_user_id(token)
    service = AIChatService(db)

    try:
        message = await service.chat(
            conversation_id=conversation_id,
            request=request,
            user_id=user_id,
        )
        return ChatResponse(message=message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    dataset_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """List conversations for the current user."""
    user_id = await get_current_user_id(token)
    service = AIChatService(db)

    if dataset_id:
        conversations = await service.get_conversations_by_dataset(user_id, dataset_id)
    else:
        from sqlalchemy import select

        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        conversations = result.scalars().all()

    return conversations


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Delete a conversation."""
    user_id = await get_current_user_id(token)

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conversation)
    await db.commit()
