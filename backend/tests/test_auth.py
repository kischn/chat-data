"""Tests for authentication endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router
from app.core.security import hash_password, verify_password


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a bcrypt hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

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


class TestAuthRouter:
    """Test authentication router endpoints."""

    @pytest.fixture
    def app(self):
        """Create test app."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_register_missing_fields(self, client):
        """Test registration with missing fields returns error."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 422  # Validation error

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

        assert response.status_code == 422  # Validation error

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

        assert response.status_code == 422  # Validation error
