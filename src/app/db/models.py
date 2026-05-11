from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    encryption_salt: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    encrypted_data_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    datasets: Mapped[list["Dataset"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    comparisons: Mapped[list["Comparison"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    encrypted_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="datasets",
    )

    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    comparisons: Mapped[list["Comparison"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )

    method_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    method_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    parameters_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )

    results_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="analysis_runs",
    )

    dataset: Mapped["Dataset"] = relationship(
        back_populates="analysis_runs",
    )


class Comparison(Base):
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )

    selected_runs_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    comparison_results_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="comparisons",
    )

    dataset: Mapped["Dataset"] = relationship(
        back_populates="comparisons",
    )