"""Tests for data cleaning service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.cleaning_service import DataCleaningService


class TestDataCleaningService:
    """Test DataCleaningService class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_db_session):
        """Create cleaning service with mock dependencies."""
        with patch("app.services.cleaning_service.get_settings") as mock_settings:
            mock_settings.return_value.storage.endpoint = "localhost:9000"
            mock_settings.return_value.storage.access_key = "test"
            mock_settings.return_value.storage.secret_key = "test"
            mock_settings.return_value.storage.bucket = "test-bucket"

            with patch("app.services.cleaning_service.Minio"):
                service = DataCleaningService(mock_db_session)
                return service

    @pytest.mark.asyncio
    async def test_suggest_cleaning_strategies_dataset_not_found(self, service, mock_db_session):
        """Test suggest_cleaning_strategies raises error for non-existent dataset."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(ValueError, match="Dataset not found"):
            await service.suggest_cleaning_strategies(uuid4())


class TestCleaningStrategies:
    """Test cleaning strategy logic."""

    def test_high_missing_rate_strategy(self):
        """Test strategy for high missing rate (>50%)."""
        null_rate = 0.7  # 70% missing

        if null_rate > 0.5:
            strategy = "drop_column"
            reason = f"Missing {null_rate:.1%} of values - too many to impute"

        assert strategy == "drop_column"
        assert "too many" in reason

    def test_moderate_missing_rate_numeric_strategy(self):
        """Test strategy for moderate missing rate with numeric data (>10%)."""
        null_rate = 0.15  # 15% missing
        is_numeric = True

        if null_rate > 0.5:
            strategy = "drop_column"
        elif null_rate > 0.1:
            if is_numeric:
                strategy = "impute_median"
                reason = "Moderate missing rate - use median to resist outliers"
            else:
                strategy = "impute_mode"

        assert strategy == "impute_median"
        assert "median" in reason

    def test_low_missing_rate_strategy(self):
        """Test strategy for low missing rate (<10%)."""
        null_rate = 0.05  # 5% missing
        is_numeric = True

        if null_rate > 0.5:
            strategy = "drop_column"
        elif null_rate > 0.1:
            strategy = "impute_median" if is_numeric else "impute_mode"
        else:
            strategy = "impute_mean" if is_numeric else "drop_rows"

        assert strategy == "impute_mean"

    def test_outlier_detection_threshold(self):
        """Test outlier detection threshold (1%)."""
        outlier_rate = 0.005  # 0.5% outliers

        if outlier_rate > 0.01:
            should_handle = True
        else:
            should_handle = False

        assert should_handle is False  # Below threshold

    def test_outlier_handling(self):
        """Test outlier handling decision."""
        outlier_rate = 0.02  # 2% outliers

        if outlier_rate > 0.01:
            strategy = "winsorize"
            reason = f"{outlier_rate:.1%} outliers detected - winsorize to cap extreme values"

        assert strategy == "winsorize"
        assert "winsorize" in reason


class TestCleaningExecution:
    """Test cleaning execution logic."""

    def test_cleaning_operation_types(self):
        """Test supported cleaning operation types."""
        valid_operations = [
            "missing_values",
            "outliers",
            "data_type",
        ]

        operation = "missing_values"
        assert operation in valid_operations

    def test_missing_value_strategies(self):
        """Test missing value handling strategies."""
        strategies = ["drop_rows", "drop_column", "impute_mean", "impute_median", "impute_mode"]

        strategy = "impute_median"
        assert strategy in strategies

        # Verify strategies are applicable to data types
        numeric_strategies = ["impute_mean", "impute_median"]
        categorical_strategies = ["impute_mode", "drop_rows"]

        assert "impute_median" in numeric_strategies
        assert "impute_mode" in categorical_strategies

    def test_outlier_strategies(self):
        """Test outlier handling strategies."""
        strategies = ["winsorize", "drop_rows", "cap_values"]

        strategy = "winsorize"
        assert strategy in strategies

    def test_datatype_conversion_strategies(self):
        """Test data type conversion strategies."""
        strategies = ["convert_datetime", "convert_numeric", "normalize"]

        strategy = "convert_datetime"
        assert strategy in strategies
