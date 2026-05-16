import streamlit as st


USER_ID_KEY = "user_id"
USERNAME_KEY = "username"
USER_EMAIL_KEY = "user_email"
DATA_KEY_KEY = "data_key"
AUTHENTICATED_KEY = "is_authenticated"
SELECTED_DATASET_ID_KEY = "selected_dataset_id"
SELECTED_DATASET_NAME_KEY = "selected_dataset_name"

def login_user_session(
    user_id: int,
    username: str,
    email: str,
    data_key: bytes,
) -> None:
    """
    Saves authenticated user data in Streamlit session state.
    """
    st.session_state[AUTHENTICATED_KEY] = True
    st.session_state[USER_ID_KEY] = user_id
    st.session_state[USERNAME_KEY] = username
    st.session_state[USER_EMAIL_KEY] = email
    st.session_state[DATA_KEY_KEY] = data_key


def logout_user_session() -> None:
    """
    Clears authenticated user data from Streamlit session state.
    """
    keys_to_remove = [
        AUTHENTICATED_KEY,
        USER_ID_KEY,
        USERNAME_KEY,
        USER_EMAIL_KEY,
        DATA_KEY_KEY,
        SELECTED_DATASET_ID_KEY,
        SELECTED_DATASET_NAME_KEY,
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    """
    Checks if a user is currently authenticated.
    """
    return bool(st.session_state.get(AUTHENTICATED_KEY, False))


def get_current_user_id() -> int | None:
    """
    Returns current authenticated user id.
    """
    return st.session_state.get(USER_ID_KEY)


def get_current_username() -> str | None:
    """
    Returns current authenticated username.
    """
    return st.session_state.get(USERNAME_KEY)


def get_current_user_email() -> str | None:
    """
    Returns current authenticated user email.
    """
    return st.session_state.get(USER_EMAIL_KEY)


def get_current_data_key() -> bytes | None:
    """
    Returns current user's decrypted data key.
    """
    return st.session_state.get(DATA_KEY_KEY)

def set_selected_dataset(
    dataset_id: int,
    dataset_name: str,
) -> None:
    """
    Saves selected dataset in Streamlit session state.
    """
    st.session_state[SELECTED_DATASET_ID_KEY] = dataset_id
    st.session_state[SELECTED_DATASET_NAME_KEY] = dataset_name


def get_selected_dataset_id() -> int | None:
    """
    Returns currently selected dataset id.
    """
    return st.session_state.get(SELECTED_DATASET_ID_KEY)


def get_selected_dataset_name() -> str | None:
    """
    Returns currently selected dataset name.
    """
    return st.session_state.get(SELECTED_DATASET_NAME_KEY)


def clear_selected_dataset() -> None:
    """
    Clears selected dataset from Streamlit session state.
    """
    st.session_state.pop(SELECTED_DATASET_ID_KEY, None)
    st.session_state.pop(SELECTED_DATASET_NAME_KEY, None)