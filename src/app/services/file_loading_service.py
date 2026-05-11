from io import BytesIO, StringIO

import pandas as pd
from sqlalchemy.orm import Session

from app.db.models import Dataset
from app.services.dataset_service import get_dataset_for_user
from app.storage.file_manager import load_user_file


def load_dataset_bytes(
    db: Session,
    user_id: int,
    dataset_id: int,
    data_key: bytes,
) -> bytes:
    """
    Loads and decrypts a dataset file for the current user.
    """
    dataset = get_dataset_for_user(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    return load_user_file(
        encrypted_path=dataset.encrypted_path,
        data_key=data_key,
    )


def dataframe_from_bytes(
    file_data: bytes,
    file_type: str,
) -> pd.DataFrame:
    """
    Converts raw decrypted file bytes into a pandas DataFrame.
    """
    file_type = file_type.lower()

    if file_type == ".csv":
        text_data = file_data.decode("utf-8")
        return pd.read_csv(StringIO(text_data))

    if file_type == ".xlsx":
        return pd.read_excel(BytesIO(file_data))

    if file_type == ".json":
        text_data = file_data.decode("utf-8")
        return pd.read_json(StringIO(text_data))

    raise ValueError(f"Unsupported file type: {file_type}")


def load_dataset_as_dataframe(
    db: Session,
    user_id: int,
    dataset_id: int,
    data_key: bytes,
) -> pd.DataFrame:
    """
    Loads a user's encrypted dataset and returns it as a pandas DataFrame.
    """
    dataset = get_dataset_for_user(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    file_data = load_user_file(
        encrypted_path=dataset.encrypted_path,
        data_key=data_key,
    )

    return dataframe_from_bytes(
        file_data=file_data,
        file_type=dataset.file_type,
    )


def get_dataframe_preview(
    dataframe: pd.DataFrame,
    rows: int = 5,
) -> dict:
    """
    Returns a lightweight preview useful for UI display.
    """
    return {
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "column_names": list(dataframe.columns),
        "dtypes": {
            column: str(dtype)
            for column, dtype in dataframe.dtypes.items()
        },
        "preview": dataframe.head(rows).to_dict(orient="records"),
    }


def load_dataset_preview(
    db: Session,
    user_id: int,
    dataset_id: int,
    data_key: bytes,
    rows: int = 5,
) -> dict:
    """
    Loads a dataset and returns metadata + preview.
    """
    dataframe = load_dataset_as_dataframe(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        data_key=data_key,
    )

    return get_dataframe_preview(
        dataframe=dataframe,
        rows=rows,
    )