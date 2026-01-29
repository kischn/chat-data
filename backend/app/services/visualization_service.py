"""Visualization service for generating charts."""
import io
import uuid
from typing import Any

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Dataset


class VisualizationService:
    """Service for generating data visualizations."""

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

    async def generate_chart(
        self,
        dataset_id: uuid.UUID,
        chart_type: str,
        x_column: str | None = None,
        y_column: str | None = None,
        title: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a chart for a dataset."""
        # Get dataset
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ValueError("Dataset not found")

        # Load data
        df = await self._load_data(dataset.file_path)

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Generate chart based on type
        chart_generators = {
            "bar": self._bar_chart,
            "line": self._line_chart,
            "scatter": self._scatter_chart,
            "histogram": self._histogram,
            "heatmap": self._heatmap,
            "pie": self._pie_chart,
        }

        generator = chart_generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        generator(ax, df, x_column, y_column, title, **kwargs)

        # Save to buffer
        chart_id = str(uuid.uuid4())
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)

        # Upload to MinIO
        object_path = f"charts/{chart_id}.png"
        self.minio_client.put_object(
            self.bucket,
            object_path,
            buffer,
            buffer.getbuffer().nbytes,
            content_type="image/png",
        )

        plt.close(fig)

        # Return chart info
        return {
            "chart_id": chart_id,
            "chart_type": chart_type,
            "url": f"/api/v1/charts/{chart_id}",
        }

    def _bar_chart(
        self,
        ax,
        df: pd.DataFrame,
        x_column: str | None,
        y_column: str | None,
        title: str | None,
        **kwargs,
    ):
        """Generate bar chart."""
        if x_column and y_column:
            df.groupby(x_column)[y_column].sum().plot(kind="bar", ax=ax)
        else:
            df.iloc[:, 0].value_counts().head(10).plot(kind="bar", ax=ax)
        ax.set_title(title or "Bar Chart")
        ax.set_xlabel(x_column or df.columns[0])
        ax.set_ylabel(y_column or "Count")
        plt.xticks(rotation=45)

    def _line_chart(
        self,
        ax,
        df: pd.DataFrame,
        x_column: str | None,
        y_column: str | None,
        title: str | None,
        **kwargs,
    ):
        """Generate line chart."""
        if x_column and y_column:
            df.plot(kind="line", x=x_column, y=y_column, ax=ax)
        else:
            df.select_dtypes(include=["number"]).iloc[:, :2].plot(kind="line", ax=ax)
        ax.set_title(title or "Line Chart")
        ax.set_xlabel(x_column or "Index")
        ax.set_ylabel(y_column or "Value")
        plt.xticks(rotation=45)

    def _scatter_chart(
        self,
        ax,
        df: pd.DataFrame,
        x_column: str | None,
        y_column: str | None,
        title: str | None,
        **kwargs,
    ):
        """Generate scatter chart."""
        if x_column and y_column:
            df.plot(kind="scatter", x=x_column, y=y_column, ax=ax, alpha=0.5)
        else:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) >= 2:
                df.plot(kind="scatter", x=numeric_cols[0], y=numeric_cols[1], ax=ax, alpha=0.5)
        ax.set_title(title or "Scatter Chart")

    def _histogram(
        self,
        ax,
        df: pd.DataFrame,
        x_column: str | None,
        y_column: str | None,
        title: str | None,
        bins: int = 30,
        **kwargs,
    ):
        """Generate histogram."""
        column = x_column or df.select_dtypes(include=["number"]).columns[0]
        df[column].hist(bins=bins, ax=ax, edgecolor="black")
        ax.set_title(title or f"Histogram of {column}")
        ax.set_xlabel(column)
        ax.set_ylabel("Frequency")

    def _heatmap(
        self,
        ax,
        df: pd.DataFrame,
        x_column: str | None,
        y_column: str | None,
        title: str | None,
        **kwargs,
    ):
        """Generate correlation heatmap."""
        numeric_df = df.select_dtypes(include=["number"])
        if numeric_df.empty:
            ax.text(0.5, 0.5, "No numeric columns for heatmap", ha="center")
            return

        corr = numeric_df.corr()
        im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)

        # Add labels
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr.columns)

        # Add correlation values
        for i in range(len(corr)):
            for j in range(len(corr)):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)

        ax.set_title(title or "Correlation Heatmap")
        plt.colorbar(im, ax=ax)

    def _pie_chart(
        self,
        ax,
        df: pd.DataFrame,
        x_column: str | None,
        y_column: str | None,
        title: str | None,
        **kwargs,
    ):
        """Generate pie chart."""
        column = x_column or df.columns[0]
        counts = df[column].value_counts().head(6)
        counts.plot(kind="pie", ax=ax, autopct="%1.1f%%")
        ax.set_title(title or f"Distribution of {column}")
        ax.set_ylabel("")

    async def get_chart(self, chart_id: str) -> tuple[bytes, str]:
        """Get chart image data and content type."""
        object_path = f"charts/{chart_id}.png"

        try:
            response = self.minio_client.get_object(self.bucket, object_path)
            content = response.read()
            return content, "image/png"
        except Exception:
            raise ValueError(f"Chart not found: {chart_id}")

    async def suggest_chart_types(
        self,
        dataset_id: uuid.UUID,
    ) -> list[dict[str, str]]:
        """Suggest appropriate chart types based on data."""
        from sqlalchemy import select
        from app.models import DatasetColumn

        result = await self.db.execute(
            select(DatasetColumn).where(DatasetColumn.dataset_id == dataset_id)
        )
        columns = result.scalars().all()

        suggestions = []

        # Check for datetime columns
        for col in columns:
            if col.data_type and "datetime" in col.data_type.lower():
                suggestions.append({
                    "type": "line",
                    "description": f"Time series for {col.name}",
                    "columns": {"x": col.name},
                })

        # Check for numeric columns
        numeric_cols = [col for col in columns if col.data_type and (
            "int" in col.data_type.lower() or "float" in col.data_type.lower()
        )]

        if len(numeric_cols) >= 2:
            suggestions.append({
                "type": "scatter",
                "description": "Relationship between numeric variables",
                "columns": {"x": numeric_cols[0].name, "y": numeric_cols[1].name},
            })

        # Check for categorical columns
        cat_cols = [col for col in columns if col.data_type == "object"]
        if cat_cols and numeric_cols:
            suggestions.append({
                "type": "bar",
                "description": f"{cat_cols[0].name} by {numeric_cols[0].name}",
                "columns": {"x": cat_cols[0].name, "y": numeric_cols[0].name},
            })

        # Correlation heatmap
        if len(numeric_cols) >= 3:
            suggestions.append({
                "type": "heatmap",
                "description": "Correlation matrix of numeric columns",
                "columns": {},
            })

        return suggestions
