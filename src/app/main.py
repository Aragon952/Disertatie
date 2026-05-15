import streamlit as st

from app.auth.session import is_authenticated
from app.front.pages.auth_page import render_auth_page
from app.front.pages.main_page import render_main_page


def main() -> None:
    st.set_page_config(
        page_title="Data Analysis App",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if is_authenticated():
        render_main_page()
    else:
        render_auth_page()


if __name__ == "__main__":
    main()