"""Team and collaboration endpoints."""
from typing import list
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Team, TeamMember, User
from app.schemas import TeamCreate, TeamResponse, TeamMemberResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


async def get_current_user_id(token: str) -> UUID:
    """Extract user ID from token."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return UUID(payload.get("sub"))


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Create a new team."""
    user_id = await get_current_user_id(token)

    # Create team
    team = Team(name=team_data.name)
    db.add(team)
    await db.flush()

    # Add creator as owner
    membership = TeamMember(
        team_id=team.id,
        user_id=user_id,
        role="owner",
    )
    db.add(membership)

    await db.commit()
    await db.refresh(team)

    return team


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """List teams the current user belongs to."""
    user_id = await get_current_user_id(token)

    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.user_id == user_id)
        .join(Team)
    )
    memberships = result.scalars().all()

    return [membership.team for membership in memberships]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Get team details."""
    user_id = await get_current_user_id(token)

    # Check membership
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team",
        )

    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    return team


@router.post("/{team_id}/members", response_model=TeamMemberResponse)
async def add_member(
    team_id: UUID,
    user_email: str,
    role: str = "member",
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Add a member to the team."""
    current_user_id = await get_current_user_id(token)

    # Check if current user is owner or admin
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership or membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners or admins can add members",
        )

    # Find user by email
    result = await db.execute(
        select(User).where(User.email == user_email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member",
        )

    # Add member
    new_membership = TeamMember(
        team_id=team_id,
        user_id=user.id,
        role=role,
    )
    db.add(new_membership)
    await db.commit()
    await db.refresh(new_membership)

    return new_membership


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_members(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """List team members."""
    user_id = await get_current_user_id(token)

    # Check membership
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team",
        )

    result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id)
    )
    return result.scalars().all()


@router.delete("/{team_id}/members/{user_id}")
async def remove_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = None,
):
    """Remove a member from the team."""
    current_user_id = await get_current_user_id(token)

    # Get current user's membership
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership or membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can remove members",
        )

    # Cannot remove owner
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    target_membership = result.scalar_one_or_none()

    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    if target_membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove team owner",
        )

    await db.delete(target_membership)
    await db.commit()
