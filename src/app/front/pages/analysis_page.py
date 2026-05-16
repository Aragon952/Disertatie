import json
from typing import Any

import pandas as pd
import streamlit as st

from app.analysis_methods.registry import list_steps_metadata
from app.auth.session import (
    get_current_data_key,
    get_current_user_id,
    get_selected_dataset_id,
    get_selected_dataset_name,
)
from app.db.base import SessionLocal
from app.services.analysis_service import run_pipeline_and_save
from app.services.file_loading_service import load_dataset_as_dataframe


CURRENT_PIPELINE_KEY = "current_pipeline_steps"
LAST_PIPELINE_RESULTS_KEY = "last_pipeline_results"


def render_analysis_page() -> None:
    """
    Renders the pipeline builder and runner page.
    """
    st.title("Analysis")

    user_id = get_current_user_id()
    data_key = get_current_data_key()
    selected_dataset_id = get_selected_dataset_id()
    selected_dataset_name = get_selected_dataset_name()

    if user_id is None or data_key is None:
        st.error("Nu există utilizator autentificat sau cheia de date lipsește.")
        return

    if selected_dataset_id is None:
        st.warning("Nu ai selectat niciun dataset.")
        st.info("Mergi la pagina Datasets și selectează sau încarcă un dataset.")
        return

    initialize_pipeline_state()

    st.success(
        f"Dataset curent: **{selected_dataset_name}** "
        f"(id={selected_dataset_id})"
    )

    db = SessionLocal()

    try:
        dataframe = load_dataset_as_dataframe(
            db=db,
            user_id=user_id,
            dataset_id=selected_dataset_id,
            data_key=data_key,
        )

        render_dataset_overview(dataframe)

        st.divider()

        left_column, right_column = st.columns([1, 1])

        with left_column:
            render_step_builder(dataframe)

        with right_column:
            render_current_pipeline()

        st.divider()

        render_run_pipeline_section(
            db=db,
            user_id=user_id,
            dataset_id=selected_dataset_id,
            dataframe=dataframe,
        )

        render_last_results_section()

    finally:
        db.close()


def initialize_pipeline_state() -> None:
    """
    Initializes Streamlit session state for pipeline builder.
    """
    if CURRENT_PIPELINE_KEY not in st.session_state:
        st.session_state[CURRENT_PIPELINE_KEY] = []

    if LAST_PIPELINE_RESULTS_KEY not in st.session_state:
        st.session_state[LAST_PIPELINE_RESULTS_KEY] = []


def render_dataset_overview(dataframe: pd.DataFrame) -> None:
    """
    Displays basic information and preview for the selected dataset.
    """
    st.subheader("Dataset preview")

    col_rows, col_columns = st.columns(2)

    with col_rows:
        st.metric("Rows", dataframe.shape[0])

    with col_columns:
        st.metric("Columns", dataframe.shape[1])

    with st.expander("Coloane și tipuri de date", expanded=False):
        dtypes = {
            column: str(dtype)
            for column, dtype in dataframe.dtypes.items()
        }
        st.json(dtypes)

    st.dataframe(
        dataframe.head(10),
        width="stretch",
    )


def render_step_builder(dataframe: pd.DataFrame) -> None:
    """
    Lets the user choose and configure one pipeline step.
    """
    st.subheader("Adaugă metodă în pipeline")

    steps_metadata = list_steps_metadata()

    if not steps_metadata:
        st.warning("Nu există metode disponibile în registry.")
        return

    step_labels = {
        build_step_label(step_metadata): step_metadata
        for step_metadata in steps_metadata
    }

    selected_step_label = st.selectbox(
        "Alege o metodă",
        options=list(step_labels.keys()),
    )

    selected_step_metadata = step_labels[selected_step_label]

    st.caption(selected_step_metadata["description"])
    st.write(f"Output type: `{selected_step_metadata['output_type']}`")
    st.write(f"Category: `{selected_step_metadata['category']}`")

    with st.form("add_step_form"):
        parameters = render_parameters_form(
            step_metadata=selected_step_metadata,
            dataframe=dataframe,
        )

        submitted = st.form_submit_button("Adaugă pas în pipeline")

    if submitted:
        step_config = {
            "step_name": selected_step_metadata["name"],
            "parameters": parameters,
        }

        st.session_state[CURRENT_PIPELINE_KEY].append(step_config)

        st.success(
            f"Pasul '{selected_step_metadata['display_name']}' a fost adăugat."
        )
        st.rerun()


