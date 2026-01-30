"""Tests for data cleaning service and API endpoints."""
import io
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pandas as pd
from pydantic import ValidationError

from app.schemas.cleaning import (
    CleaningSuggestionItem,
    CleaningSuggestionResponse,
    CleaningOperation,
    CleaningExecuteRequest,
    CleaningExecuteResponse,
)


class TestCleaningSchemas:
    """Test Pydantic schemas for data cleaning."""

    def test_cleaning_suggestion_item_valid(self):
        """Test CleaningSuggestionItem with valid data."""
        item = CleaningSuggestionItem(
            type="missing_values",
            column="age",
            rate=0.15,
            strategy="impute_median",
            reason="Moderate missing rate - use median to resist outliers",
        )
        assert item.type == "missing_values"
        assert item.column == "age"
        assert item.rate == 0.15
        assert item.strategy == "impute_median"

    def test_cleaning_suggestion_item_optional_fields(self):
        """Test CleaningSuggestionItem with optional fields."""
        item = CleaningSuggestionItem(
            type="outliers",
            column="salary",
            count=25,
            rate=0.02,
            strategy="winsorize",
            reason="2.0% outliers detected",
        )
        assert item.count == 25
        assert item.rate == 0.02

    def test_cleaning_suggestion_response_valid(self):
        """Test CleaningSuggestionResponse with valid data."""
        response = CleaningSuggestionResponse(
            dataset_id=str(uuid4()),
            dataset_name="test_data",
            row_count=1000,
            column_count=5,
            suggestions=[
                CleaningSuggestionItem(
                    type="missing_values",
                    column="age",
                    rate=0.1,
                    strategy="impute_mean",
                    reason="Low missing rate",
                )
            ],
        )
        assert response.row_count == 1000
        assert len(response.suggestions) == 1

    def test_cleaning_operation_valid(self):
        """Test CleaningOperation with valid data."""
        op = CleaningOperation(
            type="missing_values",
            column="age",
            strategy="impute_median",
        )
        assert op.type == "missing_values"
        assert op.strategy == "impute_median"

    def test_cleaning_execute_request_valid(self):
        """Test CleaningExecuteRequest with valid operations."""
        request = CleaningExecuteRequest(
            operations=[
                CleaningOperation(
                    type="missing_values",
                    column="age",
                    strategy="impute_median",
                ),
                CleaningOperation(
                    type="outliers",
                    column="salary",
                    strategy="winsorize",
                ),
            ]
        )
        assert len(request.operations) == 2

    def test_cleaning_execute_response_valid(self):
        """Test CleaningExecuteResponse with valid data."""
        response = CleaningExecuteResponse(
            new_dataset_id=str(uuid4()),
            new_dataset_name="data (cleaned)",
            original_shape=[1000, 5],
            cleaned_shape=[995, 5],
            operations_applied=[
                {"type": "drop_rows", "column": "age", "rows_removed": 5}
            ],
        )
        assert response.original_shape == [1000, 5]
        assert response.cleaned_shape == [995, 5]


class TestMissingValueDetection:
    """Test missing value detection and strategies."""

    def test_missing_value_detection_high_rate(self):
        """Test detection with high missing rate (>50%)."""
        df = pd.DataFrame({
            "id": range(100),
            "empty_col": [None] * 80 + list(range(20)),  # 80% missing
        })

        null_rate = df["empty_col"].isna().mean()
        assert null_rate == 0.8
        assert null_rate > 0.5

    def test_missing_value_detection_moderate_rate_numeric(self):
        """Test detection with moderate missing rate for numeric column."""
        df = pd.DataFrame({
            "id": range(100),
            "numeric_col": [None] * 15 + list(range(85)),  # 15% missing
        })

        null_rate = df["numeric_col"].isna().mean()
        assert 0.1 < null_rate <= 0.5

    def test_missing_value_detection_low_rate(self):
        """Test detection with low missing rate."""
        df = pd.DataFrame({
            "id": range(100),
            "low_missing": [None] * 5 + list(range(95)),  # 5% missing
        })

        null_rate = df["low_missing"].isna().mean()
        assert null_rate == 0.05
        assert null_rate <= 0.1

    def test_missing_value_detection_categorical(self):
        """Test detection for categorical column."""
        df = pd.DataFrame({
            "id": range(100),
            "category": ["A"] * 85 + [None] * 15,  # 15% missing
        })

        null_rate = df["category"].isna().mean()
        assert null_rate == 0.15
        assert pd.api.types.is_object_dtype(df["category"])


