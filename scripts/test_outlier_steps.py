import json

import pandas as pd

from app.db.base import SessionLocal
from app.db.crud import list_user_datasets, list_pipeline_runs_for_dataset
from app.services.analysis_service import run_pipeline_and_save


def main() -> None:
    db = SessionLocal()

    try:
        user_id = 1

        datasets = list_user_datasets(db=db, user_id=user_id)

        if not datasets:
            print("Nu există dataset-uri pentru user_id=1.")
            return

        dataset = datasets[0]

        dataframe = pd.DataFrame(
            {
                "price": [10, 12, 11, 13, 1000],
                "quantity": [1, 2, 2, 3, 50],
                "category": ["A", "A", "B", "B", "C"],
            }
        )

        steps_config = [
            {
                "step_name": "outlier_detection_iqr",
                "parameters": {
                    "columns": ["price", "quantity"],
                    "factor": 1.5,
                },
            },
            {
                "step_name": "outlier_detection_zscore",
                "parameters": {
                    "columns": ["price", "quantity"],
                    "threshold": 1.5,
                },
            },
        ]

        final_dataframe, results = run_pipeline_and_save(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
            dataframe=dataframe,
            pipeline_name="Outlier detection test",
            steps_config=steps_config,
        )

        print("Pipeline rulat cu succes.")
        print(f"Shape inițial: {dataframe.shape}")
        print(f"Shape final: {final_dataframe.shape}")
        print(f"Rezultate returnate: {len(results)}")

        for result in results:
            print("\n" + "-" * 80)
            print(f"step_name: {result.step_name}")
            print(f"category: {result.category}")
            print(f"output_type: {result.output_type}")
            print("metrics:")
            print(json.dumps(result.metrics, indent=2, ensure_ascii=False))

        pipeline_runs = list_pipeline_runs_for_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset.id,
        )

        latest_run = pipeline_runs[0]

        print("\nUltimul PipelineRun salvat:")
        print(f"id={latest_run.id}")
        print(f"name={latest_run.pipeline_name}")

    finally:
        db.close()


if __name__ == "__main__":
    main()