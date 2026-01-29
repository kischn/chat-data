"""Tests for Pydantic schemas."""
import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4

from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.schemas.dataset import DatasetCreate, DatasetResponse, ColumnStatistics
from app.schemas.conversation import ChatRequest, ChatResponse, ConversationCreate
from app.schemas.cleaning import CleaningSuggestionResponse, CleaningExecuteRequest
from app.schemas.chart import ChartGenerateRequest


class TestUserSchemas:
    """Test user-related schemas."""

    def test_user_create_valid(self):
        """Test valid UserCreate schema."""
        data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        assert data.email == "test@example.com"
        assert data.username == "testuser"
        assert data.password == "password123"

    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="password123",
            )

    def test_user_create_short_username(self):
        """Test UserCreate with short username."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",  # min_length=3
                password="password123",
            )

    def test_user_create_short_password(self):
        """Test UserCreate with short password."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",  # min_length=8
            )

    def test_login_request_valid(self):
        """Test valid LoginRequest schema."""
        data = LoginRequest(
            email="test@example.com",
            password="password123",
        )
        assert data.email == "test@example.com"
        assert data.password == "password123"


class TestDatasetSchemas:
    """Test dataset-related schemas."""

    def test_dataset_create_valid(self):
        """Test valid DatasetCreate schema."""
        data = DatasetCreate(
            name="My Dataset",
            description="A test dataset",
            is_public=True,
        )
        assert data.name == "My Dataset"
        assert data.description == "A test dataset"
        assert data.is_public is True

    def test_dataset_create_minimal(self):
        """Test DatasetCreate with minimal fields."""
        data = DatasetCreate(name="Minimal Dataset")
        assert data.name == "Minimal Dataset"
        assert data.description is None
        assert data.is_public is False

    def test_column_statistics_valid(self):
        """Test valid ColumnStatistics schema."""
        data = ColumnStatistics(
            dtype="float64",
            null_count=5,
            null_rate=0.05,
            unique_count=100,
            min=0.0,
            max=100.0,
            mean=50.0,
            std=10.0,
            sample_values=[1.0, 2.0, 3.0],
        )
        assert data.dtype == "float64"
        assert data.null_rate == 0.05


class TestConversationSchemas:
    """Test conversation-related schemas."""

    def test_chat_request_valid(self):
        """Test valid ChatRequest schema."""
        data = ChatRequest(
            message="Show me the data distribution",
            code_execution=True,
        )
        assert data.message == "Show me the data distribution"
        assert data.code_execution is True

    def test_chat_request_empty_message(self):
        """Test ChatRequest with empty message."""
        with pytest.raises(ValidationError):
            ChatRequest(message="", code_execution=True)

    def test_conversation_create_valid(self):
        """Test valid ConversationCreate schema."""
        data = ConversationCreate(
            dataset_id=uuid4(),
            title="Analysis Session",
        )
        assert data.title == "Analysis Session"
        assert data.dataset_id is not None


class TestCleaningSchemas:
    """Test cleaning-related schemas."""

    def test_cleaning_suggestion_response(self):
        """Test CleaningSuggestionResponse schema."""
        data = CleaningSuggestionResponse(
            dataset_id=str(uuid4()),
            dataset_name="Test Dataset",
            row_count=1000,
            column_count=5,
            suggestions=[
                {
                    "type": "missing_values",
                    "column": "price",
                    "rate": 0.05,
                    "strategy": "impute_median",
                    "reason": "Low missing rate - use median",
                }
            ],
        )
        assert data.dataset_name == "Test Dataset"
        assert len(data.suggestions) == 1

    def test_cleaning_execute_request(self):
        """Test CleaningExecuteRequest schema."""
        data = CleaningExecuteRequest(
            operations=[
                {"type": "missing_values", "column": "price", "strategy": "impute_median"},
                {"type": "outliers", "column": "value", "strategy": "winsorize"},
            ]
        )
        assert len(data.operations) == 2


class TestChartSchemas:
    """Test chart-related schemas."""

    def test_chart_generate_request_valid(self):
        """Test valid ChartGenerateRequest schema."""
        data = ChartGenerateRequest(
            dataset_id=str(uuid4()),
            chart_type="bar",
            x_column="category",
            y_column="value",
            title="Sales by Category",
        )
        assert data.chart_type == "bar"
        assert data.x_column == "category"

    def test_chart_generate_request_invalid_type(self):
        """Test ChartGenerateRequest with invalid chart type."""
        with pytest.raises(ValidationError):
            ChartGenerateRequest(
                dataset_id=str(uuid4()),
                chart_type="invalid_type",
            )
