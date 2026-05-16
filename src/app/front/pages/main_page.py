import streamlit as st

from app.auth.session import (
    get_current_user_email,
    get_current_username,
    get_selected_dataset_name,
    logout_user_session,
)
from app.front.pages.upload_page import render_upload_page
from app.front.pages.analysis_page import render_analysis_page
from app.front.pages.results_page import render_results_page

def render_main_page() -> None:
    """
    Renders the main authenticated layout.
    """
    username = get_current_username()
    email = get_current_user_email()
    selected_dataset_name = get_selected_dataset_name()

    with st.sidebar:
        st.title("📊 App")

        st.write(f"Utilizator: **{username}**")
        st.caption(email)

        if selected_dataset_name:
            st.success(f"Dataset: {selected_dataset_name}")
        else:
            st.warning("Niciun dataset selectat")

        st.divider()

        selected_page = st.radio(
            "Navigare",
            options=[
                "Home",
                "Datasets",
                "Analysis",
                "Results",
                "Settings",
            ],
        )

        st.divider()

        if st.button("Logout"):
            logout_user_session()
            st.rerun()

    if selected_page == "Home":
        render_home_page()

    elif selected_page == "Datasets":
        render_upload_page()

    elif selected_page == "Analysis":
        render_analysis_page()

    elif selected_page == "Results":
        render_results_page()

    elif selected_page == "Settings":
        render_placeholder_page(
            title="Settings",
            message="Aici vor fi setări ale aplicației.",
        )


def render_home_page() -> None:
    st.title("Dashboard")

    st.write(
        """
        Bine ai venit în aplicația ta de analiză comparativă a datelor.

        Momentan sunt disponibile:
        - autentificare și înregistrare utilizatori;
        - upload dataset criptat local;
        - selectare dataset curent;
        - preview dataset;
        - backend pentru pipeline-uri, metode de analiză și comparații.
        """
    )

    selected_dataset_name = get_selected_dataset_name()

    if selected_dataset_name:
        st.success(f"Dataset curent: {selected_dataset_name}")
    else:
        st.info("Mergi la pagina Datasets pentru a selecta sau încărca un dataset.")


def render_placeholder_page(title: str, message: str) -> None:
    st.title(title)
    st.info(message)

