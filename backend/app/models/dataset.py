"""Dataset models."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dataset(Base):
    """Dataset model."""

    __tablename__ = "datasets"

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    owner_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="datasets")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="datasets")
    columns: Mapped[list["DatasetColumn"]] = relationship(
        "DatasetColumn", back_populates="dataset", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetColumn(Base):
    """Dataset column metadata."""

    __tablename__ = "dataset_columns"

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    dataset_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sample_values: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="columns")


# Import User and Team for relationship annotations (avoiding circular import)
from app.models import User, Team  # noqa: E402, F401
