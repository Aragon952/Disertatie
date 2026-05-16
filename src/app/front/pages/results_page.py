import json
from typing import Any

import pandas as pd
import streamlit as st

from app.auth.session import (
    get_current_user_id,
    get_selected_dataset_id,
    get_selected_dataset_name,
)
from app.db.base import SessionLocal
from app.db.crud import (
    list_comparisons_for_dataset,
    list_pipeline_runs_for_dataset,
    update_comparison_ai_summary,
)
from app.services.comparison_service import compare_pipeline_runs
from app.services.openai_service import (
    generate_comparison_ai_summary,
    is_openai_configured,
)


def render_results_page() -> None:
    """
    Renders saved pipeline runs, comparisons and AI interpretation.
    """
    st.title("Results")

    user_id = get_current_user_id()
    dataset_id = get_selected_dataset_id()
    dataset_name = get_selected_dataset_name()

    if user_id is None:
        st.error("Nu există utilizator autentificat.")
        return

    if dataset_id is None:
        st.warning("Nu ai selectat niciun dataset.")
        st.info("Mergi la pagina Datasets și selectează un dataset.")
        return

    st.success(f"Dataset curent: **{dataset_name}** (id={dataset_id})")

    db = SessionLocal()

    try:
        pipeline_runs = list_pipeline_runs_for_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
        )

        if not pipeline_runs:
            st.info("Nu există pipeline runs salvate pentru acest dataset.")
            return

        render_pipeline_runs_overview(pipeline_runs)

        st.divider()

        render_pipeline_run_details_section(pipeline_runs)

        st.divider()

        render_create_comparison_section(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
            pipeline_runs=pipeline_runs,
        )

        st.divider()

        render_saved_comparisons_section(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
        )

    finally:
        db.close()


