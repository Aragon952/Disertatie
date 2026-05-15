from typing import Any

import pandas as pd

from app.analysis_methods.base import PipelineStep, StepParameter, StepResult


class OutlierDetectionIQRStep(PipelineStep):
    name = "outlier_detection_iqr"
    display_name = "Outlier Detection - IQR"
    category = "statistics"
    description = "Detects outliers in numeric columns using the IQR method."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns to analyze.",
        ),
        StepParameter(
            name="factor",
            label="IQR factor",
            parameter_type="number",
            required=True,
            default=1.5,
            description="Multiplier used for the IQR bounds.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}

        columns = parameters.get("columns")
        factor = float(parameters.get("factor", 1.5))

        numeric_dataframe = dataframe.select_dtypes(include="number")

        if columns:
            numeric_columns = [
                column
                for column in columns
                if column in numeric_dataframe.columns
            ]
        else:
            numeric_columns = list(numeric_dataframe.columns)

        skipped_columns = []
        if columns:
            skipped_columns = [
                column
                for column in columns
                if column not in numeric_dataframe.columns
            ]

        if not numeric_columns:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "factor": factor,
                },
                metrics={
                    "method": "iqr",
                    "factor": factor,
                    "columns": [],
                    "columns_count": 0,
                    "total_rows": int(len(dataframe)),
                    "outliers_count": 0,
                    "outliers_percentage": 0.0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                    "per_column": {},
                },
                warnings=["No numeric columns available for IQR outlier detection."],
                interpretation="No outliers were detected because no numeric columns were available.",
            )

        outlier_mask = pd.Series(False, index=dataframe.index)
        per_column: dict[str, Any] = {}

        for column in numeric_columns:
            series = dataframe[column].dropna()

            if series.empty:
                per_column[column] = {
                    "q1": None,
                    "q3": None,
                    "iqr": None,
                    "lower_bound": None,
                    "upper_bound": None,
                    "outliers_count": 0,
                    "skipped": True,
                }
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr

            column_mask = (
                (dataframe[column] < lower_bound)
                | (dataframe[column] > upper_bound)
            )

            column_outliers_count = int(column_mask.sum())
            outlier_mask = outlier_mask | column_mask.fillna(False)

            per_column[column] = {
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outliers_count": column_outliers_count,
                "skipped": False,
            }

        total_rows = int(len(dataframe))
        outliers_count = int(outlier_mask.sum())
        outliers_percentage = (
            round((outliers_count / total_rows) * 100, 4)
            if total_rows > 0
            else 0.0
        )

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped non-numeric or missing columns: {skipped_columns}."
            )

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters={
                "columns": numeric_columns,
                "factor": factor,
            },
            metrics={
                "method": "iqr",
                "factor": factor,
                "columns": numeric_columns,
                "columns_count": len(numeric_columns),
                "total_rows": total_rows,
                "outliers_count": outliers_count,
                "outliers_percentage": outliers_percentage,
                "skipped_columns": skipped_columns,
                "skipped_columns_count": len(skipped_columns),
                "per_column": per_column,
            },
            warnings=warnings,
            interpretation=f"Detected {outliers_count} outlier rows using the IQR method.",
        )


class OutlierDetectionZScoreStep(PipelineStep):
    name = "outlier_detection_zscore"
    display_name = "Outlier Detection - Z-score"
    category = "statistics"
    description = "Detects outliers in numeric columns using the Z-score method."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns to analyze.",
        ),
        StepParameter(
            name="threshold",
            label="Z-score threshold",
            parameter_type="number",
            required=True,
            default=3.0,
            description="Absolute Z-score threshold used to mark outliers.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}

        columns = parameters.get("columns")
        threshold = float(parameters.get("threshold", 3.0))

        numeric_dataframe = dataframe.select_dtypes(include="number")

        if columns:
            numeric_columns = [
                column
                for column in columns
                if column in numeric_dataframe.columns
            ]
        else:
            numeric_columns = list(numeric_dataframe.columns)

        skipped_columns = []
        if columns:
            skipped_columns = [
                column
                for column in columns
                if column not in numeric_dataframe.columns
            ]

        if not numeric_columns:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "threshold": threshold,
                },
                metrics={
                    "method": "zscore",
                    "threshold": threshold,
                    "columns": [],
                    "columns_count": 0,
                    "total_rows": int(len(dataframe)),
                    "outliers_count": 0,
                    "outliers_percentage": 0.0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                    "per_column": {},
                },
                warnings=["No numeric columns available for Z-score outlier detection."],
                interpretation="No outliers were detected because no numeric columns were available.",
            )

        outlier_mask = pd.Series(False, index=dataframe.index)
        per_column: dict[str, Any] = {}

        for column in numeric_columns:
            mean_value = dataframe[column].mean()
            std_value = dataframe[column].std()

            if std_value == 0 or pd.isna(std_value):
                per_column[column] = {
                    "mean": float(mean_value) if not pd.isna(mean_value) else None,
                    "std": 0.0,
                    "threshold": threshold,
                    "outliers_count": 0,
                    "skipped": True,
                }
                continue

            z_scores = (dataframe[column] - mean_value) / std_value
            column_mask = z_scores.abs() > threshold

            column_outliers_count = int(column_mask.sum())
            outlier_mask = outlier_mask | column_mask.fillna(False)

            per_column[column] = {
                "mean": float(mean_value),
                "std": float(std_value),
                "threshold": threshold,
                "outliers_count": column_outliers_count,
                "skipped": False,
            }

        total_rows = int(len(dataframe))
        outliers_count = int(outlier_mask.sum())
        outliers_percentage = (
            round((outliers_count / total_rows) * 100, 4)
            if total_rows > 0
            else 0.0
        )

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped non-numeric or missing columns: {skipped_columns}."
            )

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters={
                "columns": numeric_columns,
                "threshold": threshold,
            },
            metrics={
                "method": "zscore",
                "threshold": threshold,
                "columns": numeric_columns,
                "columns_count": len(numeric_columns),
                "total_rows": total_rows,
                "outliers_count": outliers_count,
                "outliers_percentage": outliers_percentage,
                "skipped_columns": skipped_columns,
                "skipped_columns_count": len(skipped_columns),
                "per_column": per_column,
            },
            warnings=warnings,
            interpretation=f"Detected {outliers_count} outlier rows using the Z-score method.",
        )