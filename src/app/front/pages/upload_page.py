import pandas as pd
import streamlit as st

from app.auth.session import (
    get_current_data_key,
    get_current_user_id,
    get_selected_dataset_id,
    get_selected_dataset_name,
    set_selected_dataset,
)
from app.db.base import SessionLocal
from app.services.dataset_service import get_user_datasets, upload_dataset
from app.services.file_loading_service import load_dataset_preview


def render_upload_page() -> None:
    """
    Renders dataset selection and upload page.
    """
    st.title("Datasets")

    user_id = get_current_user_id()
    data_key = get_current_data_key()

    if user_id is None or data_key is None:
        st.error("Nu există utilizator autentificat sau cheia de date lipsește.")
        return

    db = SessionLocal()

    try:
        render_selected_dataset_info()

        st.divider()

        render_existing_datasets_section(
            db=db,
            user_id=user_id,
            data_key=data_key,
        )

        st.divider()

        render_upload_dataset_section(
            db=db,
            user_id=user_id,
            data_key=data_key,
        )

    finally:
        db.close()


def render_selected_dataset_info() -> None:
    """
    Displays currently selected dataset.
    """
    selected_dataset_id = get_selected_dataset_id()
    selected_dataset_name = get_selected_dataset_name()

    if selected_dataset_id is None:
        st.info("Nu ai selectat încă niciun dataset.")
        return

    st.success(
        f"Dataset selectat: **{selected_dataset_name}** "
        f"(id={selected_dataset_id})"
    )


def render_existing_datasets_section(
    db,
    user_id: int,
    data_key: bytes,
) -> None:
    """
    Shows existing datasets and allows user to select one.
    """
    st.subheader("Dataset-uri existente")

    datasets = get_user_datasets(
        db=db,
        user_id=user_id,
    )

    if not datasets:
        st.warning("Nu ai încă dataset-uri încărcate.")
        return

    dataset_options = {
        f"{dataset.original_filename} | id={dataset.id}": dataset
        for dataset in datasets
    }

    selected_label = st.selectbox(
        "Selectează un dataset",
        options=list(dataset_options.keys()),
    )

    selected_dataset = dataset_options[selected_label]

    col_select, col_preview = st.columns([1, 1])

    with col_select:
        if st.button("Setează ca dataset curent"):
            set_selected_dataset(
                dataset_id=selected_dataset.id,
                dataset_name=selected_dataset.original_filename,
            )
            st.success(
                f"Datasetul '{selected_dataset.original_filename}' a fost selectat."
            )
            st.rerun()

    with col_preview:
        show_preview = st.button("Afișează preview")

    if show_preview:
        render_dataset_preview(
            db=db,
            user_id=user_id,
            dataset_id=selected_dataset.id,
            data_key=data_key,
        )


def render_dataset_preview(
    db,
    user_id: int,
    dataset_id: int,
    data_key: bytes,
) -> None:
    """
    Loads and displays dataset preview.
    """
    try:
        preview = load_dataset_preview(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
            data_key=data_key,
            rows=5,
        )

        st.write("Preview dataset")

        col_rows, col_columns = st.columns(2)

        with col_rows:
            st.metric("Rows", preview["rows"])

        with col_columns:
            st.metric("Columns", preview["columns"])

        st.write("Coloane:")
        st.write(", ".join(preview["column_names"]))

        st.write("Tipuri de date:")
        st.json(preview["dtypes"])

        preview_dataframe = pd.DataFrame(preview["preview"])
        st.dataframe(
            preview_dataframe,
            width="stretch",
        )

    except Exception as error:
        st.error(f"Nu am putut încărca preview-ul datasetului: {error}")


def render_upload_dataset_section(
    db,
    user_id: int,
    data_key: bytes,
) -> None:
    """
    Handles new dataset upload.
    """
    st.subheader("Încarcă dataset nou")

    uploaded_file = st.file_uploader(
        "Alege un fișier",
        type=["csv", "xlsx", "json"],
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.caption("Formate acceptate: CSV, XLSX, JSON.")
        return

    st.write("Fișier selectat:")
    st.write(f"**{uploaded_file.name}**")

    if st.button("Încarcă dataset"):
        try:
            file_data = uploaded_file.getvalue()

            dataset = upload_dataset(
                db=db,
                user_id=user_id,
                original_filename=uploaded_file.name,
                file_data=file_data,
                data_key=data_key,
            )

            set_selected_dataset(
                dataset_id=dataset.id,
                dataset_name=dataset.original_filename,
            )

            st.success(
                f"Datasetul '{dataset.original_filename}' a fost încărcat și selectat."
            )

            st.rerun()

        except Exception as error:
            st.error(f"Upload eșuat: {error}")