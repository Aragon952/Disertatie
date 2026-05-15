import json

import pandas as pd

from app.db.base import SessionLocal
from app.db.crud import list_user_datasets, list_pipeline_runs_for_dataset
from app.services.analysis_service import run_pipeline_and_save


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

        print("Dataset folosit pentru metadata:")
        print(f"  id={dataset.id}")
        print(f"  filename={dataset.original_filename}")

        dataframe = pd.DataFrame(
            {
                "price": [10, 20, None, 40],
                "quantity": [1, 2, 3, None],
                "category": ["A", "B", "A", "C"],
            }
        )

        steps_config = [
            {
                "step_name": "fill_missing_values",
                "parameters": {
                    "columns": ["price", "quantity"],
                    "strategy": "mean",
                },
            },
            {
                "step_name": "describe_dataset",
                "parameters": {},
            },
        ]

        final_dataframe, results = run_pipeline_and_save(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
            dataframe=dataframe,
            pipeline_name="Pipeline summary test",
            steps_config=steps_config,
        )

        print("\nPipeline rulat cu succes.")
        print(f"Shape inițial: {dataframe.shape}")
        print(f"Shape final: {final_dataframe.shape}")
        print(f"Număr rezultate returnate: {len(results)}")

        summary = results[-1]

        print("\nUltimul rezultat returnat:")
        print(f"  step_name={summary.step_name}")
        print(f"  category={summary.category}")
        print(f"  output_type={summary.output_type}")

        print("\nMetrici pipeline_summary:")
        print(json.dumps(summary.metrics, indent=2, ensure_ascii=False))

        pipeline_runs = list_pipeline_runs_for_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
        )

        latest_run = pipeline_runs[0]
        saved_results = json.loads(latest_run.results_json)

        print("\nUltimul PipelineRun salvat:")
        print(f"  id={latest_run.id}")
        print(f"  name={latest_run.pipeline_name}")

        print("\nUltimul element din results_json:")
        print(json.dumps(saved_results[-1], indent=2, ensure_ascii=False))

    finally:
        db.close()


if __name__ == "__main__":
    main()