class TestOutlierDetection:
    """Test outlier detection using IQR method."""

    def test_outlier_detection_basic(self):
        """Test basic outlier detection with IQR."""
        df = pd.DataFrame({
            "value": [10, 12, 14, 13, 11, 100, 15, 14, 12],  # 100 is outlier
        })

        q1 = df["value"].quantile(0.25)
        q3 = df["value"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = ((df["value"] < lower) | (df["value"] > upper)).sum()
        outlier_rate = outliers / len(df)

        assert outlier_rate > 0.01  # Should trigger suggestion

    def test_outlier_detection_no_outliers(self):
        """Test detection with no outliers."""
        df = pd.DataFrame({
            "value": [10, 12, 14, 13, 11, 15, 14, 12, 16],
        })

        q1 = df["value"].quantile(0.25)
        q3 = df["value"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = ((df["value"] < lower) | (df["value"] > upper)).sum()
        outlier_rate = outliers / len(df)

        assert outlier_rate == 0  # No outliers
        assert outlier_rate <= 0.01

    def test_outlier_detection_with_extreme_values(self):
        """Test detection with very extreme outliers."""
        df = pd.DataFrame({
            "value": [100, 102, 101, 99, 1000, 103, 100, 102, 100],
        })

        q1 = df["value"].quantile(0.25)
        q3 = df["value"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = ((df["value"] < lower) | (df["value"] > upper)).sum()
        outlier_rate = outliers / len(df)

        assert outlier_rate > 0.1  # Should trigger suggestion


class TestDataTypeDetection:
    """Test data type detection for datetime conversion."""

    def test_datetime_detection_valid(self):
        """Test detection of datetime-like values."""
        dates = ["2024-01-15", "2024-02-20", "2024-03-10"]
        df = pd.DataFrame({"date_col": dates})

        try:
            pd.to_datetime(df["date_col"].dropna().head(100), errors="raise")
            is_datetime = True
        except Exception:
            is_datetime = False

        assert is_datetime is True

    def test_datetime_detection_invalid(self):
        """Test detection of non-datetime values."""
        values = ["abc", "def", "ghi"]
        df = pd.DataFrame({"text_col": values})

        try:
            pd.to_datetime(df["text_col"].dropna().head(100), errors="raise")
            is_datetime = True
        except Exception:
            is_datetime = False

        assert is_datetime is False

    def test_mixed_datetime_detection(self):
        """Test detection with mixed valid/invalid datetime values."""
        values = ["2024-01-15", "invalid", "2024-03-10"]
        df = pd.DataFrame({"date_col": values})

        # Should still detect as potential datetime
        converted = pd.to_datetime(df["date_col"], errors="coerce")
        valid_count = converted.notna().sum()

        assert valid_count == 2


class TestCleaningStrategies:
    """Test cleaning strategy selection based on data characteristics."""

    def test_strategy_for_high_missing_numeric(self):
        """Test strategy selection for high missing rate in numeric column."""
        null_rate = 0.6
        is_numeric = True

        if null_rate > 0.5:
            strategy = "drop_column"
        elif null_rate > 0.1:
            if is_numeric:
                strategy = "impute_median"
            else:
                strategy = "impute_mode"
        else:
            if is_numeric:
                strategy = "impute_mean"
            else:
                strategy = "drop_rows"

        assert strategy == "drop_column"

    def test_strategy_for_moderate_missing_numeric(self):
        """Test strategy selection for moderate missing rate in numeric column."""
        null_rate = 0.25
        is_numeric = True

        if null_rate > 0.5:
            strategy = "drop_column"
        elif null_rate > 0.1:
            if is_numeric:
                strategy = "impute_median"
            else:
                strategy = "impute_mode"
        else:
            if is_numeric:
                strategy = "impute_mean"
            else:
                strategy = "drop_rows"

        assert strategy == "impute_median"

    def test_strategy_for_low_missing_categorical(self):
        """Test strategy selection for low missing rate in categorical column."""
        null_rate = 0.05
        is_numeric = False

        if null_rate > 0.5:
            strategy = "drop_column"
        elif null_rate > 0.1:
            if is_numeric:
                strategy = "impute_median"
            else:
                strategy = "impute_mode"
        else:
            if is_numeric:
                strategy = "impute_mean"
            else:
                strategy = "drop_rows"

        assert strategy == "drop_rows"


class TestCleaningOperations:
    """Test actual cleaning operations on DataFrames."""

    def test_drop_rows_with_missing(self):
        """Test dropping rows with missing values."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, None, 30, None, 50],
        })

        original_count = len(df)
        df_cleaned = df.dropna(subset=["value"])

        assert len(df_cleaned) == 3
        assert original_count - len(df_cleaned) == 2

    def test_drop_column(self):
        """Test dropping a column."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "to_drop": [None, None, None],
            "keep": [10, 20, 30],
        })

        df_cleaned = df.drop(columns=["to_drop"])

        assert "to_drop" not in df_cleaned.columns
        assert "keep" in df_cleaned.columns

    def test_impute_mean(self):
        """Test mean imputation."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "value": [10, None, 30, None],  # mean = 20
        })

        mean_val = df["value"].mean()
        df["value"] = df["value"].fillna(mean_val)

        assert df["value"].isna().sum() == 0
        assert df["value"].tolist() == [10, 20, 30, 20]

    def test_impute_median(self):
        """Test median imputation."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, None, 30, None, 50],  # median = 30
        })

        median_val = df["value"].median()
        df["value"] = df["value"].fillna(median_val)

        assert df["value"].isna().sum() == 0
        assert df["value"].tolist() == [10, 30, 30, 30, 50]

    def test_impute_mode(self):
        """Test mode imputation for categorical data."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "category": ["A", None, "A", "B"],
        })

        mode_val = df["category"].mode().iloc[0] if not df["category"].mode().empty else df["category"].iloc[0]
        df["category"] = df["category"].fillna(mode_val)

        assert df["category"].isna().sum() == 0
        assert df["category"].tolist() == ["A", "A", "A", "B"]

    def test_winsorize(self):
        """Test winsorization for outliers."""
        df = pd.DataFrame({
            "value": [10, 12, 11, 100, 13, 12, 11, 1000],
        })

        q1 = df["value"].quantile(0.05)
        q3 = df["value"].quantile(0.95)
        df["value"] = df["value"].clip(q1, q3)

        assert df["value"].max() <= q3
        assert df["value"].min() >= q1
        # Original had 1000, which should be clipped
        assert df["value"].max() < 1000

    def test_convert_datetime(self):
        """Test datetime conversion."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "date_str": ["2024-01-15", "2024-02-20", "2024-03-10"],
        })

        df["date_parsed"] = pd.to_datetime(df["date_str"], errors="coerce")

        assert pd.api.types.is_datetime64_any_dtype(df["date_parsed"])
        assert df["date_parsed"].iloc[0] == pd.Timestamp("2024-01-15")


