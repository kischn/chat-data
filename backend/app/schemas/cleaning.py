"""Cleaning schemas."""
from typing import Any

from pydantic import BaseModel


class CleaningSuggestionItem(BaseModel):
    """Schema for a single cleaning suggestion."""
    type: str  # 'missing_values', 'outliers', 'data_type'
    column: str
    rate: float | None = None
    count: int | None = None
    strategy: str
    reason: str


class CleaningSuggestionResponse(BaseModel):
    """Schema for cleaning suggestions response."""
    dataset_id: str
    dataset_name: str
    row_count: int
    column_count: int
    suggestions: list[CleaningSuggestionItem]


class CleaningOperation(BaseModel):
    """Schema for a cleaning operation."""
    type: str
    column: str
    strategy: str


class CleaningExecuteRequest(BaseModel):
    """Schema for executing cleaning operations."""
    operations: list[CleaningOperation]


class CleaningExecuteResponse(BaseModel):
    """Schema for cleaning execution response."""
    new_dataset_id: str
    new_dataset_name: str
    original_shape: list[int]
    cleaned_shape: list[int]
    operations_applied: list[dict[str, Any]]
