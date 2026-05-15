import streamlit as st

from app.auth.session import (
    get_current_user_email,
    get_current_username,
    logout_user_session,
)


def render_main_page() -> None:
    """
    Renders the main authenticated layout.
    """
    username = get_current_username()
    email = get_current_user_email()

    with st.sidebar:
        st.title("📊 App")

        st.write(f"Utilizator: **{username}**")
        st.caption(email)

        st.divider()

        selected_page = st.radio(
            "Navigare",
            options=[
                "Home",
                "Upload dataset",
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

    elif selected_page == "Upload dataset":
        render_placeholder_page(
            title="Upload dataset",
            message="Aici vom implementa încărcarea dataset-urilor criptate.",
        )

    elif selected_page == "Analysis":
        render_placeholder_page(
            title="Analysis",
            message="Aici vom construi pipeline-uri și vom rula metode de analiză.",
        )

    elif selected_page == "Results":
        render_placeholder_page(
            title="Results",
            message="Aici vom afișa pipeline runs, comparații și rezultate.",
        )

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
        - salvare cheie de date în sesiune;
        - structură de navigare pentru front-end;
        - backend pentru upload dataset, pipeline-uri, comparații și metode de analiză.
        """
    )

    st.info(
        "Următorul pas va fi pagina de upload dataset, apoi pagina de analysis."
    )


def render_placeholder_page(title: str, message: str) -> None:
    st.title(title)
    st.info(message)