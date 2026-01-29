"""Data cleaning API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.schemas import CleaningSuggestionResponse, CleaningExecuteRequest, CleaningExecuteResponse
from app.services import DataCleaningService

router = APIRouter(prefix="/datasets", tags=["Data Cleaning"])


async def get_current_user_id(token: str) -> UUID:
    """Extract user ID from token."""
    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return UUID(payload.get("sub"))


@router.get("/{dataset_id}/cleaning/suggestions", response_model=CleaningSuggestionResponse)
async def get_cleaning_suggestions(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Get AI-powered data cleaning suggestions for a dataset."""
    user_id = await get_current_user_id(token)

    # Verify dataset ownership
    from app.models import Dataset
    from sqlalchemy import select

    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.owner_id == user_id,
        )
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    service = DataCleaningService(db)
    suggestions = await service.suggest_cleaning_strategies(dataset_id)

    return CleaningSuggestionResponse(**suggestions)


@router.post("/{dataset_id}/cleaning/execute", response_model=CleaningExecuteResponse)
async def execute_cleaning(
    dataset_id: UUID,
    request: CleaningExecuteRequest,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Execute data cleaning operations on a dataset."""
    user_id = await get_current_user_id(token)

    # Verify dataset ownership
    from app.models import Dataset
    from sqlalchemy import select

    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.owner_id == user_id,
        )
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    service = DataCleaningService(db)
    result = await service.execute_cleaning(dataset_id, request.operations)

    return CleaningExecuteResponse(**result)
