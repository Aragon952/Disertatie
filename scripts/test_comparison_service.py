import json

from app.db.base import SessionLocal
from app.db.crud import (
    list_user_datasets,
    list_pipeline_runs_for_dataset,
)
from app.services.comparison_service import compare_pipeline_runs


def main() -> None:
    db = SessionLocal()

    try:
        user_id = 1

        datasets = list_user_datasets(
            db=db,
            user_id=user_id,
        )

        if not datasets:
            print("Nu există dataset-uri pentru user_id=1.")
            return

        dataset = datasets[0]

        print(f"Dataset ales:")
        print(f"  id: {dataset.id}")
        print(f"  filename: {dataset.original_filename}")

        pipeline_runs = list_pipeline_runs_for_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
        )

        print(f"\nPipeline runs găsite: {len(pipeline_runs)}")

        for run in pipeline_runs:
            print(
                f"  id={run.id} | name={run.pipeline_name} | created_at={run.created_at}"
            )

        if len(pipeline_runs) < 2:
            print("\nAi nevoie de cel puțin 2 pipeline runs pentru comparație.")
            return

        selected_run_ids = [
            pipeline_runs[0].id,
            pipeline_runs[1].id,
        ]

        print(f"\nCompar pipeline runs: {selected_run_ids}")

        comparison = compare_pipeline_runs(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
            pipeline_run_ids=selected_run_ids,
        )

        print("\nComparație creată cu succes!")
        print(f"Comparison id: {comparison.id}")

        comparison_results = json.loads(comparison.comparison_results_json)

        print("\nMetrici comparate:")
        for metric in comparison_results["all_metrics"]:
            print(f"  - {metric}")

        print("\nTabel comparație:")
        for row in comparison_results["comparison_table"]:
            print(row)

    finally:
        db.close()


if __name__ == "__main__":
    main()