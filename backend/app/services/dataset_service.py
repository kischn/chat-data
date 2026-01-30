"""Dataset service for handling uploads and metadata extraction."""
import os
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Dataset, DatasetColumn


class DatasetService:
    """Service for dataset operations."""

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

    async def upload_dataset(
        self,
        file: BinaryIO,
        user_id: uuid.UUID,
        name: str,
        description: str | None = None,
        is_public: bool = False,
    ) -> Dataset:
        """Upload and process a dataset file."""
        # Ensure bucket exists
        try:
            self.minio_client.bucket_exists(self.bucket)
        except Exception:
            self.minio_client.make_bucket(self.bucket)

        # Generate unique file path
        file_id = uuid.uuid4()
        file_ext = Path(name).suffix.lower()
        object_path = f"datasets/{user_id}/{file_id}{file_ext}"

        # Upload to MinIO
        file_content = await file.read()
        await self._upload_to_minio(object_path, file_content, file_ext)

        # Extract metadata
        metadata = await self._extract_metadata(BytesIO(file_content), file_ext)

        # Create dataset record
        dataset = Dataset(
            name=name,
            description=description,
            file_path=object_path,
            file_size=len(file_content),
            file_type=file_ext.lstrip("."),
            owner_id=user_id,
            is_public=is_public,
            extra_metadata={
                "columns": metadata["columns"],
                "row_count": metadata["row_count"],
            },
        )
        self.db.add(dataset)
        await self.db.flush()

        # Create column records
        for i, col in enumerate(metadata["columns"]):
            col_stats = metadata["statistics"].get(col, {})
            column = DatasetColumn(
                dataset_id=dataset.id,
                name=col,
                data_type=col_stats.get("dtype"),
                nullable=col_stats.get("null_count", 0) > 0,
                statistics=col_stats,
                sample_values=col_stats.get("sample_values", [])[:5],
                position=i,
            )
            self.db.add(column)

        await self.db.commit()
        await self.db.refresh(dataset)

        return dataset

    async def _upload_to_minio(
        self,
        object_path: str,
        content: bytes,
        file_ext: str,
    ):
        """Upload file to MinIO/S3."""
        content_type = {
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".json": "application/json",
        }.get(file_ext, "application/octet-stream")

        await self.minio_client.put_object(
            self.bucket,
            object_path,
            BytesIO(content),
            len(content),
            content_type=content_type,
        )

    async def _extract_metadata(
        self,
        file_content: BinaryIO,
        file_ext: str,
    ) -> dict:
        """Extract metadata from data file."""
        # Use first 1000 rows for sampling
        read_kwargs = {"nrows": 1000} if file_ext == ".csv" else {}

        if file_ext == ".csv":
            df = pd.read_csv(file_content, **read_kwargs)
        elif file_ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_content, **read_kwargs)
        elif file_ext == ".json":
            df = pd.read_json(file_content, **read_kwargs)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Get total row count (re-read full file)
        file_content.seek(0)
        if file_ext == ".csv":
            df_full = pd.read_csv(file_content)
        elif file_ext in [".xlsx", ".xls"]:
            df_full = pd.read_excel(file_content)
        elif file_ext == ".json":
            df_full = pd.read_json(file_content)
        else:
            df_full = df

        row_count = len(df_full)

        # Generate statistics for each column
        statistics = {}
        for col in df.columns:
            col_data = df[col]
            col_stats = {
                "dtype": str(col_data.dtype),
                "null_count": int(col_data.isna().sum()),
                "null_rate": float(col_data.isna().mean()),
                "unique_count": int(col_data.nunique()),
                "sample_values": col_data.dropna().head(5).tolist(),
            }

            # Numeric statistics
            if pd.api.types.is_numeric_dtype(col_data):
                col_stats.update({
                    "min": float(col_data.min()) if not col_data.empty else None,
                    "max": float(col_data.max()) if not col_data.empty else None,
                    "mean": float(col_data.mean()) if not col_data.empty else None,
                    "std": float(col_data.std()) if not col_data.empty else None,
                })

            statistics[col] = col_stats

        return {
            "columns": list(df.columns),
            "row_count": row_count,
            "statistics": statistics,
        }

    async def get_dataset_file(self, dataset_id: uuid.UUID) -> bytes:
        """Get dataset file content from storage."""
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ValueError("Dataset not found")

        response = self.minio_client.get_object(
            self.bucket,
            dataset.file_path,
        )
        return response.read()
