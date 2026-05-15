import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.crud import create_comparison, get_pipeline_run_by_id
from app.db.models import Comparison, PipelineRun


def compare_pipeline_runs(
    db: Session,
    user_id: int,
    dataset_id: int,
    pipeline_run_ids: list[int],
) -> Comparison:
    """
    Compares multiple pipeline runs for the same user and dataset.

    The comparison is descriptive:
    - it validates the selected runs;
    - extracts comparable metrics;
    - builds a table-like structure for UI display;
    - saves the comparison in the comparisons table.

    It does not decide which run is better.
    """
    if len(pipeline_run_ids) < 2:
        raise ValueError("You must select at least two pipeline runs to compare.")

    runs = _load_and_validate_pipeline_runs(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        pipeline_run_ids=pipeline_run_ids,
    )

    comparison_results = _build_pipeline_comparison_results(
        dataset_id=dataset_id,
        runs=runs,
    )

    comparison = create_comparison(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        selected_run_ids=pipeline_run_ids,
        comparison_results=comparison_results,
        ai_summary=None,
    )

    return comparison


def _load_and_validate_pipeline_runs(
    db: Session,
    user_id: int,
    dataset_id: int,
    pipeline_run_ids: list[int],
) -> list[PipelineRun]:
    """
    Loads pipeline runs and validates ownership and dataset consistency.
    """
    runs: list[PipelineRun] = []

    for run_id in pipeline_run_ids:
        pipeline_run = get_pipeline_run_by_id(
            db=db,
            pipeline_run_id=run_id,
        )

        if pipeline_run is None:
            raise ValueError(f"Pipeline run with id={run_id} was not found.")

        if pipeline_run.user_id != user_id:
            raise PermissionError(
                f"Pipeline run with id={run_id} does not belong to the current user."
            )

        if pipeline_run.dataset_id != dataset_id:
            raise ValueError(
                f"Pipeline run with id={run_id} does not belong to dataset id={dataset_id}."
            )

        runs.append(pipeline_run)

    return runs


def _build_pipeline_comparison_results(
    dataset_id: int,
    runs: list[PipelineRun],
) -> dict[str, Any]:
    """
    Builds the full JSON-serializable comparison result.
    """
    run_summaries = [
        _summarize_pipeline_run(run)
        for run in runs
    ]

    comparison_table = _build_comparison_table(run_summaries)
    common_steps = _extract_common_steps(run_summaries)
    all_metrics = _extract_all_metric_names(run_summaries)

    return {
        "comparison_type": "pipeline_runs",
        "dataset_id": dataset_id,
        "selected_pipeline_run_ids": [run.id for run in runs],
        "runs": run_summaries,
        "comparison_table": comparison_table,
        "common_steps": common_steps,
        "all_metrics": all_metrics,
        "notes": [
            "Metrics are displayed for each selected pipeline run.",
            "The application does not automatically decide which pipeline is better.",
            "The final decision is left to the user based on the displayed metrics.",
        ],
    }


def _summarize_pipeline_run(run: PipelineRun) -> dict[str, Any]:
    """
    Converts one PipelineRun into a normalized summary.
    """
    pipeline_config = _safe_json_load(
        run.pipeline_config_json,
        default=[],
    )

    results = _safe_json_load(
        run.results_json,
        default=[],
    )

    step_names = _extract_step_names(results)
    categories = _extract_categories(results)
    warnings = _extract_warnings(results)
    parameters_by_step = _extract_parameters_by_step(results)
    metrics = _extract_comparable_metrics(results)
    step_details = _extract_step_details(results)

    return {
        "pipeline_run_id": run.id,
        "pipeline_name": run.pipeline_name,
        "dataset_id": run.dataset_id,
        "created_at": _datetime_to_string(run.created_at),
        "steps_count": len(step_names),
        "step_names": step_names,
        "categories": categories,
        "pipeline_config": pipeline_config,
        "parameters_by_step": parameters_by_step,
        "warnings_count": len(warnings),
        "warnings": warnings,
        "metrics": metrics,
        "step_details": step_details,
    }


def _safe_json_load(
    json_text: str | None,
    default: Any,
) -> Any:
    """
    Safely parses JSON stored as text.
    """
    if not json_text:
        return default

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return default


