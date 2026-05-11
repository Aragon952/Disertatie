from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[3]

DATA_DIR = BASE_DIR / "data"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'app.db'}",
)

USER_STORAGE_DIR = Path(
    os.getenv(
        "USER_STORAGE_DIR",
        str(DATA_DIR / "users"),
    )
)

if not USER_STORAGE_DIR.is_absolute():
    USER_STORAGE_DIR = BASE_DIR / USER_STORAGE_DIR

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

APP_ENV = os.getenv("APP_ENV", "development")

ALLOWED_FILE_TYPES = {".csv", ".xlsx", ".json"}

MAX_UPLOAD_SIZE_MB = 50


def ensure_directories_exist() -> None:
    """
    Creates the local folders required by the application.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def is_development() -> bool:
    """
    Returns True if the app runs in development mode.
    """
    return APP_ENV.lower() == "development"