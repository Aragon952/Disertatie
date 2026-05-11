from typing import Any

import pandas as pd

from app.analysis_methods.base import PipelineStep, StepParameter, StepResult


class DropMissingRowsStep(PipelineStep):
    name = "drop_missing_rows"
    display_name = "Drop missing rows"
    category = "preprocessing"
    description = "Removes rows that contain missing values."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional list of columns to check for missing values.",
        )
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}
        columns = parameters.get("columns")

        initial_rows = len(dataframe)

        if columns:
            result_dataframe = dataframe.dropna(subset=columns)
        else:
            result_dataframe = dataframe.dropna()

        removed_rows = initial_rows - len(result_dataframe)

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters=parameters,
            metrics={
                "initial_rows": initial_rows,
                "final_rows": len(result_dataframe),
                "removed_rows": removed_rows,
            },
            interpretation=f"Removed {removed_rows} rows with missing values.",
            output_data=result_dataframe,
        )


class FillMissingValuesStep(PipelineStep):
    name = "fill_missing_values"
    display_name = "Fill missing values"
    category = "preprocessing"
    description = "Fills missing values using mean, median, mode or a custom value."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional list of columns to fill.",
        ),
        StepParameter(
            name="strategy",
            label="Strategy",
            parameter_type="select",
            required=True,
            default="mean",
            options=["mean", "median", "mode", "constant"],
            description="Strategy used to fill missing values.",
        ),
        StepParameter(
            name="constant_value",
            label="Constant value",
            parameter_type="text",
            required=False,
            default="",
            description="Value used when strategy is constant.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}

        columns = parameters.get("columns")
        strategy = parameters.get("strategy", "mean")
        constant_value = parameters.get("constant_value", "")

        result_dataframe = dataframe.copy()

        if columns is None or columns == []:
            columns = list(result_dataframe.columns)

        filled_values = {}
        skipped_columns = []

        for column in columns:
            if column not in result_dataframe.columns:
                skipped_columns.append(column)
                continue

            if strategy == "mean":
                if not pd.api.types.is_numeric_dtype(result_dataframe[column]):
                    skipped_columns.append(column)
                    continue
                value = result_dataframe[column].mean()

            elif strategy == "median":
                if not pd.api.types.is_numeric_dtype(result_dataframe[column]):
                    skipped_columns.append(column)
                    continue
                value = result_dataframe[column].median()

            elif strategy == "mode":
                mode_values = result_dataframe[column].mode()
                if mode_values.empty:
                    skipped_columns.append(column)
                    continue
                value = mode_values.iloc[0]

            elif strategy == "constant":
                value = constant_value

            else:
                raise ValueError(f"Unsupported fill strategy: {strategy}")

            result_dataframe[column] = result_dataframe[column].fillna(value)
            filled_values[column] = str(value)

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped columns: {skipped_columns}. They may be missing or incompatible with the selected strategy."
            )

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters=parameters,
            metrics={
                "filled_columns": list(filled_values.keys()),
                "filled_values": filled_values,
                "skipped_columns": skipped_columns,
            },
            warnings=warnings,
            interpretation=f"Filled missing values for {len(filled_values)} columns.",
            output_data=result_dataframe,
        )


class SelectColumnsStep(PipelineStep):
    name = "select_columns"
    display_name = "Select columns"
    category = "preprocessing"
    description = "Keeps only selected columns from the dataset."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=True,
            description="Columns that should remain in the dataset.",
        )
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}
        columns = parameters.get("columns", [])

        if not columns:
            raise ValueError("You must select at least one column.")

        missing_columns = [
            column
            for column in columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError(f"Columns not found: {missing_columns}")

        result_dataframe = dataframe[columns].copy()

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters=parameters,
            metrics={
                "selected_columns": columns,
                "initial_columns": list(dataframe.columns),
                "final_column_count": len(result_dataframe.columns),
            },
            interpretation=f"Selected {len(columns)} columns.",
            output_data=result_dataframe,
        )