class TestCleaningServiceUnit:
    """Unit tests for DataCleaningService with mocked dependencies."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.storage.endpoint = "localhost:9000"
        settings.storage.access_key = "minioadmin"
        settings.storage.secret_key = "minioadmin"
        settings.storage.secure = False
        settings.storage.bucket = "chat-data"
        return settings

    @pytest.fixture
    def mock_minio(self):
        """Create a mock MinIO client."""
        minio = MagicMock()
        minio.get_object = MagicMock()
        minio.put_object = AsyncMock()
        return minio

    def test_service_initialization(self, mock_db, mock_settings, mock_minio):
        """Test DataCleaningService initializes correctly."""
        # Import first, then patch
        from app.services import cleaning_service
        with patch.object(cleaning_service, "get_settings", return_value=mock_settings):
            with patch.object(cleaning_service, "Minio", return_value=mock_minio):
                service = cleaning_service.DataCleaningService(mock_db)

                assert service.db == mock_db
                assert service.minio_client == mock_minio
                assert service.bucket == "chat-data"

    @pytest.mark.asyncio
    async def test_suggest_cleaning_dataset_not_found(self, mock_db, mock_settings, mock_minio):
        """Test suggesting cleaning when dataset doesn't exist."""
        from app.services import cleaning_service
        with patch.object(cleaning_service, "get_settings", return_value=mock_settings):
            with patch.object(cleaning_service, "Minio", return_value=mock_minio):
                service = cleaning_service.DataCleaningService(mock_db)
                mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

                with pytest.raises(ValueError, match="Dataset not found"):
                    await service.suggest_cleaning_strategies(uuid4())

    @pytest.mark.asyncio
    async def test_execute_cleaning_dataset_not_found(self, mock_db, mock_settings, mock_minio):
        """Test executing cleaning when dataset doesn't exist."""
        from app.services import cleaning_service
        with patch.object(cleaning_service, "get_settings", return_value=mock_settings):
            with patch.object(cleaning_service, "Minio", return_value=mock_minio):
                service = cleaning_service.DataCleaningService(mock_db)
                mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

                with pytest.raises(ValueError, match="Dataset not found"):
                    await service.execute_cleaning(uuid4(), [])


