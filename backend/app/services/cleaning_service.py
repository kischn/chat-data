"""Data cleaning and preprocessing service."""
import uuid
from io import BytesIO
from typing import Any

import pandas as pd
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Dataset, DatasetColumn


class DataCleaningService:
    """AI-assisted data cleaning service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        settings = get_settings()
        self.minio_client = Minio(
            settings.storage.endpoint,
            access_key=settings.storage.access_key,
            secret_key=settings.storage.secret_key,
            secure=settings.storage.secure,
        )
        self.bucket = settings.storage.bucket

    async def suggest_cleaning_strategies(
        self,
        dataset_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Analyze data and suggest cleaning strategies."""
        # Get dataset info
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ValueError("Dataset not found")

        # Get column metadata
        result = await self.db.execute(
            select(DatasetColumn)
            .where(DatasetColumn.dataset_id == dataset_id)
            .order_by(DatasetColumn.position)
        )
        columns = result.scalars().all()

        # Load data for analysis
        df = await self._load_data(dataset.file_path)

        suggestions = []
        for col in columns:
            if col.name not in df.columns:
                continue

            col_data = df[col.name]
            col_stats = col.statistics or {}
            issues = []

            # Missing values
            if col_stats.get("null_rate", 0) > 0:
                null_rate = col_stats["null_rate"]
                if null_rate > 0.5:
                    strategy = "drop_column"
                    reason = f"Missing {null_rate:.1%} of values - too many to impute"
                elif null_rate > 0.1:
                    if pd.api.types.is_numeric_dtype(col_data):
                        strategy = "impute_median"
                        reason = "Moderate missing rate - use median to resist outliers"
                    else:
                        strategy = "impute_mode"
                        reason = "Moderate missing rate - use mode for categorical"
                else:
                    if pd.api.types.is_numeric_dtype(col_data):
                        strategy = "impute_mean"
                        reason = "Low missing rate - mean imputation is appropriate"
                    else:
                        strategy = "drop_rows"
                        reason = "Low missing rate - drop affected rows"

                issues.append({
                    "type": "missing_values",
                    "column": col.name,
                    "rate": null_rate,
                    "strategy": strategy,
                    "reason": reason,
                })

            # Outliers (numeric columns)
            if pd.api.types.is_numeric_dtype(col_data) and col_data.notna().any():
                q1 = col_data.quantile(0.25)
                q3 = col_data.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = ((col_data < lower) | (col_data > upper)).sum()
                outlier_rate = outliers / len(col_data) if len(col_data) > 0 else 0

                if outlier_rate > 0.01:
                    issues.append({
                        "type": "outliers",
                        "column": col.name,
                        "count": int(outliers),
                        "rate": float(outlier_rate),
                        "strategy": "winsorize",
                        "reason": f"{outlier_rate:.1%} outliers detected - winsorize to cap extreme values",
                    })

            # Data type issues
            if col.data_type == "object":
                # Check for mixed types or datetime
                try:
                    pd.to_datetime(col_data.dropna().head(100), errors="raise")
                    issues.append({
                        "type": "data_type",
                        "column": col.name,
                        "issue": "potential_datetime",
                        "strategy": "convert_datetime",
                        "reason": "Column appears to contain datetime values",
                    })
                except Exception:
                    pass

            if issues:
                suggestions.extend(issues)

        return {
            "dataset_id": str(dataset_id),
            "dataset_name": dataset.name,
            "row_count": len(df),
            "column_count": len(columns),
            "suggestions": suggestions,
        }

    async def execute_cleaning(
        self,
        dataset_id: uuid.UUID,
        operations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute cleaning operations on dataset."""
        # Get dataset
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ValueError("Dataset not found")

        # Load data
        df = await self._load_data(dataset.file_path)
        original_shape = df.shape

        # Track operations
        operations_applied = []

        for op in operations:
            op_type = op.get("type")
            column = op.get("column")
            strategy = op.get("strategy")

            if column not in df.columns:
                continue

            col_data = df[column]

            if op_type == "missing_values":
                if strategy == "drop_rows":
                    mask = col_data.isna()
                    df.dropna(subset=[column], inplace=True)
                    operations_applied.append({
                        "type": "drop_rows",
                        "column": column,
                        "rows_removed": int(mask.sum()),
                    })
                elif strategy == "drop_column":
                    df.drop(columns=[column], inplace=True)
                    operations_applied.append({
                        "type": "drop_column",
                        "column": column,
                    })
                elif strategy == "impute_mean":
                    df[column] = col_data.fillna(col_data.mean())
                    operations_applied.append({
                        "type": "impute",
                        "column": column,
                        "strategy": "mean",
                    })
                elif strategy == "impute_median":
                    df[column] = col_data.fillna(col_data.median())
                    operations_applied.append({
                        "type": "impute",
                        "column": column,
                        "strategy": "median",
                    })
                elif strategy == "impute_mode":
                    mode_val = col_data.mode().iloc[0] if not col_data.mode().empty else col_data.iloc[0]
                    df[column] = col_data.fillna(mode_val)
                    operations_applied.append({
                        "type": "impute",
                        "column": column,
                        "strategy": "mode",
                    })

            elif op_type == "outliers":
                if strategy == "winsorize":
                    q1 = col_data.quantile(0.05)
                    q3 = col_data.quantile(0.95)
                    df[column] = col_data.clip(q1, q3)
                    operations_applied.append({
                        "type": "winsorize",
                        "column": column,
                    })

            elif op_type == "data_type":
                if strategy == "convert_datetime":
                    df[column] = pd.to_datetime(col_data, errors="coerce")
                    operations_applied.append({
                        "type": "convert_datetime",
                        "column": column,
                    })

        # Save cleaned data
        file_id = uuid.uuid4()
        new_path = f"datasets/{dataset.owner_id}/{file_id}_cleaned.csv"

        await self._save_data(new_path, df)

        # Create new dataset record
        new_dataset = Dataset(
            name=f"{dataset.name} (cleaned)",
            description=f"Cleaned version of {dataset.name}",
            file_path=new_path,
            file_size=0,
            file_type="csv",
            owner_id=dataset.owner_id,
            team_id=dataset.team_id,
            is_public=False,
            metadata={
                "source_dataset_id": str(dataset_id),
                "operations_applied": operations_applied,
                "original_shape": list(original_shape),
                "cleaned_shape": list(df.shape),
            },
        )
        self.db.add(new_dataset)
        await self.db.commit()
        await self.db.refresh(new_dataset)

        return {
            "new_dataset_id": str(new_dataset.id),
            "new_dataset_name": new_dataset.name,
            "original_shape": list(original_shape),
            "cleaned_shape": list(df.shape),
            "operations_applied": operations_applied,
        }

    async def _load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from MinIO."""
        response = self.minio_client.get_object(self.bucket, file_path)
        content = response.read()

        if file_path.endswith(".csv"):
            return pd.read_csv(BytesIO(content))
        elif file_path.endswith(".xlsx"):
            return pd.read_excel(BytesIO(content))
        elif file_path.endswith(".json"):
            return pd.read_json(BytesIO(content))
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    async def _save_data(self, file_path: str, df: pd.DataFrame):
        """Save data to MinIO."""
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)

        self.minio_client.put_object(
            self.bucket,
            file_path,
            buffer,
            buffer.getbuffer().nbytes,
            content_type="text/csv",
        )