def build_step_label(step_metadata: dict[str, Any]) -> str:
    """
    Builds a readable label for step selectbox.
    """
    return (
        f"{step_metadata['display_name']} "
        f"({step_metadata['category']})"
    )


def render_parameters_form(
    step_metadata: dict[str, Any],
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Dynamically renders input widgets based on StepParameter metadata.
    """
    parameters: dict[str, Any] = {}

    step_parameters = step_metadata.get("parameters", [])

    if not step_parameters:
        st.info("Această metodă nu are parametri configurabili.")
        return parameters

    for parameter in step_parameters:
        parameter_name = parameter["name"]
        parameter_label = parameter["label"]
        parameter_type = parameter["parameter_type"]
        required = parameter["required"]
        default = parameter["default"]
        options = parameter["options"]
        description = parameter["description"]

        help_text = description or None

        widget_key = f"param_{step_metadata['name']}_{parameter_name}"

        if parameter_type == "column":
            column_options = list(dataframe.columns)

            if not column_options:
                st.warning("Datasetul nu are coloane disponibile.")
                parameters[parameter_name] = None
                continue

            default_index = 0

            if isinstance(default, str) and default in column_options:
                default_index = column_options.index(default)

            value = st.selectbox(
                parameter_label,
                options=column_options,
                index=default_index,
                help=help_text,
                key=widget_key,
            )

            if required and not value:
                st.warning(f"Parametrul '{parameter_label}' este obligatoriu.")

            parameters[parameter_name] = value

        elif parameter_type == "columns":
            default_columns = normalize_default_columns(
                default=default,
                dataframe=dataframe,
            )

            value = st.multiselect(
                parameter_label,
                options=list(dataframe.columns),
                default=default_columns,
                help=help_text,
                key=widget_key,
            )

            if required and not value:
                st.warning(f"Parametrul '{parameter_label}' este obligatoriu.")

            parameters[parameter_name] = value

        elif parameter_type == "select":
            select_options = options or []

            if not select_options:
                st.warning(
                    f"Parametrul '{parameter_label}' nu are opțiuni definite."
                )
                parameters[parameter_name] = default
                continue

            default_index = get_default_index(
                options=select_options,
                default=default,
            )

            value = st.selectbox(
                parameter_label,
                options=select_options,
                index=default_index,
                help=help_text,
                key=widget_key,
            )

            parameters[parameter_name] = value

        elif parameter_type == "number":
            value = st.number_input(
                parameter_label,
                value=float(default) if default is not None else 0.0,
                help=help_text,
                key=widget_key,
            )

            parameters[parameter_name] = value

        elif parameter_type == "text":
            value = st.text_input(
                parameter_label,
                value=str(default) if default is not None else "",
                help=help_text,
                key=widget_key,
            )

            parameters[parameter_name] = value

        else:
            st.warning(
                f"Tip de parametru necunoscut: {parameter_type}. "
                "Va fi tratat ca text."
            )

            value = st.text_input(
                parameter_label,
                value=str(default) if default is not None else "",
                help=help_text,
                key=widget_key,
            )

            parameters[parameter_name] = value

    return parameters


def normalize_default_columns(
    default: Any,
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Normalizes default value for columns parameter.
    """
    if default is None:
        return []

    if isinstance(default, list):
        return [
            column
            for column in default
            if column in dataframe.columns
        ]

    if isinstance(default, str) and default in dataframe.columns:
        return [default]

    return []


def get_default_index(
    options: list[Any],
    default: Any,
) -> int:
    """
    Finds default index for selectbox.
    """
    if default in options:
        return options.index(default)

    return 0


def render_current_pipeline() -> None:
    """
    Displays current pipeline from session state.
    """
    st.subheader("Pipeline curent")

    steps_config = st.session_state[CURRENT_PIPELINE_KEY]

    if not steps_config:
        st.info("Pipeline-ul este gol. Adaugă cel puțin un pas.")
        return

    for index, step_config in enumerate(steps_config):
        with st.expander(
            f"{index + 1}. {step_config['step_name']}",
            expanded=True,
        ):
            st.write("Parametri:")
            st.json(step_config.get("parameters", {}))

            if st.button(
                "Șterge pasul",
                key=f"remove_step_{index}",
            ):
                st.session_state[CURRENT_PIPELINE_KEY].pop(index)
                st.rerun()

    if st.button("Golește pipeline-ul"):
        st.session_state[CURRENT_PIPELINE_KEY] = []
        st.session_state[LAST_PIPELINE_RESULTS_KEY] = []
        st.rerun()


def render_run_pipeline_section(
    db,
    user_id: int,
    dataset_id: int,
    dataframe: pd.DataFrame,
) -> None:
    """
    Renders pipeline execution section.
    """
    st.subheader("Rulează pipeline")

    steps_config = st.session_state[CURRENT_PIPELINE_KEY]

    pipeline_name = st.text_input(
        "Nume pipeline",
        value="Untitled pipeline",
    )

    run_button = st.button(
        "Rulează pipeline",
        type="primary",
    )

    if not run_button:
        return

    if not steps_config:
        st.error("Pipeline-ul este gol. Adaugă cel puțin un pas înainte de rulare.")
        return

    if not pipeline_name.strip():
        st.error("Numele pipeline-ului nu poate fi gol.")
        return

    try:
        final_dataframe, results = run_pipeline_and_save(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
            dataframe=dataframe,
            pipeline_name=pipeline_name.strip(),
            steps_config=steps_config,
        )

        st.session_state[LAST_PIPELINE_RESULTS_KEY] = [
            step_result_to_display_dict(result)
            for result in results
        ]

        st.success("Pipeline rulat și salvat cu succes.")

        st.write("Preview DataFrame final:")
        st.dataframe(
            final_dataframe.head(10),
            width="stretch",
        )

    except Exception as error:
        st.error(f"Eroare la rularea pipeline-ului: {error}")


def step_result_to_display_dict(result) -> dict[str, Any]:
    """
    Converts StepResult to a display-friendly dictionary.
    """
    return {
        "step_name": result.step_name,
        "category": result.category,
        "output_type": result.output_type,
        "parameters": make_json_safe(result.parameters),
        "metrics": make_json_safe(result.metrics),
        "warnings": make_json_safe(result.warnings),
        "interpretation": result.interpretation,
    }


def make_json_safe(value: Any) -> Any:
    """
    Converts values to JSON-safe objects for Streamlit display.
    """
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def render_last_results_section() -> None:
    """
    Displays the latest pipeline results from session state.
    """
    results = st.session_state.get(LAST_PIPELINE_RESULTS_KEY, [])

    if not results:
        return

    st.divider()
    st.subheader("Ultimele rezultate")

    for index, result in enumerate(results):
        title = f"{index + 1}. {result['step_name']}"

        with st.expander(title, expanded=result["step_name"] == "pipeline_summary"):
            st.write(f"Category: `{result['category']}`")
            st.write(f"Output type: `{result['output_type']}`")

            if result["interpretation"]:
                st.info(result["interpretation"])

            if result["warnings"]:
                st.warning("Warnings:")
                st.json(result["warnings"])

            st.write("Parameters:")
            st.json(result["parameters"])

            st.write("Metrics:")
            st.json(result["metrics"])