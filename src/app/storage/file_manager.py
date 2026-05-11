from pathlib import Path
from uuid import uuid4

from app.config.settings import ALLOWED_FILE_TYPES, USER_STORAGE_DIR
from app.storage.encrypted_storage import load_encrypted_file, save_encrypted_file


def get_user_storage_dir(user_id: int) -> Path:
    """
    Returns the local storage directory for a specific user.
    """
    user_dir = USER_STORAGE_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    return user_dir


def get_file_extension(filename: str) -> str:
    """
    Returns the lowercase extension of a filename.
    """
    return Path(filename).suffix.lower()


def validate_file_type(filename: str) -> None:
    """
    Validates that the uploaded file type is allowed.
    """
    extension = get_file_extension(filename)

    if extension not in ALLOWED_FILE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_FILE_TYPES))
        raise ValueError(f"File type not allowed. Allowed types: {allowed}")


def generate_stored_filename(original_filename: str) -> str:
    """
    Generates a safe unique filename for encrypted local storage.
    """
    extension = get_file_extension(original_filename)
    return f"{uuid4().hex}{extension}.enc"


def save_user_file(
    user_id: int,
    original_filename: str,
    file_data: bytes,
    data_key: bytes,
) -> dict[str, str]:
    """
    Validates, encrypts and saves a user's uploaded file.

    Returns metadata that can be saved in the database.
    """
    validate_file_type(original_filename)

    user_dir = get_user_storage_dir(user_id)
    stored_filename = generate_stored_filename(original_filename)
    encrypted_path = user_dir / stored_filename

    save_encrypted_file(
        source_data=file_data,
        destination_path=encrypted_path,
        data_key=data_key,
    )

    return {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "encrypted_path": str(encrypted_path),
        "file_type": get_file_extension(original_filename),
    }


def load_user_file(
    encrypted_path: str,
    data_key: bytes,
) -> bytes:
    """
    Loads and decrypts a user's saved file.
    """
    return load_encrypted_file(
        file_path=Path(encrypted_path),
        data_key=data_key,
    )


def delete_user_file(encrypted_path: str) -> None:
    """
    Deletes an encrypted file from local storage.
    """
    file_path = Path(encrypted_path)

    if file_path.exists():
        file_path.unlink()