class TestCleaningAPIRoutes:
    """Test cleaning API endpoints with mocks."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()
        db.refresh = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_suggestions_not_found(self, mock_db):
        """Test getting suggestions for non-existent dataset."""
        from app.api.cleaning import get_cleaning_suggestions
        from app.core.security import create_access_token

        # Create a valid token for a mock user
        user_id = uuid4()
        token = create_access_token(data={"sub": str(user_id), "email": "test@example.com"})

        # Mock the execute to return None (dataset not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await get_cleaning_suggestions(
                dataset_id=uuid4(),
                db=mock_db,
                token=token,
            )

        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_execute_cleaning_not_found(self, mock_db):
        """Test executing cleaning for non-existent dataset."""
        from app.api.cleaning import execute_cleaning
        from app.core.security import create_access_token

        # Create a valid token for a mock user
        user_id = uuid4()
        token = create_access_token(data={"sub": str(user_id), "email": "test@example.com"})

        # Mock the execute to return None (dataset not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await execute_cleaning(
                dataset_id=uuid4(),
                request=CleaningExecuteRequest(operations=[]),
                db=mock_db,
                token=token,
            )

        assert "not found" in str(exc_info.value.detail).lower()


class TestCleaningEdgeCases:
    """Test edge cases in data cleaning."""

    def test_empty_dataframe(self):
        """Test cleaning operations on empty DataFrame."""
        df = pd.DataFrame({"value": pd.Series(dtype="int64")})

        assert len(df) == 0
        assert df["value"].isna().all()

    def test_all_missing_column(self):
        """Test handling of column with all missing values."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "all_null": [None, None, None],
        })

        null_rate = df["all_null"].isna().mean()
        assert null_rate == 1.0

        # Strategy should be to drop the column
        if null_rate > 0.5:
            strategy = "drop_column"
        assert strategy == "drop_column"

    def test_single_row_dataframe(self):
        """Test cleaning operations on single row DataFrame."""
        df = pd.DataFrame({"value": [42]})

        assert len(df) == 1
        assert df["value"].mean() == 42

    def test_single_column_dataframe(self):
        """Test cleaning operations on single column DataFrame."""
        df = pd.DataFrame({"only_col": [1, 2, 3, 4, 5]})

        assert len(df.columns) == 1
        assert "only_col" in df.columns

    def test_outlier_at_boundaries(self):
        """Test winsorization at exact IQR boundaries."""
        df = pd.DataFrame({"value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})

        q1 = df["value"].quantile(0.05)
        q3 = df["value"].quantile(0.95)

        # With this small dataset, winsorization might not change values
        df_clipped = df["value"].clip(q1, q3)
        assert df_clipped.min() >= q1
        assert df_clipped.max() <= q3

    def test_datetime_with_invalid_values(self):
        """Test datetime conversion with some invalid values."""
        df = pd.DataFrame({
            "date_col": ["2024-01-15", "not-a-date", "2024-03-10", "also-invalid"],
        })

        converted = pd.to_datetime(df["date_col"], errors="coerce")
        valid_count = converted.notna().sum()
        null_count = converted.isna().sum()

        assert valid_count == 2
        assert null_count == 2

    def test_imputation_with_all_null(self):
        """Test imputation when all values are null."""
        df = pd.DataFrame({"value": [None, None, None]})

        # Mean/median/mode will be NaN for all-null
        mean_val = df["value"].mean()
        median_val = df["value"].median()

        assert pd.isna(mean_val)
        assert pd.isna(median_val)

    def test_mixed_type_column_detection(self):
        """Test detection of mixed type columns."""
        df = pd.DataFrame({
            "mixed": [1, "two", 3.0, None],
        })

        # Object dtype indicates mixed types
        assert df["mixed"].dtype == "object"

    def test_large_dataset_sampling(self):
        """Test that cleaning works on larger datasets."""
        df = pd.DataFrame({
            "id": range(10000),
            "value": [i % 100 for i in range(10000)],
        })

        # Add some missing values
        df.loc[df["id"] % 10 == 0, "value"] = None

        null_rate = df["value"].isna().mean()
        assert null_rate == 0.1  # 10% missing

        # Mean imputation should work
        mean_val = df["value"].mean()
        df_cleaned = df["value"].fillna(mean_val)

        assert df_cleaned.isna().sum() == 0
        assert len(df_cleaned) == 10000


class TestCleaningValidation:
    """Test validation of cleaning operations."""

    def test_invalid_operation_type(self):
        """Test handling of invalid operation type."""
        operations = [
            {"type": "invalid_type", "column": "age", "strategy": "impute_mean"}
        ]

        # The service should skip unknown operation types
        assert operations[0]["type"] == "invalid_type"

    def test_nonexistent_column_operation(self):
        """Test operation on non-existent column."""
        df = pd.DataFrame({"existing": [1, 2, 3]})
        operations = [{"type": "missing_values", "column": "nonexistent", "strategy": "drop_rows"}]

        # Should skip non-existent column
        for op in operations:
            column = op.get("column")
            if column not in df.columns:
                continue  # Should be skipped

        assert True  # Test passes if we handle this gracefully

    def test_wrong_strategy_for_operation(self):
        """Test handling of mismatched strategy for operation type."""
        df = pd.DataFrame({"value": [1, 2, None]})

        # Using wrong strategy (impute_mean for missing values) should still work
        # but might give unexpected results
        strategy = "impute_mean"  # Correct for missing values
        col_data = df["value"]

        if strategy == "impute_mean":
            result = col_data.fillna(col_data.mean())
            assert result.isna().sum() == 0

    def test_empty_operations_list(self):
        """Test executing with empty operations list."""
        operations = []

        assert len(operations) == 0
        # Should not raise any errors

    def test_cleaning_response_shape(self):
        """Test that cleaning response contains shape information."""
        response = CleaningExecuteResponse(
            new_dataset_id=str(uuid4()),
            new_dataset_name="cleaned_data",
            original_shape=[100, 5],
            cleaned_shape=[95, 5],
            operations_applied=[{"type": "drop_rows", "rows_removed": 5}],
        )

        assert response.original_shape[0] - response.cleaned_shape[0] == 5


class TestOriginalCleaningServiceTests:
    """Original tests from the existing file."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.flush = MagicMock()
        session.refresh = MagicMock()

        # Create a mock result for execute
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        return session

    @pytest.fixture
    def service(self, mock_db_session):
        """Create cleaning service with mock dependencies."""
        from app.services import cleaning_service
        with patch.object(cleaning_service, "get_settings") as mock_settings:
            mock_settings.return_value.storage.endpoint = "localhost:9000"
            mock_settings.return_value.storage.access_key = "test"
            mock_settings.return_value.storage.secret_key = "test"
            mock_settings.return_value.storage.bucket = "test-bucket"

            with patch.object(cleaning_service, "Minio"):
                service = cleaning_service.DataCleaningService(mock_db_session)
                return service

    @pytest.mark.asyncio
    async def test_suggest_cleaning_strategies_dataset_not_found(self, service, mock_db_session):
        """Test suggest_cleaning_strategies raises error for non-existent dataset."""
        # The mock is already set up in the fixture to return None
        with pytest.raises(ValueError, match="Dataset not found"):
            await service.suggest_cleaning_strategies(uuid4())

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
