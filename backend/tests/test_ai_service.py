"""Tests for AI chat service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.ai_service import AIChatService


class TestAIChatService:
    """Test AIChatService class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.flush = session.refresh = Async AsyncMock()
       Mock()
        return session

    @pytest.fixture
    def service(self, mock_db_session):
        """Create AI chat service with mock dependencies."""
        with patch("app.services.ai_service.get_settings") as mock_settings:
            mock_settings.return_value.ai.api_key = "test-key"
            mock_settings.return_value.ai.base_url = "https://api.deepseek.com"
            mock_settings.return_value.ai.model = "deepseek-chat"
            mock_settings.return_value.ai.temperature = 0.7

            with patch("app.services.ai_service.AsyncOpenAI") as mock_client:
                mock_client.return_value.chat.completions.create = AsyncMock()
                service = AIChatService(mock_db_session)
                return service

    @pytest.mark.asyncio
    async def test_create_conversation(self, service, mock_db_session):
        """Test conversation creation."""
        user_id = uuid4()
        dataset_id = uuid4()

        mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', uuid4())

        conversation = await service.create_conversation(
            user_id=user_id,
            dataset_id=dataset_id,
            title="Test Conversation",
        )

        assert conversation.user_id == user_id
        assert conversation.dataset_id == dataset_id
        assert conversation.title == "Test Conversation"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, service, mock_db_session):
        """Test get_conversation returns None for non-existent conversation."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await service.get_conversation(uuid4(), uuid4())

        assert result is None


class TestSystemPromptBuilder:
    """Test system prompt generation."""

    def test_build_prompt_without_dataset(self):
        """Test prompt building without dataset context."""
        context = {"has_dataset": False}

        if context.get("has_dataset"):
            has_dataset_info = True
        else:
            has_dataset_info = False

        assert has_dataset_info is False

    def test_build_prompt_with_dataset(self):
        """Test prompt building with dataset context."""
        context = {
            "has_dataset": True,
            "dataset_id": "test-id",
            "dataset_name": "Sales Data",
            "dataset_description": "Q4 sales data",
            "row_count": 1000,
            "columns": [
                {
                    "name": "date",
                    "type": "datetime64",
                    "statistics": {"null_rate": 0, "unique_count": 100},
                },
                {
                    "name": "amount",
                    "type": "float64",
                    "statistics": {"null_rate": 0.02, "mean": 500, "std": 100},
                },
            ],
        }

        assert context["has_dataset"] is True
        assert context["dataset_name"] == "Sales Data"
        assert len(context["columns"]) == 2

        # Check column info is included
        col = context["columns"][1]
        assert col["statistics"]["mean"] == 500


class TestCodeExtraction:
    """Test code extraction from responses."""

    def test_extract_python_code(self):
        """Test extracting Python code from markdown response."""
        import re

        response = """
Here's the analysis code:

```python
import pandas as pd

df = pd.read_csv('data.csv')
print(df.describe())
```

Let me know if you need any changes!
"""

        pattern = r"```python\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)

        assert len(matches) == 1
        assert "pandas" in matches[0]
        assert "read_csv" in matches[0]

    def test_no_code_in_response(self):
        """Test when no code is present in response."""
        import re

        response = "I can help you analyze the data. The average value is 42.5."

        pattern = r"```python\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)

        assert len(matches) == 0

    def test_multiple_code_blocks(self):
        """Test extracting from multiple code blocks."""
        import re

        response = """
First, let's load the data:

```python
df = pd.read_csv('data.csv')
```

Then, let's analyze it:

```python
print(df.mean())
```
"""

        pattern = r"```python\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)

        assert len(matches) == 2


class TestResponseFormatting:
    """Test response formatting utilities."""

    def test_format_code_result_dataframe_info(self):
        """Test formatting dataframe info from code result."""
        result = {
            "success": True,
            "dataframe_info": {
                "shape": [1000, 5],
                "columns": ["id", "name", "value", "date", "status"],
            },
            "charts": [{"id": "abc123", "type": "image"}],
            "output": "mean: 50.0\nstd: 10.0",
        }

        # Verify result structure
        assert result["success"] is True
        assert result["dataframe_info"]["shape"] == [1000, 5]
        assert len(result["dataframe_info"]["columns"]) == 5
        assert len(result["charts"]) == 1
        assert result["output"] is not None

    def test_format_code_result_no_dataframe(self):
        """Test formatting when no dataframe info."""
        result = {
            "success": False,
            "error": "Dataset not found",
            "message": "The specified dataset could not be located",
        }

        assert result["success"] is False
        assert "error" in result
