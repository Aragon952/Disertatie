import base64
import os

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


PBKDF2_ITERATIONS = 390_000


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)

    return password_hash.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a plain text password against a bcrypt hash.
    """
    password_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")

    return bcrypt.checkpw(password_bytes, hash_bytes)


def generate_encryption_salt() -> str:
    """
    Generates a random salt used for deriving the encryption key.
    """
    return base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")


def derive_password_key(password: str, encryption_salt: str) -> bytes:
    """
    Derives a Fernet-compatible key from the user's password and salt.

    This key is not used directly to encrypt files.
    It is used to encrypt/decrypt the user's data key.
    """
    salt = base64.urlsafe_b64decode(encryption_salt.encode("utf-8"))

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    return key


def generate_data_key() -> bytes:
    """
    Generates the real key used to encrypt/decrypt user files.
    """
    return Fernet.generate_key()


def encrypt_data_key(data_key: bytes, password_key: bytes) -> str:
    """
    Encrypts the user's data key using the password-derived key.
    """
    fernet = Fernet(password_key)
    encrypted_key = fernet.encrypt(data_key)

    return encrypted_key.decode("utf-8")


def decrypt_data_key(encrypted_data_key: str, password_key: bytes) -> bytes:
    """
    Decrypts the user's data key using the password-derived key.
    """
    fernet = Fernet(password_key)

    try:
        return fernet.decrypt(encrypted_data_key.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("Invalid password or corrupted encryption data.") from exc