from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


def encrypt_bytes(data: bytes, data_key: bytes) -> bytes:
    """
    Encrypts raw bytes using the user's data key.
    """
    fernet = Fernet(data_key)
    return fernet.encrypt(data)


def decrypt_bytes(encrypted_data: bytes, data_key: bytes) -> bytes:
    """
    Decrypts raw bytes using the user's data key.
    """
    fernet = Fernet(data_key)

    try:
        return fernet.decrypt(encrypted_data)
    except InvalidToken as exc:
        raise ValueError("Could not decrypt file. Invalid key or corrupted file.") from exc


def save_encrypted_file(
    source_data: bytes,
    destination_path: Path,
    data_key: bytes,
) -> None:
    """
    Encrypts source bytes and saves them to disk.
    """
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    encrypted_data = encrypt_bytes(source_data, data_key)

    with destination_path.open("wb") as file:
        file.write(encrypted_data)


def load_encrypted_file(
    file_path: Path,
    data_key: bytes,
) -> bytes:
    """
    Loads encrypted bytes from disk and decrypts them.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    encrypted_data = file_path.read_bytes()

    return decrypt_bytes(encrypted_data, data_key)