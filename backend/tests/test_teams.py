"""Tests for team collaboration endpoints."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.schemas import TeamCreate, TeamResponse, TeamMemberResponse


class TestTeamSchemas:
    """Test Pydantic schemas for teams."""

    def test_team_create_valid(self):
        """Test TeamCreate schema with valid data."""
        data = TeamCreate(name="Engineering Team")
        assert data.name == "Engineering Team"

    def test_team_create_minimal(self):
        """Test TeamCreate with minimal data."""
        data = TeamCreate(name="My Team")
        assert data.name == "My Team"
        assert len(data.name) > 0

    def test_team_create_empty_name_fails(self):
        """Test TeamCreate rejects empty name."""
        with pytest.raises(ValueError):
            TeamCreate(name="")

    def test_team_create_long_name(self):
        """Test TeamCreate with max length name."""
        long_name = "a" * 200
        data = TeamCreate(name=long_name)
        assert len(data.name) == 200

    def test_team_create_name_too_long(self):
        """Test TeamCreate rejects name exceeding max length."""
        with pytest.raises(ValueError):
            TeamCreate(name="a" * 201)

    def test_team_create_unicode_name(self):
        """Test TeamCreate with unicode characters."""
        data = TeamCreate(name="团队_2024")
        assert data.name == "团队_2024"

    def test_team_create_special_chars(self):
        """Test TeamCreate with special characters."""
        data = TeamCreate(name="Team v2.0 - Alpha/Beta")
        assert data.name == "Team v2.0 - Alpha/Beta"


class TestTeamResponseSchemas:
    """Test team response schemas."""

    def test_team_response_fields(self):
        """Test TeamResponse has all required fields."""
        team_id = uuid4()
        now = datetime.utcnow()
        response_data = {
            "id": team_id,
            "name": "Test Team",
            "created_at": now.isoformat(),
        }
        response = TeamResponse(**response_data)
        assert response.id == team_id
        assert response.name == "Test Team"
        assert response.created_at is not None

    def test_team_response_with_minimal_data(self):
        """Test TeamResponse with minimal data."""
        team_id = uuid4()
        response = TeamResponse(
            id=team_id,
            name="Minimal Team",
            created_at=datetime.utcnow(),
        )
        assert response.id == team_id
        assert response.name == "Minimal Team"


class TestTeamMemberSchemas:
    """Test team member schemas."""

    def test_team_member_response_valid(self):
        """Test TeamMemberResponse with valid data."""
        team_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        response_data = {
            "team_id": team_id,
            "user_id": user_id,
            "role": "member",
            "joined_at": now.isoformat(),
        }
        response = TeamMemberResponse(**response_data)
        assert response.team_id == team_id
        assert response.user_id == user_id
        assert response.role == "member"

    def test_team_member_response_owner_role(self):
        """Test TeamMemberResponse with owner role."""
        team_id = uuid4()
        user_id = uuid4()
        response = TeamMemberResponse(
            team_id=team_id,
            user_id=user_id,
            role="owner",
            joined_at=datetime.utcnow(),
        )
        assert response.role == "owner"

    def test_team_member_response_admin_role(self):
        """Test TeamMemberResponse with admin role."""
        team_id = uuid4()
        user_id = uuid4()
        response = TeamMemberResponse(
            team_id=team_id,
            user_id=user_id,
            role="admin",
            joined_at=datetime.utcnow(),
        )
        assert response.role == "admin"


class TestTeamRouterSync:
    """Test team router with sync TestClient."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        from app.api.teams import router
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create sync test client."""
        return TestClient(app, raise_server_exceptions=False)

    @pytest.fixture
    def valid_token(self):
        """Create a valid JWT token for testing."""
        user_id = uuid4()
        return create_access_token(data={"sub": str(user_id), "email": "test@example.com"})

    def test_create_team_missing_name(self, client, valid_token):
        """Test creating team without name returns error."""
        response = client.post(
            "/teams",
            json={},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_team_empty_name(self, client, valid_token):
        """Test creating team with empty name returns error."""
        response = client.post(
            "/teams",
            json={"name": ""},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_teams_no_auth(self, client):
        """Test listing teams without auth returns error."""
        response = client.get("/teams")
        # Without auth token, the validation fails first
        assert response.status_code in [401, 422]

    def test_get_team_no_auth(self, client):
        """Test getting team without auth returns error."""
        team_id = uuid4()
        response = client.get(f"/teams/{team_id}")
        assert response.status_code in [401, 422]

    def test_invalid_token_format(self, client):
        """Test with invalid token format returns error."""
        response = client.get(
            "/teams",
            headers={"Authorization": "InvalidTokenFormat"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTeamRouterAsync:
    """Test team router endpoints with async database mocks."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = uuid4()
        user.email = "test@example.com"
        user.username = "testuser"
        return user

    @pytest.fixture
    def mock_team(self):
        """Create a mock team object."""
        team = MagicMock()
        team.id = uuid4()
        team.name = "Test Team"
        team.created_at = datetime.utcnow()
        return team

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def valid_token(self, mock_user):
        """Create a valid JWT token for testing."""
        return create_access_token(data={"sub": str(mock_user.id), "email": mock_user.email})

    @pytest.mark.asyncio
    async def test_create_team_invalid_token(self, mock_db):
        """Test team creation with invalid token fails."""
        from app.api.teams import create_team
        from app.schemas import TeamCreate

        team_data = TeamCreate(name="New Team")

        with pytest.raises(HTTPException) as exc_info:
            await create_team(team_data, mock_db, "invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_teams_invalid_token(self, mock_db):
        """Test listing teams with invalid token fails."""
        from app.api.teams import list_teams

        with pytest.raises(HTTPException) as exc_info:
            await list_teams(mock_db, "invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_team_invalid_token(self, mock_db):
        """Test getting team with invalid token fails."""
        from app.api.teams import get_team

        team_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await get_team(team_id, mock_db, "invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_add_member_invalid_token(self, mock_db):
        """Test adding member with invalid token fails."""
        from app.api.teams import add_member

        team_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await add_member(
                team_id=team_id,
                user_email="test@example.com",
                role="member",
                db=mock_db,
                token="invalid-token",
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_members_invalid_token(self, mock_db):
        """Test listing members with invalid token fails."""
        from app.api.teams import list_members

        team_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await list_members(team_id, mock_db, "invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_remove_member_invalid_token(self, mock_db):
        """Test removing member with invalid token fails."""
        from app.api.teams import remove_member

        team_id = uuid4()
        user_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await remove_member(team_id, user_id, mock_db, "invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_team_not_member(self, mock_db, valid_token):
        """Test getting team when not a member fails."""
        from app.api.teams import get_team

        team_id = uuid4()

        # Membership check returns None (not a member)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await get_team(team_id, mock_db, valid_token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not a member" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_team_not_found(self, mock_db, mock_user, valid_token):
        """Test getting non-existent team fails."""
        from app.api.teams import get_team

        team_id = uuid4()

        # First execute returns membership (user is member)
        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none = MagicMock(return_value=MagicMock())

        # Second execute returns None (team doesn't exist)
        mock_team_result = MagicMock()
        mock_team_result.scalar_one_or_none = MagicMock(return_value=None)

        mock_db.execute = AsyncMock(side_effect=[
            mock_membership_result,
            mock_team_result,
        ])

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await get_team(team_id, mock_db, valid_token)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Team not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_members_not_member(self, mock_db, valid_token):
        """Test listing members when not a member fails."""
        from app.api.teams import list_members

        team_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await list_members(team_id, mock_db, valid_token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestTeamMemberPermissions:
    """Test team member permission checks."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = uuid4()
        user.email = "member@example.com"
        user.username = "memberuser"
        return user

    @pytest.fixture
    def mock_team(self):
        """Create a mock team object."""
        team = MagicMock()
        team.id = uuid4()
        team.name = "Test Team"
        team.created_at = datetime.utcnow()
        return team

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def owner_token(self, mock_user):
        """Create token for team owner."""
        return create_access_token(data={"sub": str(mock_user.id), "email": mock_user.email})

    @pytest.fixture
    def member_token(self):
        """Create token for regular team member."""
        member_id = uuid4()
        return create_access_token(data={"sub": str(member_id), "email": "member@test.com"})

    @pytest.mark.asyncio
    async def test_add_member_by_non_admin_fails(self, mock_db, mock_team, member_token):
        """Test regular member cannot add members."""
        from app.api.teams import add_member

        team_id = mock_team.id

        # Mock membership check (regular member)
        member_membership = MagicMock()
        member_membership.role = "member"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=member_membership)
        mock_db.execute.return_value = mock_result

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await add_member(
                    team_id=team_id,
                    user_email="newmember@example.com",
                    role="member",
                    db=mock_db,
                    token=member_token,
                )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only owners or admins" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_add_member_user_not_found(self, mock_db, mock_user, mock_team, owner_token):
        """Test adding non-existent user fails."""
        from app.api.teams import add_member

        team_id = mock_team.id

        # Mock owner membership check
        owner_membership = MagicMock()
        owner_membership.role = "owner"

        # Mock user lookup returns None
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=owner_membership)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # User not found
        ])

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await add_member(
                    team_id=team_id,
                    user_email="nonexistent@example.com",
                    role="member",
                    db=mock_db,
                    token=owner_token,
                )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_remove_member_by_non_owner_fails(self, mock_db, member_token):
        """Test non-owner cannot remove members."""
        from app.api.teams import remove_member

        team_id = uuid4()
        member_id = uuid4()

        # Mock admin membership (not owner)
        admin_membership = MagicMock()
        admin_membership.role = "admin"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=admin_membership)
        mock_db.execute.return_value = mock_result

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await remove_member(team_id, member_id, mock_db, member_token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only owners can remove" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_remove_member_not_found(self, mock_db, mock_user, mock_team, owner_token):
        """Test removing non-existent member fails."""
        from app.api.teams import remove_member

        team_id = mock_team.id
        member_id = uuid4()

        # Mock owner membership check
        owner_membership = MagicMock()
        owner_membership.role = "owner"

        # Mock target membership returns None
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=owner_membership)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ])

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await remove_member(team_id, member_id, mock_db, owner_token)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Member not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_remove_owner_fails(self, mock_db, mock_user, mock_team, owner_token):
        """Test removing team owner fails."""
        from app.api.teams import remove_member

        team_id = mock_team.id
        owner_id = mock_user.id

        # Mock owner membership check
        owner_membership = MagicMock()
        owner_membership.role = "owner"

        # Mock target membership is also owner
        target_membership = MagicMock()
        target_membership.role = "owner"

        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=owner_membership)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_membership)),
        ])

        with patch("app.api.teams.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await remove_member(team_id, owner_id, mock_db, owner_token)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot remove team owner" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_admin_can_add_members(self, mock_db, mock_team):
        """Test admin can add team members - permission check only."""
        from app.api.teams import add_member

        team_id = mock_team.id
        admin_id = uuid4()
        admin_token = create_access_token(data={"sub": str(admin_id), "email": "admin@test.com"})

        # Mock admin membership check - permission should pass for admin
        admin_membership = MagicMock()
        admin_membership.role = "admin"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=admin_membership)
        mock_db.execute.return_value = mock_result

        with patch("app.api.teams.get_db", return_value=mock_db):
            # The test verifies that an admin (role=admin) passes the permission check
            # which is "Only owners or admins can add members"
            # We check that the error is NOT a 403 (permission denied)
            try:
                await add_member(
                    team_id=team_id,
                    user_email="new@example.com",
                    role="member",
                    db=mock_db,
                    token=admin_token,
                )
            except HTTPException as e:
                # If we get an HTTPException, it should NOT be a 403 (permission denied)
                # It might be 404 (user not found) or 400 (already member), but not 403
                assert e.status_code != status.HTTP_403_FORBIDDEN, "Admin should have permission to add members"


class TestTeamEdgeCases:
    """Test edge cases in team operations."""

    def test_team_name_whitespace(self):
        """Test team name with whitespace."""
        from app.schemas import TeamCreate

        # Leading/trailing whitespace should be allowed by schema
        data = TeamCreate(name="  Team Name  ")
        assert data.name == "  Team Name  "

    def test_team_name_unicode_length(self):
        """Test unicode character counting in team name."""
        from app.schemas import TeamCreate

        # Each unicode character should count as one
        data = TeamCreate(name="中文团队")
        assert len(data.name) == 4

    def test_role_values(self):
        """Test valid role values."""
        from app.schemas import TeamMemberResponse
        from datetime import datetime

        team_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()

        for role in ["owner", "admin", "member"]:
            response = TeamMemberResponse(
                team_id=team_id,
                user_id=user_id,
                role=role,
                joined_at=now,
            )
            assert response.role == role

    def test_empty_members_list(self):
        """Test response with empty members list."""
        from app.schemas import TeamResponse
        from datetime import datetime

        team_id = uuid4()
        response = TeamResponse(
            id=team_id,
            name="Solo Team",
            created_at=datetime.utcnow(),
        )
        assert response.id == team_id
        assert response.name == "Solo Team"

    def test_token_with_expired_format(self):
        """Test token with proper format but expired."""
        from app.core.security import decode_access_token
        from datetime import timedelta

        # Create an expired token
        user_id = str(uuid4())
        token = create_access_token(
            data={"sub": user_id, "email": "test@example.com"},
            expires_delta=timedelta(hours=-1)
        )
        decoded = decode_access_token(token)
        assert decoded is None

    def test_token_with_valid_sub_claim(self):
        """Test token with valid sub claim."""
        from app.core.security import decode_access_token

        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id, "email": "test@example.com"})
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == user_id
        assert decoded["email"] == "test@example.com"


class TestTeamValidation:
    """Test input validation for team endpoints."""

    def test_team_create_name_min_length(self):
        """Test team name minimum length."""
        from app.schemas import TeamCreate

        # Empty string should fail
        with pytest.raises(ValueError):
            TeamCreate(name="")

    def test_team_create_name_max_length(self):
        """Test team name maximum length."""
        from app.schemas import TeamCreate

        # 200 chars should pass
        data = TeamCreate(name="a" * 200)
        assert len(data.name) == 200

        # 201 chars should fail
        with pytest.raises(ValueError):
            TeamCreate(name="a" * 201)

    def test_team_member_response_validation(self):
        """Test team member response schema validation."""
        from app.schemas import TeamMemberResponse
        from datetime import datetime

        team_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()

        # Valid data
        response = TeamMemberResponse(
            team_id=team_id,
            user_id=user_id,
            role="admin",
            joined_at=now,
        )
        assert response.role == "admin"

    def test_team_response_validation(self):
        """Test team response schema validation."""
        from app.schemas import TeamResponse
        from datetime import datetime

        team_id = uuid4()

        # Valid data
        response = TeamResponse(
            id=team_id,
            name="Test Team",
            created_at=datetime.utcnow(),
        )
        assert response.name == "Test Team"