def render_pipeline_runs_overview(pipeline_runs: list) -> None:
    """
    Displays a simple table with saved pipeline runs.
    """
    st.subheader("Pipeline runs salvate")

    rows = []

    for run in pipeline_runs:
        config = safe_json_load(run.pipeline_config_json, default=[])
        results = safe_json_load(run.results_json, default=[])

        rows.append(
            {
                "id": run.id,
                "name": run.pipeline_name,
                "created_at": str(run.created_at),
                "steps_count": len(config),
                "results_count": len(results),
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
    )


def render_pipeline_run_details_section(pipeline_runs: list) -> None:
    """
    Allows the user to inspect one old pipeline run.
    """
    st.subheader("Detalii pipeline run")

    run_options = {
        build_pipeline_run_label(run): run
        for run in pipeline_runs
    }

    selected_label = st.selectbox(
        "Selectează un pipeline run pentru detalii",
        options=list(run_options.keys()),
        key="results_details_selected_run",
    )

    selected_run = run_options[selected_label]

    pipeline_config = safe_json_load(
        selected_run.pipeline_config_json,
        default=[],
    )

    results = safe_json_load(
        selected_run.results_json,
        default=[],
    )

    st.write(f"Pipeline: **{selected_run.pipeline_name}**")
    st.caption(f"id={selected_run.id} | created_at={selected_run.created_at}")

    with st.expander("Pipeline config", expanded=False):
        st.json(pipeline_config)

    with st.expander("Results", expanded=False):
        for index, result in enumerate(results):
            step_name = result.get("step_name", f"step_{index + 1}")

            with st.expander(
                f"{index + 1}. {step_name}",
                expanded=step_name == "pipeline_summary",
            ):
                st.write(f"Category: `{result.get('category')}`")
                st.write(f"Output type: `{result.get('output_type')}`")

                interpretation = result.get("interpretation")
                if interpretation:
                    st.info(interpretation)

                warnings = result.get("warnings", [])
                if warnings:
                    st.warning("Warnings:")
                    st.json(warnings)

                st.write("Parameters:")
                st.json(result.get("parameters", {}))

                st.write("Metrics:")
                st.json(result.get("metrics", {}))


def render_create_comparison_section(
    db,
    user_id: int,
    dataset_id: int,
    pipeline_runs: list,
) -> None:
    """
    Lets the user select multiple pipeline runs and create a comparison.
    """
    st.subheader("Compară pipeline runs")

    if len(pipeline_runs) < 2:
        st.info("Ai nevoie de cel puțin două pipeline runs pentru comparație.")
        return

    run_options = {
        build_pipeline_run_label(run): run.id
        for run in pipeline_runs
    }

    selected_labels = st.multiselect(
        "Selectează cel puțin două pipeline runs",
        options=list(run_options.keys()),
        key="comparison_selected_runs",
    )

    selected_run_ids = [
        run_options[label]
        for label in selected_labels
    ]

    generate_ai = st.checkbox(
        "Generează interpretare AI după comparație",
        value=False,
        help="Necesită OPENAI_API_KEY configurat în environment.",
    )

    if generate_ai and not is_openai_configured():
        st.warning(
            "OPENAI_API_KEY nu este configurat. Comparația poate fi creată, "
            "dar interpretarea AI nu va funcționa până setezi cheia."
        )

    if st.button("Creează comparație", type="primary"):
        if len(selected_run_ids) < 2:
            st.error("Selectează cel puțin două pipeline runs.")
            return

        try:
            comparison = compare_pipeline_runs(
                db=db,
                user_id=user_id,
                dataset_id=dataset_id,
                pipeline_run_ids=selected_run_ids,
            )

            comparison_results = safe_json_load(
                comparison.comparison_results_json,
                default={},
            )

            st.success(f"Comparație creată cu succes. id={comparison.id}")

            render_comparison_results(comparison_results)

            if generate_ai:
                render_and_save_ai_summary(
                    db=db,
                    comparison_id=comparison.id,
                    comparison_results=comparison_results,
                )

        except Exception as error:
            st.error(f"Eroare la crearea comparației: {error}")


def render_saved_comparisons_section(
    db,
    user_id: int,
    dataset_id: int,
) -> None:
    """
    Displays saved comparisons for the selected dataset.
    """
    st.subheader("Comparații salvate")

    comparisons = list_comparisons_for_dataset(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    if not comparisons:
        st.info("Nu există comparații salvate pentru acest dataset.")
        return

    comparison_options = {
        build_comparison_label(comparison): comparison
        for comparison in comparisons
    }

    selected_label = st.selectbox(
        "Selectează o comparație salvată",
        options=list(comparison_options.keys()),
        key="saved_comparison_selectbox",
    )

    selected_comparison = comparison_options[selected_label]

    selected_runs = safe_json_load(
        selected_comparison.selected_runs_json,
        default=[],
    )

    comparison_results = safe_json_load(
        selected_comparison.comparison_results_json,
        default={},
    )

    st.caption(
        f"id={selected_comparison.id} | "
        f"created_at={selected_comparison.created_at} | "
        f"selected_runs={selected_runs}"
    )

    render_comparison_results(comparison_results)

    if selected_comparison.ai_summary:
        st.subheader("Interpretare AI salvată")
        st.write(selected_comparison.ai_summary)
    else:
        st.info("Această comparație nu are încă interpretare AI.")

    col_ai, col_refresh = st.columns([1, 1])

    with col_ai:
        if st.button(
            "Generează interpretare AI pentru comparația selectată",
            key=f"generate_ai_for_comparison_{selected_comparison.id}",
        ):
            render_and_save_ai_summary(
                db=db,
                comparison_id=selected_comparison.id,
                comparison_results=comparison_results,
            )

    with col_refresh:
        if st.button("Reîncarcă pagina"):
            st.rerun()


def render_comparison_results(
    comparison_results: dict[str, Any],
) -> None:
    """
    Displays comparison results as table and details.
    """
    if not comparison_results:
        st.warning("Comparația nu conține rezultate.")
        return

    comparison_table = comparison_results.get("comparison_table", [])

    if comparison_table:
        st.write("Tabel comparativ")

        st.dataframe(
            pd.DataFrame(comparison_table),
            width="stretch",
        )
    else:
        st.info("Nu există tabel comparativ disponibil.")

    with st.expander("Detalii comparație", expanded=False):
        st.json(comparison_results)


def render_and_save_ai_summary(
    db,
    comparison_id: int,
    comparison_results: dict[str, Any],
) -> None:
    """
    Generates AI summary and saves it to the comparison.
    """
    if not is_openai_configured():
        st.error(
            "OPENAI_API_KEY nu este configurat. "
            "Adaugă cheia în environment sau în fișierul .env."
        )
        return

    try:
        with st.spinner("Generez interpretarea AI..."):
            ai_summary = generate_comparison_ai_summary(
                comparison_results=comparison_results,
            )

            update_comparison_ai_summary(
                db=db,
                comparison_id=comparison_id,
                ai_summary=ai_summary,
            )

        st.success("Interpretarea AI a fost generată și salvată.")
        st.subheader("Interpretare AI")
        st.write(ai_summary)

    except Exception as error:
        st.error(f"Nu am putut genera interpretarea AI: {error}")


def build_pipeline_run_label(run) -> str:
    return f"id={run.id} | {run.pipeline_name} | {run.created_at}"


def build_comparison_label(comparison) -> str:
    return f"id={comparison.id} | {comparison.created_at}"


def safe_json_load(
    json_text: str | None,
    default: Any,
) -> Any:
    if not json_text:
        return default

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return default