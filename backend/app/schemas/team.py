"""Team schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    """Base team schema."""
    name: str = Field(..., min_length=1, max_length=200)


class TeamCreate(TeamBase):
    """Schema for creating a team."""
    pass


class TeamResponse(TeamBase):
    """Schema for team response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    team_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True
