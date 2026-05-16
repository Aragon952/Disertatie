import os

import streamlit as st

from app.auth.session import (
    get_current_user_email,
    get_current_user_id,
    get_current_username,
    get_selected_dataset_id,
    get_selected_dataset_name,
)
from app.db.base import SessionLocal
from app.db.crud import (
    list_comparisons_for_dataset,
    list_pipeline_runs_for_dataset,
    list_user_datasets,
)
from app.services.openai_service import is_openai_configured, get_openai_model


def render_settings_page() -> None:
    """
    Renders a simple settings/about page for the application.
    """
    st.title("Settings")

    user_id = get_current_user_id()
    username = get_current_username()
    email = get_current_user_email()

    if user_id is None:
        st.error("Nu există utilizator autentificat.")
        return

    render_user_section(
        user_id=user_id,
        username=username,
        email=email,
    )

    st.divider()

    render_dataset_section(user_id=user_id)

    st.divider()

    render_openai_section()

    st.divider()

    render_application_section()


def render_user_section(
    user_id: int,
    username: str | None,
    email: str | None,
) -> None:
    st.subheader("Utilizator curent")

    col_id, col_username, col_email = st.columns(3)

    with col_id:
        st.metric("User ID", user_id)

    with col_username:
        st.metric("Username", username or "-")

    with col_email:
        st.metric("Email", email or "-")


def render_dataset_section(user_id: int) -> None:
    st.subheader("Dataseturi și rezultate")

    selected_dataset_id = get_selected_dataset_id()
    selected_dataset_name = get_selected_dataset_name()

    db = SessionLocal()

    try:
        datasets = list_user_datasets(
            db=db,
            user_id=user_id,
        )

        pipeline_runs_count = 0
        comparisons_count = 0

        if selected_dataset_id is not None:
            pipeline_runs = list_pipeline_runs_for_dataset(
                db=db,
                user_id=user_id,
                dataset_id=selected_dataset_id,
            )

            comparisons = list_comparisons_for_dataset(
                db=db,
                user_id=user_id,
                dataset_id=selected_dataset_id,
            )

            pipeline_runs_count = len(pipeline_runs)
            comparisons_count = len(comparisons)

        col_datasets, col_runs, col_comparisons = st.columns(3)

        with col_datasets:
            st.metric("Dataseturi încărcate", len(datasets))

        with col_runs:
            st.metric("Pipeline runs pentru datasetul curent", pipeline_runs_count)

        with col_comparisons:
            st.metric("Comparații pentru datasetul curent", comparisons_count)

        if selected_dataset_id is None:
            st.info("Nu ai selectat încă un dataset curent.")
        else:
            st.success(
                f"Dataset curent: **{selected_dataset_name}** "
                f"(id={selected_dataset_id})"
            )

    finally:
        db.close()


def render_openai_section() -> None:
    st.subheader("OpenAI API")

    configured = is_openai_configured()
    model = get_openai_model()

    col_status, col_model = st.columns(2)

    with col_status:
        if configured:
            st.success("OPENAI_API_KEY este configurat.")
        else:
            st.warning("OPENAI_API_KEY nu este configurat.")

    with col_model:
        st.metric("Model configurat", model)

    if not configured:
        st.info(
            "Aplicația funcționează și fără OpenAI API. "
            "Interpretarea AI a comparațiilor este disponibilă doar după configurarea cheii."
        )

    with st.expander("Cum configurezi OpenAI API", expanded=False):
        st.write(
            """
            În PowerShell, pentru sesiunea curentă:

            ```powershell
            $env:OPENAI_API_KEY="cheia_ta_aici"
            $env:OPENAI_MODEL="gpt-5.5"
            streamlit run src/app/main.py
            ```

            Dacă nu setezi `OPENAI_MODEL`, aplicația folosește modelul default definit în `openai_service.py`.
            """
        )


def render_application_section() -> None:
    st.subheader("Despre aplicație")

    st.write(
        """
        Această aplicație permite utilizatorilor să încarce dataseturi criptate local,
        să ruleze pipeline-uri de analiză a datelor și să compare rezultatele obținute.
        """
    )

    st.write(
        """
        Funcționalități implementate:
        - autentificare și înregistrare utilizatori;
        - stocare locală criptată a dataseturilor;
        - metadata salvată în SQLite;
        - pipeline builder generic;
        - pași de preprocessing, statistici și outlier detection;
        - metrici generale de pipeline;
        - comparații între pipeline runs;
        - interpretare AI opțională pentru comparații.
        """
    )

    st.caption(
        f"Working directory: {os.getcwd()}"
    )