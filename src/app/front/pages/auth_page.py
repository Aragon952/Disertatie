import streamlit as st

from app.auth.session import login_user_session
from app.auth.user_service import authenticate_user, register_user
from app.db.base import SessionLocal


def render_auth_page() -> None:
    """
    Renders login/register page.
    """
    st.title("📊 Data Analysis Platform")
    st.write("Autentifică-te sau creează un cont pentru a continua.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        render_login_form()

    with tab_register:
        render_register_form()


def render_login_form() -> None:
    st.subheader("Login")

    with st.form("login_form"):
        username_or_email = st.text_input(
            "Username sau email",
            placeholder="exemplu: mihai sau mihai@email.com",
        )

        password = st.text_input(
            "Parolă",
            type="password",
        )

        submitted = st.form_submit_button("Login")

    if submitted:
        db = SessionLocal()

        try:
            authenticated_user = authenticate_user(
                db=db,
                username_or_email=username_or_email,
                password=password,
            )

            login_user_session(
                user_id=authenticated_user.user.id,
                username=authenticated_user.user.username,
                email=authenticated_user.user.email,
                data_key=authenticated_user.data_key,
            )

            st.success("Autentificare reușită.")
            st.rerun()

        except Exception as error:
            st.error(str(error))

        finally:
            db.close()


def render_register_form() -> None:
    st.subheader("Register")

    with st.form("register_form"):
        username = st.text_input(
            "Username",
            placeholder="Alege un username",
        )

        email = st.text_input(
            "Email",
            placeholder="exemplu@email.com",
        )

        password = st.text_input(
            "Parolă",
            type="password",
            help="Parola trebuie să aibă cel puțin 8 caractere.",
        )

        confirm_password = st.text_input(
            "Confirmă parola",
            type="password",
        )

        submitted = st.form_submit_button("Creează cont")

    if submitted:
        if password != confirm_password:
            st.error("Parolele nu coincid.")
            return

        db = SessionLocal()

        try:
            user = register_user(
                db=db,
                username=username,
                email=email,
                password=password,
            )

            st.success(
                f"Contul pentru utilizatorul '{user.username}' a fost creat. "
                "Te poți autentifica acum."
            )

        except Exception as error:
            st.error(str(error))

        finally:
            db.close()