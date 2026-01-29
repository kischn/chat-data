"""Chart API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.schemas import ChartGenerateRequest, ChartGenerateResponse, ChartSuggestResponse
from app.services import VisualizationService

router = APIRouter(prefix="/charts", tags=["Visualization"])


async def get_current_user_id(token: str) -> UUID:
    """Extract user ID from token."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )
    return UUID(payload.get("sub"))


@router.post("/generate", response_model=ChartGenerateResponse)
async def generate_chart(
    request: ChartGenerateRequest,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Generate a chart for a dataset."""
    await get_current_user_id(token)

    service = VisualizationService(db)
    chart = await service.generate_chart(
        dataset_id=request.dataset_id,
        chart_type=request.chart_type,
        x_column=request.x_column,
        y_column=request.y_column,
        title=request.title,
    )

    return ChartGenerateResponse(**chart)


@router.get("/{chart_id}")
async def get_chart(
    chart_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Get chart image."""
    await get_current_user_id(token)

    service = VisualizationService(db)
    try:
        content, content_type = await service.get_chart(chart_id)
        return Response(
            content=content,
            media_type=content_type,
        )
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Chart not found",
        )


@router.get("/suggest/{dataset_id}", response_model=ChartSuggestResponse)
async def suggest_charts(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Get chart suggestions for a dataset."""
    await get_current_user_id(token)

    service = VisualizationService(db)
    suggestions = await service.suggest_chart_types(dataset_id)

    return ChartSuggestResponse(
        dataset_id=str(dataset_id),
        suggestions=suggestions,
    )
