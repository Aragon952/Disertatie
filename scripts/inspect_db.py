import json

from app.db.base import SessionLocal
from app.db.crud import (
    list_user_datasets,
    list_pipeline_runs_for_dataset,
    list_comparisons_for_dataset,
)


def pretty_json(value: str):
    try:
        return json.dumps(json.loads(value), indent=2, ensure_ascii=False)
    except Exception:
        return value


def main() -> None:
    db = SessionLocal()

    try:
        user_id = 1

        datasets = list_user_datasets(db=db, user_id=user_id)

        print("\n=== DATASETS ===")
        for dataset in datasets:
            print(f"id={dataset.id}")
            print(f"original_filename={dataset.original_filename}")
            print(f"file_type={dataset.file_type}")
            print(f"uploaded_at={dataset.uploaded_at}")
            print("-" * 80)

        if not datasets:
            return

        dataset = datasets[0]

        pipeline_runs = list_pipeline_runs_for_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
        )

        print("\n=== PIPELINE RUNS ===")
        for run in pipeline_runs:
            print(f"id={run.id}")
            print(f"pipeline_name={run.pipeline_name}")
            print(f"dataset_id={run.dataset_id}")
            print(f"created_at={run.created_at}")

            print("\npipeline_config_json:")
            print(pretty_json(run.pipeline_config_json))

            print("\nresults_json:")
            print(pretty_json(run.results_json))

            print("-" * 80)

        comparisons = list_comparisons_for_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
        )

        print("\n=== COMPARISONS ===")
        for comparison in comparisons:
            print(f"id={comparison.id}")
            print(f"dataset_id={comparison.dataset_id}")
            print(f"created_at={comparison.created_at}")

            print("\nselected_runs_json:")
            print(pretty_json(comparison.selected_runs_json))

            print("\ncomparison_results_json:")
            print(pretty_json(comparison.comparison_results_json))

            print("\nai_summary:")
            print(comparison.ai_summary)

            print("-" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()