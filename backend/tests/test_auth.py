"""Tests for authentication endpoints and security functions."""
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.auth import router
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.schemas import UserCreate, LoginRequest


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a bcrypt hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_hash_password_different_for_same_input(self):
        """Test that same password produces different hashes (salt)."""
        password = "testpassword123"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)

        assert hashed1 != hashed2
        assert verify_password(password, hashed1)
        assert verify_password(password, hashed2)

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test that verify_password handles empty password correctly."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False

    def test_verify_password_special_characters(self):
        """Test password hashing with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_hash_password_unicode(self):
        """Test password hashing with unicode characters."""
        password = "密码123 пароль"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestJWTTokens:
    """Test JWT token functions."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test creating a token with custom expiry."""
        data = {"sub": "user123"}
        expires = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires)

        assert isinstance(token, str)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"

    def test_decode_access_token_valid(self):
        """Test decoding a valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_decode_access_token_invalid(self):
        """Test decoding an invalid token returns None."""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_decode_access_token_expired(self):
        """Test decoding an expired token returns None."""
        data = {"sub": "user123"}
        # Create a token that expired 1 hour ago
        expires = timedelta(hours=-1)
        token = create_access_token(data, expires_delta=expires)
        decoded = decode_access_token(token)

        assert decoded is None

    def test_token_contains_expected_claims(self):
        """Test token contains all expected claims."""
        data = {"sub": "user456", "email": "user@example.com", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded["sub"] == "user456"
        assert decoded["email"] == "user@example.com"
        assert decoded["role"] == "admin"


class TestUserSchemas:
    """Test Pydantic schemas for users."""

    def test_user_create_valid(self):
        """Test UserCreate schema with valid data."""
        data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="securepass123",
        )
        assert data.email == "test@example.com"
        assert data.username == "testuser"
        assert data.password == "securepass123"

    def test_user_create_invalid_email(self):
        """Test UserCreate schema rejects invalid email."""
        with pytest.raises(ValueError):
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="securepass123",
            )

    def test_user_create_short_username(self):
        """Test UserCreate rejects short username."""
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                username="ab",  # min_length=3
                password="securepass123",
            )

    def test_user_create_short_password(self):
        """Test UserCreate rejects short password."""
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",  # min_length=8
            )

    def test_login_request_valid(self):
        """Test LoginRequest schema with valid data."""
        data = LoginRequest(email="test@example.com", password="password123")
        assert data.email == "test@example.com"
        assert data.password == "password123"

    def test_login_request_invalid_email(self):
        """Test LoginRequest rejects invalid email."""
        with pytest.raises(ValueError):
            LoginRequest(email="invalid", password="password123")


class TestAuthRouter:
    """Test authentication router endpoints."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create sync test client."""
        return TestClient(app)

    def test_register_missing_fields(self, client):
        """Test registration with missing fields returns error."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_email(self, client):
        """Test registration with invalid email returns error."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "password123",
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, client):
        """Test registration with short password returns error."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short",
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_empty_body(self, client):
        """Test registration with empty body returns error."""
        response = client.post("/auth/register", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthRouterAsync:
    """Test authentication router endpoints with async database mocks."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object using plain MagicMock to avoid SQLAlchemy issues."""
        user = MagicMock()
        user.id = uuid4()
        user.email = "test@example.com"
        user.username = "testuser"
        user.password_hash = hash_password("securepass123")
        user.is_active = True
        user.created_at = MagicMock()
        return user

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_user):
        """Test registration with existing email fails."""
        from app.api.auth import register
        from app.schemas import UserCreate
        from fastapi import HTTPException

        user_data = UserCreate(
            email="existing@example.com",
            username="newuser",
            password="securepass123",
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        # Return existing user to simulate duplicate email
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),
        ]

        with patch("app.api.auth.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await register(user_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_success(self, mock_user):
        """Test successful login."""
        from app.api.auth import login
        from app.schemas import LoginRequest

        login_data = LoginRequest(
            email="test@example.com",
            password="securepass123",
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        with patch("app.api.auth.get_db", return_value=mock_db):
            with patch("app.api.auth.get_settings") as mock_settings:
                mock_settings.return_value.app.secret_key = "test-secret-key"
                response = await login(login_data, mock_db)

        assert response.access_token is not None
        assert response.token_type == "bearer"
        assert response.expires_in == 3600

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, mock_user):
        """Test login with non-existent email fails."""
        from app.api.auth import login
        from app.schemas import LoginRequest
        from fastapi import HTTPException

        login_data = LoginRequest(
            email="nonexistent@example.com",
            password="securepass123",
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        # Return None for non-existent user
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        with patch("app.api.auth.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, mock_user):
        """Test login with wrong password fails."""
        from app.api.auth import login
        from app.schemas import LoginRequest
        from fastapi import HTTPException

        login_data = LoginRequest(
            email="test@example.com",
            password="wrongpassword",
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        with patch("app.api.auth.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_user):
        """Test login with inactive user fails."""
        from app.api.auth import login
        from app.schemas import LoginRequest
        from fastapi import HTTPException

        mock_user.is_active = False
        login_data = LoginRequest(
            email="test@example.com",
            password="securepass123",
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        with patch("app.api.auth.get_db", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User account is disabled" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_valid(self, mock_user):
        """Test getting current user with valid token."""
        from app.api.auth import get_current_user

        token = create_access_token(
            data={"sub": str(mock_user.id), "email": mock_user.email}
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        with patch("app.api.auth.get_db", return_value=mock_db):
            response = await get_current_user(token, mock_db)

        assert response.id == mock_user.id
        assert response.email == mock_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token fails."""
        from app.api.auth import get_current_user
        from fastapi import HTTPException

        invalid_token = "invalid.token.here"

        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(invalid_token, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test getting current user when user doesn't exist."""
        from app.api.auth import get_current_user
        from fastapi import HTTPException

        user_id = str(uuid4())
        token = create_access_token(
            data={"sub": user_id, "email": "deleted@example.com"}
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        # Return None for non-existent user
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in str(exc_info.value.detail)


class TestAuthIntegration:
    """Integration tests for auth endpoints with async client."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with only auth router."""
        from fastapi import FastAPI
        from app.api.auth import router
        app = FastAPI()
        app.include_router(router)

        @app.get("/")
        async def root():
            return {"status": "ok"}

        return app

    def test_root_endpoint(self, app):
        """Test root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"

    def test_register_validation_error_invalid_email(self, app):
        """Test registration with invalid email returns validation error."""
        client = TestClient(app)
        response = client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "password123",
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
