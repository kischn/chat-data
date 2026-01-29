"""Chart/Visualization schemas."""
from typing import Any, list

from pydantic import BaseModel, Field


class ChartGenerateRequest(BaseModel):
    """Request to generate a chart."""
    dataset_id: str
    chart_type: str = Field(..., pattern="^(bar|line|scatter|histogram|heatmap|pie)$")
    x_column: str | None = None
    y_column: str | None = None
    title: str | None = None


class ChartGenerateResponse(BaseModel):
    """Response for chart generation."""
    chart_id: str
    chart_type: str
    url: str


class ChartSuggestItem(BaseModel):
    """Schema for a chart suggestion."""
    type: str
    description: str
    columns: dict[str, str]


class ChartSuggestResponse(BaseModel):
    """Response for chart suggestions."""
    dataset_id: str
    suggestions: list[ChartSuggestItem]
