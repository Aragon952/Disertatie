import json
import os
from typing import Any


DEFAULT_OPENAI_MODEL = "gpt-5.5"


def is_openai_configured() -> bool:
    """
    Checks whether OpenAI API key is available.
    """
    return bool(os.getenv("OPENAI_API_KEY"))


def get_openai_model() -> str:
    """
    Returns the configured OpenAI model or a default one.
    """
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def generate_comparison_ai_summary(
    comparison_results: dict[str, Any],
) -> str:
    """
    Generates a concise AI interpretation for pipeline comparison results.

    This function is intentionally descriptive, not prescriptive:
    it should help the user understand the differences, not decide automatically
    which pipeline is best.
    """
    if not is_openai_configured():
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment or .env file."
        )

    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError(
            "The 'openai' package is not installed. Install it with: pip install openai"
        ) from error

    client = OpenAI()

    compact_payload = build_compact_comparison_payload(comparison_results)

    prompt = build_comparison_prompt(compact_payload)

    response = client.responses.create(
        model=get_openai_model(),
        input=prompt,
    )

    return response.output_text


def build_compact_comparison_payload(
    comparison_results: dict[str, Any],
) -> dict[str, Any]:
    """
    Builds a smaller payload for AI interpretation.

    Avoids sending huge nested metrics such as full correlation matrices.
    """
    runs = comparison_results.get("runs", [])
    comparison_table = comparison_results.get("comparison_table", [])

    compact_runs = []

    for run in runs:
        compact_runs.append(
            {
                "pipeline_run_id": run.get("pipeline_run_id"),
                "pipeline_name": run.get("pipeline_name"),
                "created_at": run.get("created_at"),
                "steps_count": run.get("steps_count"),
                "step_names": run.get("step_names", []),
                "categories": run.get("categories", []),
                "warnings_count": run.get("warnings_count", 0),
                "warnings": run.get("warnings", []),
                "metrics": run.get("metrics", {}),
            }
        )

    return {
        "comparison_type": comparison_results.get("comparison_type"),
        "dataset_id": comparison_results.get("dataset_id"),
        "selected_pipeline_run_ids": comparison_results.get(
            "selected_pipeline_run_ids",
            [],
        ),
        "runs": compact_runs,
        "comparison_table": comparison_table,
        "common_steps": comparison_results.get("common_steps", []),
        "all_metrics": comparison_results.get("all_metrics", []),
    }


def build_comparison_prompt(
    compact_payload: dict[str, Any],
) -> str:
    payload_json = json.dumps(
        compact_payload,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
You are helping interpret results from a data analysis application.

The application compares pipeline runs. Each pipeline may contain preprocessing,
statistics, outlier detection, or other analysis methods.

Important rules:
- Do not choose a single "best" pipeline.
- Do not say that one pipeline is objectively better.
- Explain the differences neutrally.
- Mention trade-offs.
- If metrics are missing for a run, explain that the method was probably not used in that run.
- Use Romanian.
- Keep the response clear and useful for a student dissertation project.

Please structure the answer like this:
1. Rezumat scurt
2. Diferențe importante între pipeline-uri
3. Observații despre metrici
4. Posibile interpretări, fără a decide automat câștigătorul

Comparison data:
{payload_json}
""".strip()