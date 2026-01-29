"""Pytest configuration and fixtures."""
import asyncio
import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Set up event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepassword123",
    }


@pytest.fixture
def sample_dataset_metadata():
    """Sample dataset metadata."""
    return {
        "columns": ["id", "name", "value", "date"],
        "row_count": 100,
        "statistics": {
            "id": {"dtype": "int64", "null_rate": 0},
            "name": {"dtype": "object", "null_rate": 0.05},
            "value": {"dtype": "float64", "null_rate": 0.02, "mean": 50.5, "std": 10.2},
            "date": {"dtype": "datetime64", "null_rate": 0},
        },
    }


@pytest.fixture
def sample_chat_message():
    """Sample chat message."""
    return {
        "message": "Show me the distribution of values",
        "code_execution": True,
    }


@pytest.fixture
def sample_cleaning_operations():
    """Sample cleaning operations."""
    return [
        {
            "type": "missing_values",
            "column": "name",
            "strategy": "impute_mode",
        },
        {
            "type": "outliers",
            "column": "value",
            "strategy": "winsorize",
        },
    ]