def _datetime_to_string(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def _extract_step_names(results: list[dict[str, Any]]) -> list[str]:
    return [
        result.get("step_name", "unknown_step")
        for result in results
    ]


def _extract_categories(results: list[dict[str, Any]]) -> list[str]:
    categories = {
        result.get("category")
        for result in results
        if result.get("category") is not None
    }

    return sorted(categories)


def _extract_warnings(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []

    for result in results:
        step_name = result.get("step_name", "unknown_step")

        for warning in result.get("warnings", []):
            warnings.append(
                {
                    "step_name": step_name,
                    "warning": warning,
                }
            )

    return warnings


def _extract_parameters_by_step(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    parameters_by_step: dict[str, dict[str, Any]] = {}

    for result in results:
        step_name = result.get("step_name", "unknown_step")
        parameters = result.get("parameters", {})

        parameters_by_step[step_name] = _to_json_safe(parameters)

    return parameters_by_step


def _extract_step_details(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Keeps detailed information for each step.

    This is useful in the UI for expandable sections under the comparison table.
    """
    details: list[dict[str, Any]] = []

    for result in results:
        details.append(
            {
                "step_name": result.get("step_name", "unknown_step"),
                "category": result.get("category"),
                "output_type": result.get("output_type"),
                "parameters": _to_json_safe(result.get("parameters", {})),
                "metrics": _to_json_safe(result.get("metrics", {})),
                "warnings": _to_json_safe(result.get("warnings", [])),
                "interpretation": result.get("interpretation", ""),
            }
        )

    return details


def _extract_comparable_metrics(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Extracts metrics that are useful for comparison tables.

    The full step metrics are preserved separately in step_details.
    This function creates a cleaner, UI-friendly metric dictionary.
    """
    comparable_metrics: dict[str, Any] = {}

    for result in results:
        step_name = result.get("step_name", "unknown_step")
        parameters = result.get("parameters", {}) or {}
        metrics = result.get("metrics", {}) or {}

        if step_name == "drop_missing_rows":
            _add_metric(
                comparable_metrics,
                step_name,
                "initial_rows",
                metrics.get("initial_rows"),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "final_rows",
                metrics.get("final_rows"),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "removed_rows",
                metrics.get("removed_rows"),
            )

        elif step_name == "fill_missing_values":
            filled_columns = metrics.get("filled_columns", [])
            skipped_columns = metrics.get("skipped_columns", [])

            _add_metric(
                comparable_metrics,
                step_name,
                "strategy",
                parameters.get("strategy"),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "filled_columns_count",
                len(filled_columns),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "filled_columns",
                _format_list_value(filled_columns),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "skipped_columns_count",
                len(skipped_columns),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "skipped_columns",
                _format_list_value(skipped_columns),
            )

        elif step_name == "select_columns":
            selected_columns = metrics.get("selected_columns", [])

            _add_metric(
                comparable_metrics,
                step_name,
                "selected_columns_count",
                len(selected_columns),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "selected_columns",
                _format_list_value(selected_columns),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "final_column_count",
                metrics.get("final_column_count"),
            )

        elif step_name == "describe_dataset":
            numeric_columns = metrics.get("numeric_columns", [])

            _add_metric(
                comparable_metrics,
                step_name,
                "numeric_columns_count",
                len(numeric_columns),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "numeric_columns",
                _format_list_value(numeric_columns),
            )

        elif step_name == "correlation_matrix":
            columns = metrics.get("columns", [])

            _add_metric(
                comparable_metrics,
                step_name,
                "method",
                metrics.get("method"),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "columns_count",
                len(columns),
            )
            _add_metric(
                comparable_metrics,
                step_name,
                "columns",
                _format_list_value(columns),
            )

        else:
            generic_metrics = _flatten_generic_metrics(
                step_name=step_name,
                metrics=metrics,
            )
            comparable_metrics.update(generic_metrics)

    return comparable_metrics


def _add_metric(
    target: dict[str, Any],
    step_name: str,
    metric_name: str,
    value: Any,
) -> None:
    key = f"{step_name}.{metric_name}"
    target[key] = _to_json_safe(value)


def _format_list_value(value: Any) -> str:
    """
    Converts list-like values to a readable string for comparison tables.
    """
    if not isinstance(value, list):
        return ""

    return ", ".join(str(item) for item in value)


def _flatten_generic_metrics(
    step_name: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """
    Fallback for future custom or ML steps.

    It keeps simple scalar metrics and summarizes lists/dicts.
    This prevents large nested objects from making the comparison table unusable.
    """
    flattened: dict[str, Any] = {}

    for metric_name, value in metrics.items():
        key = f"{step_name}.{metric_name}"

        if _is_scalar(value):
            flattened[key] = value

        elif isinstance(value, list):
            flattened[f"{key}_count"] = len(value)
            flattened[key] = _format_list_value(value)

        elif isinstance(value, dict):
            flattened[f"{key}_keys_count"] = len(value.keys())
            flattened[f"{key}_keys"] = _format_list_value(list(value.keys()))

        else:
            flattened[key] = str(value)

    return flattened


def _build_comparison_table(
    run_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Builds a table-like list of rows.

    Each row has:
    - metric
    - one column per pipeline run
    """
    all_metric_names = _extract_all_metric_names(run_summaries)

    table: list[dict[str, Any]] = []

    for metric_name in all_metric_names:
        row: dict[str, Any] = {
            "metric": metric_name,
        }

        for run_summary in run_summaries:
            run_id = run_summary["pipeline_run_id"]
            run_label = f"run_{run_id}"

            row[run_label] = run_summary["metrics"].get(metric_name)

        table.append(row)

    return table


def _extract_all_metric_names(
    run_summaries: list[dict[str, Any]],
) -> list[str]:
    metric_names: set[str] = set()

    for run_summary in run_summaries:
        metric_names.update(run_summary.get("metrics", {}).keys())

    return sorted(metric_names)


def _extract_common_steps(
    run_summaries: list[dict[str, Any]],
) -> list[str]:
    """
    Returns steps that appear in all compared runs.
    """
    if not run_summaries:
        return []

    step_sets = [
        set(run_summary.get("step_names", []))
        for run_summary in run_summaries
    ]

    common_steps = set.intersection(*step_sets)

    return sorted(common_steps)


def _to_json_safe(value: Any) -> Any:
    """
    Converts values to JSON-safe structures.
    """
    if _is_scalar(value):
        return value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [
            _to_json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _to_json_safe(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key): _to_json_safe(item)
            for key, item in value.items()
        }

    return str(value)


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))