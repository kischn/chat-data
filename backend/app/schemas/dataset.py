"""Dataset schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ColumnStatistics(BaseModel):
    """Schema for column statistics."""
    dtype: Optional[str] = None
    null_count: Optional[int] = None
    null_rate: Optional[float] = None
    unique_count: Optional[int] = None
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    sample_values: Optional[list] = None


class ColumnSchema(BaseModel):
    """Schema for column metadata."""
    id: UUID
    name: str
    data_type: Optional[str] = None
    nullable: bool = True
    statistics: Optional[ColumnStatistics] = None
    position: int


class DatasetBase(BaseModel):
    """Base dataset schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False


class DatasetCreate(DatasetBase):
    """Schema for creating a dataset."""
    pass


class DatasetResponse(DatasetBase):
    """Schema for dataset response."""
    id: UUID
    file_path: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    owner_id: UUID
    team_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None
    columns: list[ColumnSchema] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Schema for dataset list response."""
    items: list[DatasetResponse]
    total: int
