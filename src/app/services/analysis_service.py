import json
import time 
from dataclasses import asdict
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.analysis_methods.base import StepResult
from app.analysis_methods.registry import get_step_by_name
from app.db.crud import create_analysis_run, create_pipeline_run


def step_result_to_dict(result: StepResult) -> dict[str, Any]:
    """
    Converts StepResult to a JSON-friendly dictionary.

    output_data is intentionally excluded because DataFrames should not be stored
    directly in the database.
    """
    result_dict = asdict(result)
    result_dict.pop("output_data", None)

    return result_dict


def run_step(
    dataframe: pd.DataFrame,
    step_name: str,
    parameters: dict[str, Any] | None = None,
) -> StepResult:
    """
    Runs one registered pipeline step.
    """
    step = get_step_by_name(step_name)

    return step.run(
        dataframe=dataframe,
        parameters=parameters or {},
    )


def run_analysis_step_and_save(
    db: Session,
    user_id: int,
    dataset_id: int,
    dataframe: pd.DataFrame,
    step_name: str,
    parameters: dict[str, Any] | None = None,
) -> StepResult:
    """
    Runs one step and saves the result in the analysis_runs table.

    For preprocessing steps, the transformed DataFrame is returned in StepResult,
    but only the metadata/metrics are saved in DB.
    """
    result = run_step(
        dataframe=dataframe,
        step_name=step_name,
        parameters=parameters,
    )

    result_dict = step_result_to_dict(result)

    create_analysis_run(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        method_name=result.step_name,
        method_category=result.category,
        parameters=result.parameters,
        results=result_dict,
    )

    return result


def run_pipeline(
    dataframe: pd.DataFrame,
    steps_config: list[dict[str, Any]],
) -> tuple[pd.DataFrame, list[StepResult]]:
    """
    Runs multiple steps in order.

    If a step returns a DataFrame, it becomes the input for the next step.
    If a step returns only metrics/results, the current DataFrame stays unchanged.
    """
    current_dataframe = dataframe.copy()
    results: list[StepResult] = []

    for step_config in steps_config:
        step_name = step_config["step_name"]
        parameters = step_config.get("parameters", {})

        result = run_step(
            dataframe=current_dataframe,
            step_name=step_name,
            parameters=parameters,
        )

        results.append(result)

        if result.output_type == "dataframe" and result.output_data is not None:
            current_dataframe = result.output_data

    return current_dataframe, results


def run_pipeline_and_save(
    db: Session,
    user_id: int,
    dataset_id: int,
    dataframe: pd.DataFrame,
    pipeline_name: str,
    steps_config: list[dict[str, Any]],
) -> tuple[pd.DataFrame, list[StepResult]]:
    """
    Runs a pipeline and saves its configuration and results in DB.

    A synthetic pipeline_summary result is added at the end, containing
    general execution and dataset metrics.
    """
    start_time = time.perf_counter()

    final_dataframe, results = run_pipeline(
        dataframe=dataframe,
        steps_config=steps_config,
    )

    execution_time_seconds = time.perf_counter() - start_time

    pipeline_summary_result = build_pipeline_summary_result(
        input_dataframe=dataframe,
        output_dataframe=final_dataframe,
        step_results=results,
        execution_time_seconds=execution_time_seconds,
    )

    results_with_summary = [
        *results,
        pipeline_summary_result,
    ]

    results_as_dicts = [
        step_result_to_dict(result)
        for result in results_with_summary
    ]

    create_pipeline_run(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        pipeline_name=pipeline_name,
        pipeline_config=steps_config,
        results=results_as_dicts,
    )

    return final_dataframe, results_with_summary


def pipeline_results_to_json(results: list[StepResult]) -> str:
    """
    Converts pipeline results to a JSON string.
    """
    return json.dumps(
        [step_result_to_dict(result) for result in results],
        ensure_ascii=False,
    )

def count_missing_values(dataframe: pd.DataFrame) -> int:
    """
    Counts all missing values in a DataFrame.
    """
    return int(dataframe.isna().sum().sum())


def dataframe_memory_mb(dataframe: pd.DataFrame) -> float:
    """
    Estimates DataFrame memory usage in MB.
    """
    memory_bytes = dataframe.memory_usage(deep=True).sum()
    return round(memory_bytes / (1024 * 1024), 4)


def build_pipeline_summary_result(
    input_dataframe: pd.DataFrame,
    output_dataframe: pd.DataFrame,
    step_results: list[StepResult],
    execution_time_seconds: float,
) -> StepResult:
    """
    Builds a synthetic StepResult with general pipeline metrics.

    This result is saved together with the other pipeline step results.
    """
    input_rows = len(input_dataframe)
    input_columns = len(input_dataframe.columns)

    output_rows = len(output_dataframe)
    output_columns = len(output_dataframe.columns)

    missing_values_before = count_missing_values(input_dataframe)
    missing_values_after = count_missing_values(output_dataframe)

    warnings_count = sum(
        len(result.warnings)
        for result in step_results
    )

    return StepResult(
        step_name="pipeline_summary",
        category="custom",
        output_type="result",
        parameters={},
        metrics={
            "execution_time_seconds": round(execution_time_seconds, 6),
            "input_rows": input_rows,
            "input_columns": input_columns,
            "output_rows": output_rows,
            "output_columns": output_columns,
            "rows_delta": output_rows - input_rows,
            "columns_delta": output_columns - input_columns,
            "missing_values_before": missing_values_before,
            "missing_values_after": missing_values_after,
            "missing_values_delta": missing_values_after - missing_values_before,
            "dataframe_memory_mb_before": dataframe_memory_mb(input_dataframe),
            "dataframe_memory_mb_after": dataframe_memory_mb(output_dataframe),
            "steps_count": len(step_results),
            "warnings_count": warnings_count,
        },
        warnings=[],
        interpretation="Generated general pipeline execution summary.",
        output_data=None,
    )