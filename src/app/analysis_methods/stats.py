from typing import Any

import pandas as pd

from app.analysis_methods.base import PipelineStep, StepParameter, StepResult


class DescribeDatasetStep(PipelineStep):
    name = "describe_dataset"
    display_name = "Describe dataset"
    category = "statistics"
    description = "Generates descriptive statistics for numeric columns."
    output_type = "result"

    parameters = []

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}

        numeric_dataframe = dataframe.select_dtypes(include="number")

        if numeric_dataframe.empty:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters=parameters,
                metrics={},
                warnings=["No numeric columns found."],
                interpretation="The dataset does not contain numeric columns.",
            )

        description = numeric_dataframe.describe().to_dict()

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters=parameters,
            metrics={
                "description": description,
                "numeric_columns": list(numeric_dataframe.columns),
            },
            interpretation="Generated descriptive statistics for numeric columns.",
        )


class CorrelationMatrixStep(PipelineStep):
    name = "correlation_matrix"
    display_name = "Correlation matrix"
    category = "statistics"
    description = "Computes the correlation matrix for numeric columns."
    output_type = "result"

    parameters = [
        StepParameter(
            name="method",
            label="Correlation method",
            parameter_type="select",
            required=True,
            default="pearson",
            options=["pearson", "spearman", "kendall"],
            description="Correlation coefficient method.",
        )
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}
        method = parameters.get("method", "pearson")

        numeric_dataframe = dataframe.select_dtypes(include="number")

        if numeric_dataframe.shape[1] < 2:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters=parameters,
                metrics={},
                warnings=["At least two numeric columns are required."],
                interpretation="Correlation matrix could not be computed.",
            )

        correlation = numeric_dataframe.corr(method=method).to_dict()

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters=parameters,
            metrics={
                "correlation_matrix": correlation,
                "method": method,
                "columns": list(numeric_dataframe.columns),
            },
            interpretation=f"Computed {method} correlation matrix.",
        )