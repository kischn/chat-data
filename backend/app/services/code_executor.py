"""Sandboxed code execution service for AI-generated Python code."""
import asyncio
import io
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Dataset


class CodeExecutor:
    """Sandboxed code execution environment for data analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        settings = get_settings()
        self.timeout = 60  # seconds
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.minio_client = Minio(
            settings.storage.endpoint,
            access_key=settings.storage.access_key,
            secret_key=settings.storage.secret_key,
            secure=settings.storage.secure,
        )
        self.bucket = settings.storage.bucket
        self.output_dir = Path("/tmp/visualizations")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(
        self,
        code: str,
        dataset_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Execute AI-generated code in sandboxed environment."""
        # Get dataset file path
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ValueError("Dataset not found")

        # Prepare execution context
        context = {
            "dataset_path": dataset.file_path,
            "dataset_id": str(dataset_id),
            "output_dir": str(self.output_dir),
            "conversation_id": str(conversation_id) if conversation_id else None,
        }

        # Run code in thread pool with timeout
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    lambda: self._safe_execute(code, context),
                ),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Execution timed out",
                "message": "Code execution exceeded 60 second timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(type(e).__name__),
                "message": str(e),
            }

    def _safe_execute(self, code: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute code with restricted globals."""
        import json
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        # Restricted globals - only allow safe operations
        safe_globals = {
            "pd": pd,
            "plt": plt,
            "np": np,
            "json": json,
            "print": lambda *args, **kwargs: None,  # Suppress output
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "isinstance": isinstance,
                "type": type,
            }
        }

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # Load dataset
        df = self._load_data(context["dataset_path"])

        # Execute code
        try:
            exec(code, safe_globals)
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

            # Check for generated visualizations
            charts = self._find_charts(context["output_dir"], context.get("conversation_id"))

            return {
                "success": True,
                "dataframe_info": {
                    "shape": list(df.shape),
                    "columns": list(df.columns),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                },
                "output": output if output else None,
                "charts": charts,
            }
        except Exception as e:
            sys.stdout = old_stdout()
            raise e

    def _load_data(self, file_path: str) -> pd.DataFrame:
        """Load dataset from MinIO."""
        response = self.minio_client.get_object(self.bucket, file_path)
        content = response.read()

        if file_path.endswith(".csv"):
            return pd.read_csv(io.BytesIO(content))
        elif file_path.endswith(".xlsx"):
            return pd.read_excel(io.BytesIO(content))
        elif file_path.endswith(".json"):
            return pd.read_json(io.BytesIO(content))
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    def _find_charts(self, output_dir: str, conversation_id: str | None) -> list[dict[str, Any]]:
        """Find and return generated chart files."""
        charts = []
        pattern = f"chart_*"
        if conversation_id:
            pattern = f"chart_{conversation_id}_*"

        path = Path(output_dir)
        for chart_path in path.glob(pattern):
            if chart_path.is_file():
                chart_id = str(uuid.uuid4())
                # Upload to MinIO
                self._upload_chart(chart_id, chart_path)
                # Clean up local file
                chart_path.unlink()

                charts.append({
                    "id": chart_id,
                    "type": "image",
                    "format": chart_path.suffix.lstrip("."),
                })

        return charts

    def _upload_chart(self, chart_id: str, chart_path: Path):
        """Upload chart to MinIO."""
        object_path = f"charts/{chart_id}{chart_path.suffix}"

        with open(chart_path, "rb") as f:
            self.minio_client.put_object(
                self.bucket,
                object_path,
                f,
                f.seek(0, 2),
                content_type=f"image/{chart_path.suffix.lstrip('.')}",
            )

    async def get_chart_url(self, chart_id: str) -> str:
        """Get presigned URL for a chart."""
        settings = get_settings()
        object_path = f"charts/{chart_id}"

        url = self.minio_client.presigned_get_object(
            self.bucket,
            object_path,
            expires=3600,  # 1 hour
        )

        return url
