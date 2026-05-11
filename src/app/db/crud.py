import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRun, Comparison, Dataset, User


def create_user(
    db: Session,
    username: str,
    email: str,
    password_hash: str,
    encryption_salt: str,
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        encryption_salt=encryption_salt,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.scalar(statement)


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def create_dataset(
    db: Session,
    user_id: int,
    original_filename: str,
    stored_filename: str,
    encrypted_path: str,
    file_type: str,
) -> Dataset:
    dataset = Dataset(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        encrypted_path=encrypted_path,
        file_type=file_type,
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


def get_dataset_by_id(db: Session, dataset_id: int) -> Dataset | None:
    statement = select(Dataset).where(Dataset.id == dataset_id)
    return db.scalar(statement)


def list_user_datasets(db: Session, user_id: int) -> list[Dataset]:
    statement = (
        select(Dataset)
        .where(Dataset.user_id == user_id)
        .order_by(Dataset.uploaded_at.desc())
    )

    return list(db.scalars(statement).all())


def create_analysis_run(
    db: Session,
    user_id: int,
    dataset_id: int,
    method_name: str,
    method_category: str,
    parameters: dict[str, Any] | None = None,
    results: dict[str, Any] | None = None,
) -> AnalysisRun:
    analysis_run = AnalysisRun(
        user_id=user_id,
        dataset_id=dataset_id,
        method_name=method_name,
        method_category=method_category,
        parameters_json=json.dumps(parameters or {}),
        results_json=json.dumps(results or {}),
    )

    db.add(analysis_run)
    db.commit()
    db.refresh(analysis_run)

    return analysis_run


def list_analysis_runs_for_dataset(
    db: Session,
    user_id: int,
    dataset_id: int,
) -> list[AnalysisRun]:
    statement = (
        select(AnalysisRun)
        .where(
            AnalysisRun.user_id == user_id,
            AnalysisRun.dataset_id == dataset_id,
        )
        .order_by(AnalysisRun.created_at.desc())
    )

    return list(db.scalars(statement).all())


def create_comparison(
    db: Session,
    user_id: int,
    dataset_id: int,
    selected_run_ids: list[int],
    comparison_results: dict[str, Any],
    ai_summary: str | None = None,
) -> Comparison:
    comparison = Comparison(
        user_id=user_id,
        dataset_id=dataset_id,
        selected_runs_json=json.dumps(selected_run_ids),
        comparison_results_json=json.dumps(comparison_results),
        ai_summary=ai_summary,
    )

    db.add(comparison)
    db.commit()
    db.refresh(comparison)

    return comparison


def list_comparisons_for_dataset(
    db: Session,
    user_id: int,
    dataset_id: int,
) -> list[Comparison]:
    statement = (
        select(Comparison)
        .where(
            Comparison.user_id == user_id,
            Comparison.dataset_id == dataset_id,
        )
        .order_by(Comparison.created_at.desc())
    )

    return list(db.scalars(statement).all())   