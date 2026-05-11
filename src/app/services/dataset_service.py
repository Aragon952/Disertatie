from sqlalchemy.orm import Session

from app.db.crud import create_dataset, get_dataset_by_id, list_user_datasets
from app.db.models import Dataset
from app.storage.file_manager import delete_user_file, save_user_file


def upload_dataset(
    db: Session,
    user_id: int,
    original_filename: str,
    file_data: bytes,
    data_key: bytes,
) -> Dataset:
    """
    Saves an uploaded dataset as an encrypted file and stores its metadata in DB.
    """
    file_metadata = save_user_file(
        user_id=user_id,
        original_filename=original_filename,
        file_data=file_data,
        data_key=data_key,
    )

    dataset = create_dataset(
        db=db,
        user_id=user_id,
        original_filename=file_metadata["original_filename"],
        stored_filename=file_metadata["stored_filename"],
        encrypted_path=file_metadata["encrypted_path"],
        file_type=file_metadata["file_type"],
    )

    return dataset


def get_user_datasets(
    db: Session,
    user_id: int,
) -> list[Dataset]:
    """
    Returns all datasets uploaded by a user.
    """
    return list_user_datasets(db=db, user_id=user_id)


def get_dataset_for_user(
    db: Session,
    user_id: int,
    dataset_id: int,
) -> Dataset:
    """
    Returns a dataset only if it belongs to the current user.
    """
    dataset = get_dataset_by_id(db=db, dataset_id=dataset_id)

    if dataset is None:
        raise ValueError("Dataset not found.")

    if dataset.user_id != user_id:
        raise PermissionError("You do not have access to this dataset.")

    return dataset


def remove_dataset(
    db: Session,
    user_id: int,
    dataset_id: int,
) -> None:
    """
    Deletes the encrypted file from disk and removes the dataset metadata from DB.
    """
    dataset = get_dataset_for_user(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    delete_user_file(dataset.encrypted_path)

    db.delete(dataset)
    db.commit()