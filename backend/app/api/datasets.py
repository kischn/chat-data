"""Dataset endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Dataset, DatasetColumn, User
from app.schemas import DatasetCreate, DatasetResponse, DatasetListResponse
from app.services import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


async def get_current_user_id(token: str) -> UUID:
    """Extract user ID from token."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return UUID(payload.get("sub"))


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_public: bool = False,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Upload a new dataset."""
    user_id = await get_current_user_id(token)

    service = DatasetService(db)
    dataset = await service.upload_dataset(
        file=file,
        user_id=user_id,
        name=name or file.filename,
        description=description,
        is_public=is_public,
    )

    return dataset


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    skip: int = 0,
    limit: int = 20,
    public_only: bool = False,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """List datasets."""
    user_id = await get_current_user_id(token)

    # Build query
    if public_only:
        query = select(Dataset).where(Dataset.is_public == True)
    else:
        query = select(Dataset).where(
            (Dataset.owner_id == user_id) | (Dataset.is_public == True)
        )

    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    # Get items
    result = await db.execute(
        query.order_by(Dataset.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()

    return DatasetListResponse(items=items, total=total)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Get dataset by ID."""
    user_id = await get_current_user_id(token)

    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            and_(
                (Dataset.owner_id == user_id) | (Dataset.is_public == True)
            )
        )
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Delete a dataset."""
    user_id = await get_current_user_id(token)

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

    await db.delete(dataset)
    await db.commit()
