from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.auth.password import (
    decrypt_data_key,
    derive_password_key,
    encrypt_data_key,
    generate_data_key,
    generate_encryption_salt,
    hash_password,
    verify_password,
)
from app.db.crud import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.db.models import User


@dataclass
class AuthenticatedUser:
    """
    Object returned after successful authentication.
    """
    user: User
    data_key: bytes


def register_user(
    db: Session,
    username: str,
    email: str,
    password: str,
) -> User:
    """
    Registers a new user.

    Creates:
    - bcrypt password hash
    - encryption salt
    - random data key
    - encrypted data key
    """
    username = username.strip()
    email = email.strip().lower()

    if not username:
        raise ValueError("Username cannot be empty.")

    if not email:
        raise ValueError("Email cannot be empty.")

    if len(password) < 8:
        raise ValueError("Password must have at least 8 characters.")

    existing_username = get_user_by_username(db, username)
    if existing_username is not None:
        raise ValueError("Username already exists.")

    existing_email = get_user_by_email(db, email)
    if existing_email is not None:
        raise ValueError("Email already exists.")

    password_hash = hash_password(password)

    encryption_salt = generate_encryption_salt()
    password_key = derive_password_key(password, encryption_salt)

    data_key = generate_data_key()
    encrypted_data_key = encrypt_data_key(data_key, password_key)

    user = create_user(
        db=db,
        username=username,
        email=email,
        password_hash=password_hash,
        encryption_salt=encryption_salt,
        encrypted_data_key=encrypted_data_key,
    )

    return user


def authenticate_user(
    db: Session,
    username_or_email: str,
    password: str,
) -> AuthenticatedUser:
    """
    Authenticates a user by username or email.

    Returns the user and decrypted data key if login succeeds.
    """
    identifier = username_or_email.strip()

    if not identifier:
        raise ValueError("Username or email cannot be empty.")

    if "@" in identifier:
        user = get_user_by_email(db, identifier.lower())
    else:
        user = get_user_by_username(db, identifier)

    if user is None:
        raise ValueError("Invalid username/email or password.")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid username/email or password.")

    password_key = derive_password_key(password, user.encryption_salt)
    data_key = decrypt_data_key(user.encrypted_data_key, password_key)

    return AuthenticatedUser(
        user=user,
        data_key=data_key,
    )