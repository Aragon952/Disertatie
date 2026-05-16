from typing import Any

import pandas as pd
import numpy as np

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
    

def get_numeric_columns(
    dataframe: pd.DataFrame,
    columns: list[str] | None,
) -> tuple[list[str], list[str]]:
    """
    Returns valid numeric columns and skipped columns.
    """
    numeric_dataframe = dataframe.select_dtypes(include="number")

    if columns:
        valid_columns = [
            column
            for column in columns
            if column in numeric_dataframe.columns
        ]

        skipped_columns = [
            column
            for column in columns
            if column not in numeric_dataframe.columns
        ]

        return valid_columns, skipped_columns

    return list(numeric_dataframe.columns), []


def build_scaling_metrics(
    original_dataframe: pd.DataFrame,
    scaled_dataframe: pd.DataFrame,
    columns: list[str],
    method: str,
    implementation: str,
    skipped_columns: list[str],
    extra_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Builds comparable metrics for scaling methods.
    """
    metrics: dict[str, Any] = {
        "method": method,
        "implementation": implementation,
        "columns": columns,
        "columns_count": len(columns),
        "skipped_columns": skipped_columns,
        "skipped_columns_count": len(skipped_columns),
    }

    if not columns:
        metrics.update(
            {
                "mean_abs_max_after": None,
                "std_mean_after": None,
                "min_after": None,
                "max_after": None,
            }
        )
        return metrics

    scaled_numeric = scaled_dataframe[columns]

    means_after = scaled_numeric.mean(numeric_only=True).to_dict()
    stds_after = scaled_numeric.std(ddof=0, numeric_only=True).to_dict()
    mins_after = scaled_numeric.min(numeric_only=True).to_dict()
    maxs_after = scaled_numeric.max(numeric_only=True).to_dict()

    metrics.update(
        {
            "mean_abs_max_after": round(
                float(max(abs(value) for value in means_after.values())),
                6,
            ),
            "std_mean_after": round(
                float(np.mean(list(stds_after.values()))),
                6,
            ),
            "min_after": round(
                float(min(mins_after.values())),
                6,
            ),
            "max_after": round(
                float(max(maxs_after.values())),
                6,
            ),
            "means_after": {
                column: round(float(value), 6)
                for column, value in means_after.items()
            },
            "stds_after": {
                column: round(float(value), 6)
                for column, value in stds_after.items()
            },
            "mins_after": {
                column: round(float(value), 6)
                for column, value in mins_after.items()
            },
            "maxs_after": {
                column: round(float(value), 6)
                for column, value in maxs_after.items()
            },
        }
    )

    if extra_metrics:
        metrics.update(extra_metrics)

    return metrics


class StandardScalerSklearnStep(PipelineStep):
    name = "standard_scaler_sklearn"
    display_name = "Standard Scaler - scikit-learn"
    category = "preprocessing"
    description = "Standardizes numeric columns using sklearn.preprocessing.StandardScaler."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns to standardize.",
        )
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.preprocessing import StandardScaler

        parameters = parameters or {}
        columns = parameters.get("columns")

        numeric_columns, skipped_columns = get_numeric_columns(
            dataframe=dataframe,
            columns=columns,
        )

        if not numeric_columns:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={"columns": columns},
                metrics=build_scaling_metrics(
                    original_dataframe=dataframe,
                    scaled_dataframe=dataframe,
                    columns=[],
                    method="standard_scaler",
                    implementation="sklearn",
                    skipped_columns=skipped_columns,
                ),
                warnings=["No numeric columns available for standardization."],
                interpretation="No columns were standardized.",
                output_data=dataframe.copy(),
            )

        result_dataframe = dataframe.copy()

        scaler = StandardScaler()
        result_dataframe[numeric_columns] = scaler.fit_transform(
            result_dataframe[numeric_columns]
        )

        metrics = build_scaling_metrics(
            original_dataframe=dataframe,
            scaled_dataframe=result_dataframe,
            columns=numeric_columns,
            method="standard_scaler",
            implementation="sklearn",
            skipped_columns=skipped_columns,
            extra_metrics={
                "scaler_mean": {
                    column: round(float(value), 6)
                    for column, value in zip(numeric_columns, scaler.mean_)
                },
                "scaler_scale": {
                    column: round(float(value), 6)
                    for column, value in zip(numeric_columns, scaler.scale_)
                },
            },
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
            parameters={"columns": numeric_columns},
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Standardized {len(numeric_columns)} columns using scikit-learn.",
            output_data=result_dataframe,
        )


class StandardScalerScipyStep(PipelineStep):
    name = "standard_scaler_scipy"
    display_name = "Standard Scaler - SciPy"
    category = "preprocessing"
    description = "Standardizes numeric columns using scipy.stats.zscore."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns to standardize.",
        ),
        StepParameter(
            name="ddof",
            label="Delta degrees of freedom",
            parameter_type="number",
            required=True,
            default=0,
            description="ddof used by scipy.stats.zscore. Use 0 to match scikit-learn more closely.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from scipy.stats import zscore

        parameters = parameters or {}
        columns = parameters.get("columns")
        ddof = int(parameters.get("ddof", 0))

        numeric_columns, skipped_columns = get_numeric_columns(
            dataframe=dataframe,
            columns=columns,
        )

        if not numeric_columns:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "ddof": ddof,
                },
                metrics=build_scaling_metrics(
                    original_dataframe=dataframe,
                    scaled_dataframe=dataframe,
                    columns=[],
                    method="standard_scaler",
                    implementation="scipy",
                    skipped_columns=skipped_columns,
                    extra_metrics={"ddof": ddof},
                ),
                warnings=["No numeric columns available for standardization."],
                interpretation="No columns were standardized.",
                output_data=dataframe.copy(),
            )

        result_dataframe = dataframe.copy()

        result_dataframe[numeric_columns] = zscore(
            result_dataframe[numeric_columns],
            axis=0,
            ddof=ddof,
            nan_policy="omit",
        )

        metrics = build_scaling_metrics(
            original_dataframe=dataframe,
            scaled_dataframe=result_dataframe,
            columns=numeric_columns,
            method="standard_scaler",
            implementation="scipy",
            skipped_columns=skipped_columns,
            extra_metrics={"ddof": ddof},
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
                "ddof": ddof,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Standardized {len(numeric_columns)} columns using SciPy zscore.",
            output_data=result_dataframe,
        )


class StandardScalerCustomStep(PipelineStep):
    name = "standard_scaler_custom"
    display_name = "Standard Scaler - Custom"
    category = "preprocessing"
    description = "Standardizes numeric columns using a custom implementation."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns to standardize.",
        ),
        StepParameter(
            name="ddof",
            label="Delta degrees of freedom",
            parameter_type="number",
            required=True,
            default=0,
            description="ddof used for standard deviation. Use 0 to match scikit-learn more closely.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}
        columns = parameters.get("columns")
        ddof = int(parameters.get("ddof", 0))

        numeric_columns, skipped_columns = get_numeric_columns(
            dataframe=dataframe,
            columns=columns,
        )

        if not numeric_columns:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "ddof": ddof,
                },
                metrics=build_scaling_metrics(
                    original_dataframe=dataframe,
                    scaled_dataframe=dataframe,
                    columns=[],
                    method="standard_scaler",
                    implementation="custom",
                    skipped_columns=skipped_columns,
                    extra_metrics={"ddof": ddof},
                ),
                warnings=["No numeric columns available for standardization."],
                interpretation="No columns were standardized.",
                output_data=dataframe.copy(),
            )

        result_dataframe = dataframe.copy()

        means = result_dataframe[numeric_columns].mean()
        stds = result_dataframe[numeric_columns].std(ddof=ddof)

        zero_std_columns = [
            column
            for column in numeric_columns
            if stds[column] == 0 or pd.isna(stds[column])
        ]

        valid_columns = [
            column
            for column in numeric_columns
            if column not in zero_std_columns
        ]

        if valid_columns:
            result_dataframe[valid_columns] = (
                result_dataframe[valid_columns] - means[valid_columns]
            ) / stds[valid_columns]

        metrics = build_scaling_metrics(
            original_dataframe=dataframe,
            scaled_dataframe=result_dataframe,
            columns=valid_columns,
            method="standard_scaler",
            implementation="custom",
            skipped_columns=skipped_columns + zero_std_columns,
            extra_metrics={
                "ddof": ddof,
                "zero_std_columns": zero_std_columns,
                "zero_std_columns_count": len(zero_std_columns),
            },
        )

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped non-numeric or missing columns: {skipped_columns}."
            )

        if zero_std_columns:
            warnings.append(
                f"Skipped columns with zero or invalid standard deviation: {zero_std_columns}."
            )

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters={
                "columns": numeric_columns,
                "ddof": ddof,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Standardized {len(valid_columns)} columns using a custom implementation.",
            output_data=result_dataframe,
        )


class MinMaxScalerSklearnStep(PipelineStep):
    name = "minmax_scaler_sklearn"
    display_name = "Min-Max Scaler - scikit-learn"
    category = "preprocessing"
    description = "Scales numeric columns to a selected range using sklearn.preprocessing.MinMaxScaler."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns to scale.",
        ),
        StepParameter(
            name="feature_min",
            label="Feature range minimum",
            parameter_type="number",
            required=True,
            default=0.0,
            description="Minimum value of the output range.",
        ),
        StepParameter(
            name="feature_max",
            label="Feature range maximum",
            parameter_type="number",
            required=True,
            default=1.0,
            description="Maximum value of the output range.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.preprocessing import MinMaxScaler

        parameters = parameters or {}

        columns = parameters.get("columns")
        feature_min = float(parameters.get("feature_min", 0.0))
        feature_max = float(parameters.get("feature_max", 1.0))

        if feature_min >= feature_max:
            raise ValueError("feature_min must be smaller than feature_max.")

        numeric_columns, skipped_columns = get_numeric_columns(
            dataframe=dataframe,
            columns=columns,
        )

        if not numeric_columns:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "feature_min": feature_min,
                    "feature_max": feature_max,
                },
                metrics=build_scaling_metrics(
                    original_dataframe=dataframe,
                    scaled_dataframe=dataframe,
                    columns=[],
                    method="minmax_scaler",
                    implementation="sklearn",
                    skipped_columns=skipped_columns,
                    extra_metrics={
                        "feature_min": feature_min,
                        "feature_max": feature_max,
                    },
                ),
                warnings=["No numeric columns available for min-max scaling."],
                interpretation="No columns were scaled.",
                output_data=dataframe.copy(),
            )

        result_dataframe = dataframe.copy()

        scaler = MinMaxScaler(feature_range=(feature_min, feature_max))
        result_dataframe[numeric_columns] = scaler.fit_transform(
            result_dataframe[numeric_columns]
        )

        metrics = build_scaling_metrics(
            original_dataframe=dataframe,
            scaled_dataframe=result_dataframe,
            columns=numeric_columns,
            method="minmax_scaler",
            implementation="sklearn",
            skipped_columns=skipped_columns,
            extra_metrics={
                "feature_min": feature_min,
                "feature_max": feature_max,
                "data_min": {
                    column: round(float(value), 6)
                    for column, value in zip(numeric_columns, scaler.data_min_)
                },
                "data_max": {
                    column: round(float(value), 6)
                    for column, value in zip(numeric_columns, scaler.data_max_)
                },
            },
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
                "feature_min": feature_min,
                "feature_max": feature_max,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Scaled {len(numeric_columns)} columns using scikit-learn MinMaxScaler.",
            output_data=result_dataframe,
        )


class RobustScalerSklearnStep(PipelineStep):
    name = "robust_scaler_sklearn"
    display_name = "Robust Scaler - scikit-learn"
    category = "preprocessing"
    description = "Scales numeric columns using median and IQR with sklearn.preprocessing.RobustScaler."
    output_type = "dataframe"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns to robust-scale.",
        )
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.preprocessing import RobustScaler

        parameters = parameters or {}
        columns = parameters.get("columns")

        numeric_columns, skipped_columns = get_numeric_columns(
            dataframe=dataframe,
            columns=columns,
        )

        if not numeric_columns:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={"columns": columns},
                metrics=build_scaling_metrics(
                    original_dataframe=dataframe,
                    scaled_dataframe=dataframe,
                    columns=[],
                    method="robust_scaler",
                    implementation="sklearn",
                    skipped_columns=skipped_columns,
                ),
                warnings=["No numeric columns available for robust scaling."],
                interpretation="No columns were scaled.",
                output_data=dataframe.copy(),
            )

        result_dataframe = dataframe.copy()

        scaler = RobustScaler()
        result_dataframe[numeric_columns] = scaler.fit_transform(
            result_dataframe[numeric_columns]
        )

        metrics = build_scaling_metrics(
            original_dataframe=dataframe,
            scaled_dataframe=result_dataframe,
            columns=numeric_columns,
            method="robust_scaler",
            implementation="sklearn",
            skipped_columns=skipped_columns,
            extra_metrics={
                "center": {
                    column: round(float(value), 6)
                    for column, value in zip(numeric_columns, scaler.center_)
                },
                "scale": {
                    column: round(float(value), 6)
                    for column, value in zip(numeric_columns, scaler.scale_)
                },
            },
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
            parameters={"columns": numeric_columns},
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Scaled {len(numeric_columns)} columns using scikit-learn RobustScaler.",
            output_data=result_dataframe,
        )
    

def prepare_clustering_data(
    dataframe: pd.DataFrame,
    columns: list[str] | None,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """
    Selects numeric columns and removes rows with missing values for clustering.

    Returns:
    - clean numeric dataframe
    - selected numeric columns
    - skipped columns
    """
    numeric_dataframe = dataframe.select_dtypes(include="number")

    if columns:
        selected_columns = [
            column
            for column in columns
            if column in numeric_dataframe.columns
        ]

        skipped_columns = [
            column
            for column in columns
            if column not in numeric_dataframe.columns
        ]
    else:
        selected_columns = list(numeric_dataframe.columns)
        skipped_columns = []

    if not selected_columns:
        return pd.DataFrame(), [], skipped_columns

    clean_dataframe = numeric_dataframe[selected_columns].dropna()

    return clean_dataframe, selected_columns, skipped_columns


def build_cluster_sizes(labels: np.ndarray) -> dict[str, int]:
    """
    Builds cluster size dictionary from labels.
    """
    unique_labels, counts = np.unique(labels, return_counts=True)

    return {
        str(int(label)): int(count)
        for label, count in zip(unique_labels, counts)
    }


def calculate_silhouette_score_safe(
    data: np.ndarray,
    labels: np.ndarray,
) -> float | None:
    """
    Calculates silhouette score when possible.

    Silhouette score requires at least 2 clusters and fewer clusters than samples.
    Noise label -1 from DBSCAN is kept as a label, but the score may not always be meaningful.
    """
    try:
        from sklearn.metrics import silhouette_score

        unique_labels = set(labels)

        if len(unique_labels) < 2:
            return None

        if len(unique_labels) >= len(labels):
            return None

        return round(float(silhouette_score(data, labels)), 6)

    except Exception:
        return None


def build_clustering_metrics(
    method: str,
    implementation: str,
    columns: list[str],
    skipped_columns: list[str],
    labels: np.ndarray,
    data: np.ndarray,
    extra_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Builds comparable metrics for clustering methods.
    """
    unique_labels = sorted(set(int(label) for label in labels))
    cluster_sizes = build_cluster_sizes(labels)
    silhouette = calculate_silhouette_score_safe(data, labels)

    metrics: dict[str, Any] = {
        "method": method,
        "implementation": implementation,
        "columns": columns,
        "columns_count": len(columns),
        "skipped_columns": skipped_columns,
        "skipped_columns_count": len(skipped_columns),
        "rows_used": int(len(labels)),
        "clusters_count": len(unique_labels),
        "cluster_labels": unique_labels,
        "cluster_sizes": cluster_sizes,
        "silhouette_score": silhouette,
    }

    if extra_metrics:
        metrics.update(extra_metrics)

    return metrics


def calculate_kmeans_inertia(
    data: np.ndarray,
    labels: np.ndarray,
    centroids: np.ndarray,
) -> float:
    """
    Calculates K-Means inertia manually.
    """
    inertia = 0.0

    for row, label in zip(data, labels):
        centroid = centroids[int(label)]
        inertia += float(np.sum((row - centroid) ** 2))

    return round(inertia, 6)


def initialize_custom_centroids(
    data: np.ndarray,
    n_clusters: int,
    random_state: int,
) -> np.ndarray:
    """
    Initializes centroids by randomly selecting existing rows.
    """
    rng = np.random.default_rng(random_state)

    indices = rng.choice(
        len(data),
        size=n_clusters,
        replace=False,
    )

    return data[indices].astype(float)

class KMeansSklearnStep(PipelineStep):
    name = "kmeans_sklearn"
    display_name = "K-Means - scikit-learn"
    category = "machine_learning"
    description = "Clusters numeric data using sklearn.cluster.KMeans."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns used for clustering.",
        ),
        StepParameter(
            name="n_clusters",
            label="Number of clusters",
            parameter_type="number",
            required=True,
            default=3,
            description="Number of clusters.",
        ),
        StepParameter(
            name="random_state",
            label="Random state",
            parameter_type="number",
            required=True,
            default=42,
            description="Random seed for reproducibility.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.cluster import KMeans

        parameters = parameters or {}

        columns = parameters.get("columns")
        n_clusters = int(parameters.get("n_clusters", 3))
        random_state = int(parameters.get("random_state", 42))

        clean_dataframe, selected_columns, skipped_columns = prepare_clustering_data(
            dataframe=dataframe,
            columns=columns,
        )

        if clean_dataframe.empty:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "n_clusters": n_clusters,
                    "random_state": random_state,
                },
                metrics={
                    "method": "kmeans",
                    "implementation": "sklearn",
                    "columns": [],
                    "columns_count": 0,
                    "rows_used": 0,
                    "clusters_count": 0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                },
                warnings=["No valid numeric data available for K-Means clustering."],
                interpretation="K-Means could not be computed.",
            )

        if n_clusters < 2:
            raise ValueError("n_clusters must be at least 2.")

        if n_clusters > len(clean_dataframe):
            raise ValueError("n_clusters cannot be greater than the number of valid rows.")

        data = clean_dataframe.to_numpy(dtype=float)

        model = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=10,
        )

        labels = model.fit_predict(data)

        metrics = build_clustering_metrics(
            method="kmeans",
            implementation="sklearn",
            columns=selected_columns,
            skipped_columns=skipped_columns,
            labels=labels,
            data=data,
            extra_metrics={
                "n_clusters": n_clusters,
                "random_state": random_state,
                "inertia": round(float(model.inertia_), 6),
                "iterations": int(model.n_iter_),
                "centroids": {
                    f"cluster_{index}": [
                        round(float(value), 6)
                        for value in centroid
                    ]
                    for index, centroid in enumerate(model.cluster_centers_)
                },
            },
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
                "columns": selected_columns,
                "n_clusters": n_clusters,
                "random_state": random_state,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Computed K-Means clustering with {n_clusters} clusters using scikit-learn.",
        )
    
class KMeansSklearnStep(PipelineStep):
    name = "kmeans_sklearn"
    display_name = "K-Means - scikit-learn"
    category = "machine_learning"
    description = "Clusters numeric data using sklearn.cluster.KMeans."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns used for clustering.",
        ),
        StepParameter(
            name="n_clusters",
            label="Number of clusters",
            parameter_type="number",
            required=True,
            default=3,
            description="Number of clusters.",
        ),
        StepParameter(
            name="random_state",
            label="Random state",
            parameter_type="number",
            required=True,
            default=42,
            description="Random seed for reproducibility.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.cluster import KMeans

        parameters = parameters or {}

        columns = parameters.get("columns")
        n_clusters = int(parameters.get("n_clusters", 3))
        random_state = int(parameters.get("random_state", 42))

        clean_dataframe, selected_columns, skipped_columns = prepare_clustering_data(
            dataframe=dataframe,
            columns=columns,
        )

        if clean_dataframe.empty:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "n_clusters": n_clusters,
                    "random_state": random_state,
                },
                metrics={
                    "method": "kmeans",
                    "implementation": "sklearn",
                    "columns": [],
                    "columns_count": 0,
                    "rows_used": 0,
                    "clusters_count": 0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                },
                warnings=["No valid numeric data available for K-Means clustering."],
                interpretation="K-Means could not be computed.",
            )

        if n_clusters < 2:
            raise ValueError("n_clusters must be at least 2.")

        if n_clusters > len(clean_dataframe):
            raise ValueError("n_clusters cannot be greater than the number of valid rows.")

        data = clean_dataframe.to_numpy(dtype=float)

        model = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=10,
        )

        labels = model.fit_predict(data)

        metrics = build_clustering_metrics(
            method="kmeans",
            implementation="sklearn",
            columns=selected_columns,
            skipped_columns=skipped_columns,
            labels=labels,
            data=data,
            extra_metrics={
                "n_clusters": n_clusters,
                "random_state": random_state,
                "inertia": round(float(model.inertia_), 6),
                "iterations": int(model.n_iter_),
                "centroids": {
                    f"cluster_{index}": [
                        round(float(value), 6)
                        for value in centroid
                    ]
                    for index, centroid in enumerate(model.cluster_centers_)
                },
            },
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
                "columns": selected_columns,
                "n_clusters": n_clusters,
                "random_state": random_state,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Computed K-Means clustering with {n_clusters} clusters using scikit-learn.",
        )
    
class KMeansScipyStep(PipelineStep):
    name = "kmeans_scipy"
    display_name = "K-Means - SciPy"
    category = "machine_learning"
    description = "Clusters numeric data using scipy.cluster.vq.kmeans2."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns used for clustering.",
        ),
        StepParameter(
            name="n_clusters",
            label="Number of clusters",
            parameter_type="number",
            required=True,
            default=3,
            description="Number of clusters.",
        ),
        StepParameter(
            name="iterations",
            label="Iterations",
            parameter_type="number",
            required=True,
            default=20,
            description="Number of iterations.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from scipy.cluster.vq import kmeans2

        parameters = parameters or {}

        columns = parameters.get("columns")
        n_clusters = int(parameters.get("n_clusters", 3))
        iterations = int(parameters.get("iterations", 20))

        clean_dataframe, selected_columns, skipped_columns = prepare_clustering_data(
            dataframe=dataframe,
            columns=columns,
        )

        if clean_dataframe.empty:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "n_clusters": n_clusters,
                    "iterations": iterations,
                },
                metrics={
                    "method": "kmeans",
                    "implementation": "scipy",
                    "columns": [],
                    "columns_count": 0,
                    "rows_used": 0,
                    "clusters_count": 0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                },
                warnings=["No valid numeric data available for K-Means clustering."],
                interpretation="K-Means could not be computed.",
            )

        if n_clusters < 2:
            raise ValueError("n_clusters must be at least 2.")

        if n_clusters > len(clean_dataframe):
            raise ValueError("n_clusters cannot be greater than the number of valid rows.")

        data = clean_dataframe.to_numpy(dtype=float)

        centroids, labels = kmeans2(
            data=data,
            k=n_clusters,
            iter=iterations,
            minit="points",
        )

        labels = labels.astype(int)

        inertia = calculate_kmeans_inertia(
            data=data,
            labels=labels,
            centroids=centroids,
        )

        metrics = build_clustering_metrics(
            method="kmeans",
            implementation="scipy",
            columns=selected_columns,
            skipped_columns=skipped_columns,
            labels=labels,
            data=data,
            extra_metrics={
                "n_clusters": n_clusters,
                "iterations": iterations,
                "inertia": inertia,
                "centroids": {
                    f"cluster_{index}": [
                        round(float(value), 6)
                        for value in centroid
                    ]
                    for index, centroid in enumerate(centroids)
                },
            },
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
                "columns": selected_columns,
                "n_clusters": n_clusters,
                "iterations": iterations,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Computed K-Means clustering with {n_clusters} clusters using SciPy.",
        )
    
class KMeansCustomStep(PipelineStep):
    name = "kmeans_custom"
    display_name = "K-Means - Custom"
    category = "machine_learning"
    description = "Clusters numeric data using a custom K-Means implementation."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns used for clustering.",
        ),
        StepParameter(
            name="n_clusters",
            label="Number of clusters",
            parameter_type="number",
            required=True,
            default=3,
            description="Number of clusters.",
        ),
        StepParameter(
            name="max_iterations",
            label="Max iterations",
            parameter_type="number",
            required=True,
            default=100,
            description="Maximum number of K-Means iterations.",
        ),
        StepParameter(
            name="random_state",
            label="Random state",
            parameter_type="number",
            required=True,
            default=42,
            description="Random seed for reproducibility.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}

        columns = parameters.get("columns")
        n_clusters = int(parameters.get("n_clusters", 3))
        max_iterations = int(parameters.get("max_iterations", 100))
        random_state = int(parameters.get("random_state", 42))

        clean_dataframe, selected_columns, skipped_columns = prepare_clustering_data(
            dataframe=dataframe,
            columns=columns,
        )

        if clean_dataframe.empty:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "n_clusters": n_clusters,
                    "max_iterations": max_iterations,
                    "random_state": random_state,
                },
                metrics={
                    "method": "kmeans",
                    "implementation": "custom",
                    "columns": [],
                    "columns_count": 0,
                    "rows_used": 0,
                    "clusters_count": 0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                },
                warnings=["No valid numeric data available for K-Means clustering."],
                interpretation="K-Means could not be computed.",
            )

        if n_clusters < 2:
            raise ValueError("n_clusters must be at least 2.")

        if n_clusters > len(clean_dataframe):
            raise ValueError("n_clusters cannot be greater than the number of valid rows.")

        data = clean_dataframe.to_numpy(dtype=float)

        centroids = initialize_custom_centroids(
            data=data,
            n_clusters=n_clusters,
            random_state=random_state,
        )

        labels = np.zeros(len(data), dtype=int)
        iterations_used = 0

        for iteration in range(max_iterations):
            distances = np.linalg.norm(
                data[:, np.newaxis, :] - centroids[np.newaxis, :, :],
                axis=2,
            )

            new_labels = np.argmin(distances, axis=1)

            new_centroids = centroids.copy()

            for cluster_index in range(n_clusters):
                cluster_points = data[new_labels == cluster_index]

                if len(cluster_points) > 0:
                    new_centroids[cluster_index] = cluster_points.mean(axis=0)

            iterations_used = iteration + 1

            if np.array_equal(labels, new_labels):
                labels = new_labels
                centroids = new_centroids
                break

            labels = new_labels
            centroids = new_centroids

        inertia = calculate_kmeans_inertia(
            data=data,
            labels=labels,
            centroids=centroids,
        )

        metrics = build_clustering_metrics(
            method="kmeans",
            implementation="custom",
            columns=selected_columns,
            skipped_columns=skipped_columns,
            labels=labels,
            data=data,
            extra_metrics={
                "n_clusters": n_clusters,
                "max_iterations": max_iterations,
                "iterations": int(iterations_used),
                "random_state": random_state,
                "inertia": inertia,
                "centroids": {
                    f"cluster_{index}": [
                        round(float(value), 6)
                        for value in centroid
                    ]
                    for index, centroid in enumerate(centroids)
                },
            },
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
                "columns": selected_columns,
                "n_clusters": n_clusters,
                "max_iterations": max_iterations,
                "random_state": random_state,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Computed K-Means clustering with {n_clusters} clusters using a custom implementation.",
        )
    
class AgglomerativeClusteringSklearnStep(PipelineStep):
    name = "agglomerative_clustering_sklearn"
    display_name = "Agglomerative Clustering - scikit-learn"
    category = "machine_learning"
    description = "Clusters numeric data using sklearn.cluster.AgglomerativeClustering."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns used for clustering.",
        ),
        StepParameter(
            name="n_clusters",
            label="Number of clusters",
            parameter_type="number",
            required=True,
            default=3,
            description="Number of clusters.",
        ),
        StepParameter(
            name="linkage",
            label="Linkage",
            parameter_type="select",
            required=True,
            default="ward",
            options=["ward", "complete", "average", "single"],
            description="Linkage criterion.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.cluster import AgglomerativeClustering

        parameters = parameters or {}

        columns = parameters.get("columns")
        n_clusters = int(parameters.get("n_clusters", 3))
        linkage = parameters.get("linkage", "ward")

        clean_dataframe, selected_columns, skipped_columns = prepare_clustering_data(
            dataframe=dataframe,
            columns=columns,
        )

        if clean_dataframe.empty:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "n_clusters": n_clusters,
                    "linkage": linkage,
                },
                metrics={
                    "method": "agglomerative_clustering",
                    "implementation": "sklearn",
                    "columns": [],
                    "columns_count": 0,
                    "rows_used": 0,
                    "clusters_count": 0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                },
                warnings=["No valid numeric data available for Agglomerative Clustering."],
                interpretation="Agglomerative Clustering could not be computed.",
            )

        if n_clusters < 2:
            raise ValueError("n_clusters must be at least 2.")

        if n_clusters > len(clean_dataframe):
            raise ValueError("n_clusters cannot be greater than the number of valid rows.")

        data = clean_dataframe.to_numpy(dtype=float)

        model = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage=linkage,
        )

        labels = model.fit_predict(data)

        metrics = build_clustering_metrics(
            method="agglomerative_clustering",
            implementation="sklearn",
            columns=selected_columns,
            skipped_columns=skipped_columns,
            labels=labels,
            data=data,
            extra_metrics={
                "n_clusters": n_clusters,
                "linkage": linkage,
            },
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
                "columns": selected_columns,
                "n_clusters": n_clusters,
                "linkage": linkage,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=f"Computed Agglomerative Clustering with {n_clusters} clusters.",
        )
    
class DBSCANSklearnStep(PipelineStep):
    name = "dbscan_sklearn"
    display_name = "DBSCAN - scikit-learn"
    category = "machine_learning"
    description = "Clusters numeric data using sklearn.cluster.DBSCAN."
    output_type = "result"

    parameters = [
        StepParameter(
            name="columns",
            label="Columns",
            parameter_type="columns",
            required=False,
            default=None,
            description="Optional numeric columns used for clustering.",
        ),
        StepParameter(
            name="eps",
            label="Epsilon",
            parameter_type="number",
            required=True,
            default=0.5,
            description="Maximum distance between two samples to be considered neighbors.",
        ),
        StepParameter(
            name="min_samples",
            label="Minimum samples",
            parameter_type="number",
            required=True,
            default=5,
            description="Minimum samples required to form a dense region.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.cluster import DBSCAN

        parameters = parameters or {}

        columns = parameters.get("columns")
        eps = float(parameters.get("eps", 0.5))
        min_samples = int(parameters.get("min_samples", 5))

        clean_dataframe, selected_columns, skipped_columns = prepare_clustering_data(
            dataframe=dataframe,
            columns=columns,
        )

        if clean_dataframe.empty:
            return StepResult(
                step_name=self.name,
                category=self.category,
                output_type=self.output_type,
                parameters={
                    "columns": columns,
                    "eps": eps,
                    "min_samples": min_samples,
                },
                metrics={
                    "method": "dbscan",
                    "implementation": "sklearn",
                    "columns": [],
                    "columns_count": 0,
                    "rows_used": 0,
                    "clusters_count": 0,
                    "noise_points": 0,
                    "skipped_columns": skipped_columns,
                    "skipped_columns_count": len(skipped_columns),
                },
                warnings=["No valid numeric data available for DBSCAN."],
                interpretation="DBSCAN could not be computed.",
            )

        if eps <= 0:
            raise ValueError("eps must be greater than 0.")

        if min_samples < 1:
            raise ValueError("min_samples must be at least 1.")

        data = clean_dataframe.to_numpy(dtype=float)

        model = DBSCAN(
            eps=eps,
            min_samples=min_samples,
        )

        labels = model.fit_predict(data)

        unique_labels = set(labels)
        noise_points = int(np.sum(labels == -1))
        clusters_without_noise = [
            label
            for label in unique_labels
            if label != -1
        ]

        metrics = build_clustering_metrics(
            method="dbscan",
            implementation="sklearn",
            columns=selected_columns,
            skipped_columns=skipped_columns,
            labels=labels,
            data=data,
            extra_metrics={
                "eps": eps,
                "min_samples": min_samples,
                "noise_points": noise_points,
                "noise_percentage": round(
                    float((noise_points / len(labels)) * 100),
                    6,
                ),
                "clusters_without_noise_count": len(clusters_without_noise),
            },
        )

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped non-numeric or missing columns: {skipped_columns}."
            )

        if len(clusters_without_noise) == 0:
            warnings.append("DBSCAN did not find any non-noise clusters.")

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters={
                "columns": selected_columns,
                "eps": eps,
                "min_samples": min_samples,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation=(
                f"Computed DBSCAN clustering with {len(clusters_without_noise)} "
                f"clusters and {noise_points} noise points."
            ),
        )
    
def prepare_regression_data(
    dataframe: pd.DataFrame,
    feature_columns: list[str] | None,
    target_column: str | None,
) -> tuple[pd.DataFrame, list[str], str, list[str]]:
    """
    Prepares numeric feature and target data for regression.

    Returns:
    - clean dataframe with selected features + target
    - valid feature columns
    - target column
    - skipped columns
    """
    if not target_column:
        raise ValueError("target_column is required.")

    if target_column not in dataframe.columns:
        raise ValueError(f"Target column '{target_column}' was not found.")

    if not pd.api.types.is_numeric_dtype(dataframe[target_column]):
        raise ValueError("Target column must be numeric.")

    numeric_dataframe = dataframe.select_dtypes(include="number")

    if feature_columns:
        valid_features = [
            column
            for column in feature_columns
            if column in numeric_dataframe.columns and column != target_column
        ]

        skipped_columns = [
            column
            for column in feature_columns
            if column not in numeric_dataframe.columns or column == target_column
        ]
    else:
        valid_features = [
            column
            for column in numeric_dataframe.columns
            if column != target_column
        ]
        skipped_columns = []

    if not valid_features:
        raise ValueError("At least one numeric feature column is required.")

    selected_columns = valid_features + [target_column]

    clean_dataframe = dataframe[selected_columns].dropna()

    if len(clean_dataframe) < 3:
        raise ValueError("At least 3 valid rows are required for linear regression.")

    return clean_dataframe, valid_features, target_column, skipped_columns


def split_regression_data(
    clean_dataframe: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    test_size: float,
    random_state: int,
):
    """
    Splits regression data into train/test sets.
    """
    from sklearn.model_selection import train_test_split

    x = clean_dataframe[feature_columns].to_numpy(dtype=float)
    y = clean_dataframe[target_column].to_numpy(dtype=float)

    return train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
    )


def calculate_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """
    Calculates common regression metrics.
    """
    residuals = y_true - y_pred

    mae = float(np.mean(np.abs(residuals)))
    mse = float(np.mean(residuals ** 2))
    rmse = float(np.sqrt(mse))

    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))

    if ss_tot == 0:
        r2 = None
    else:
        r2 = 1 - (ss_res / ss_tot)

    return {
        "r2_score": round(float(r2), 6) if r2 is not None else None,
        "mean_absolute_error": round(mae, 6),
        "mean_squared_error": round(mse, 6),
        "root_mean_squared_error": round(rmse, 6),
    }


def build_regression_metrics(
    method: str,
    implementation: str,
    target_column: str,
    feature_columns: list[str],
    skipped_columns: list[str],
    train_rows: int,
    test_rows: int,
    y_test: np.ndarray,
    y_pred: np.ndarray,
    coefficients: dict[str, float],
    intercept: float,
    extra_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Builds comparable metrics for linear regression implementations.
    """
    regression_metrics = calculate_regression_metrics(
        y_true=y_test,
        y_pred=y_pred,
    )

    metrics: dict[str, Any] = {
        "method": method,
        "implementation": implementation,
        "target_column": target_column,
        "feature_columns": feature_columns,
        "feature_columns_count": len(feature_columns),
        "skipped_columns": skipped_columns,
        "skipped_columns_count": len(skipped_columns),
        "train_rows": int(train_rows),
        "test_rows": int(test_rows),
        "coefficients": coefficients,
        "coefficients_count": len(coefficients),
        "intercept": round(float(intercept), 6),
        **regression_metrics,
    }

    if extra_metrics:
        metrics.update(extra_metrics)

    return metrics

class LinearRegressionSklearnStep(PipelineStep):
    name = "linear_regression_sklearn"
    display_name = "Linear Regression - scikit-learn"
    category = "machine_learning"
    description = "Fits a linear regression model using sklearn.linear_model.LinearRegression."
    output_type = "result"

    parameters = [
        StepParameter(
            name="target_column",
            label="Target column",
            parameter_type="column",
            required=True,
            default=None,
            description="Numeric column to predict.",
        ),
        StepParameter(
            name="feature_columns",
            label="Feature columns",
            parameter_type="columns",
            required=True,
            default=None,
            description="Numeric columns used as predictors.",
        ),
        StepParameter(
            name="test_size",
            label="Test size",
            parameter_type="number",
            required=True,
            default=0.25,
            description="Proportion of data used for testing.",
        ),
        StepParameter(
            name="random_state",
            label="Random state",
            parameter_type="number",
            required=True,
            default=42,
            description="Random seed for train/test split.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        from sklearn.linear_model import LinearRegression

        parameters = parameters or {}

        target_column = parameters.get("target_column")
        feature_columns = parameters.get("feature_columns")
        test_size = float(parameters.get("test_size", 0.25))
        random_state = int(parameters.get("random_state", 42))

        if test_size <= 0 or test_size >= 1:
            raise ValueError("test_size must be between 0 and 1.")

        clean_dataframe, valid_features, target_column, skipped_columns = prepare_regression_data(
            dataframe=dataframe,
            feature_columns=feature_columns,
            target_column=target_column,
        )

        x_train, x_test, y_train, y_test = split_regression_data(
            clean_dataframe=clean_dataframe,
            feature_columns=valid_features,
            target_column=target_column,
            test_size=test_size,
            random_state=random_state,
        )

        model = LinearRegression()
        model.fit(x_train, y_train)

        y_pred = model.predict(x_test)

        coefficients = {
            column: round(float(value), 6)
            for column, value in zip(valid_features, model.coef_)
        }

        metrics = build_regression_metrics(
            method="linear_regression",
            implementation="sklearn",
            target_column=target_column,
            feature_columns=valid_features,
            skipped_columns=skipped_columns,
            train_rows=len(x_train),
            test_rows=len(x_test),
            y_test=y_test,
            y_pred=y_pred,
            coefficients=coefficients,
            intercept=float(model.intercept_),
            extra_metrics={
                "test_size": test_size,
                "random_state": random_state,
            },
        )

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped non-numeric, missing, or target columns: {skipped_columns}."
            )

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters={
                "target_column": target_column,
                "feature_columns": valid_features,
                "test_size": test_size,
                "random_state": random_state,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation="Fitted linear regression using scikit-learn.",
        )
    
class LinearRegressionStatsmodelsStep(PipelineStep):
    name = "linear_regression_statsmodels"
    display_name = "Linear Regression - statsmodels"
    category = "machine_learning"
    description = "Fits a linear regression model using statsmodels OLS."
    output_type = "result"

    parameters = [
        StepParameter(
            name="target_column",
            label="Target column",
            parameter_type="column",
            required=True,
            default=None,
            description="Numeric column to predict.",
        ),
        StepParameter(
            name="feature_columns",
            label="Feature columns",
            parameter_type="columns",
            required=True,
            default=None,
            description="Numeric columns used as predictors.",
        ),
        StepParameter(
            name="test_size",
            label="Test size",
            parameter_type="number",
            required=True,
            default=0.25,
            description="Proportion of data used for testing.",
        ),
        StepParameter(
            name="random_state",
            label="Random state",
            parameter_type="number",
            required=True,
            default=42,
            description="Random seed for train/test split.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        import statsmodels.api as sm

        parameters = parameters or {}

        target_column = parameters.get("target_column")
        feature_columns = parameters.get("feature_columns")
        test_size = float(parameters.get("test_size", 0.25))
        random_state = int(parameters.get("random_state", 42))

        if test_size <= 0 or test_size >= 1:
            raise ValueError("test_size must be between 0 and 1.")

        clean_dataframe, valid_features, target_column, skipped_columns = prepare_regression_data(
            dataframe=dataframe,
            feature_columns=feature_columns,
            target_column=target_column,
        )

        x_train, x_test, y_train, y_test = split_regression_data(
            clean_dataframe=clean_dataframe,
            feature_columns=valid_features,
            target_column=target_column,
            test_size=test_size,
            random_state=random_state,
        )

        x_train_with_const = sm.add_constant(
            x_train,
            has_constant="add",
        )
        x_test_with_const = sm.add_constant(
            x_test,
            has_constant="add",
        )

        model = sm.OLS(y_train, x_train_with_const)
        fitted_model = model.fit()

        y_pred = fitted_model.predict(x_test_with_const)

        params = fitted_model.params

        intercept = float(params[0])

        coefficients = {
            column: round(float(value), 6)
            for column, value in zip(valid_features, params[1:])
        }

        metrics = build_regression_metrics(
            method="linear_regression",
            implementation="statsmodels",
            target_column=target_column,
            feature_columns=valid_features,
            skipped_columns=skipped_columns,
            train_rows=len(x_train),
            test_rows=len(x_test),
            y_test=y_test,
            y_pred=y_pred,
            coefficients=coefficients,
            intercept=intercept,
            extra_metrics={
                "test_size": test_size,
                "random_state": random_state,
                "aic": round(float(fitted_model.aic), 6),
                "bic": round(float(fitted_model.bic), 6),
                "train_r2_score": round(float(fitted_model.rsquared), 6),
                "train_adjusted_r2_score": round(float(fitted_model.rsquared_adj), 6),
            },
        )

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped non-numeric, missing, or target columns: {skipped_columns}."
            )

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters={
                "target_column": target_column,
                "feature_columns": valid_features,
                "test_size": test_size,
                "random_state": random_state,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation="Fitted linear regression using statsmodels OLS.",
        )
    
class LinearRegressionCustomStep(PipelineStep):
    name = "linear_regression_custom"
    display_name = "Linear Regression - Custom"
    category = "machine_learning"
    description = "Fits a linear regression model using a custom normal equation implementation."
    output_type = "result"

    parameters = [
        StepParameter(
            name="target_column",
            label="Target column",
            parameter_type="column",
            required=True,
            default=None,
            description="Numeric column to predict.",
        ),
        StepParameter(
            name="feature_columns",
            label="Feature columns",
            parameter_type="columns",
            required=True,
            default=None,
            description="Numeric columns used as predictors.",
        ),
        StepParameter(
            name="test_size",
            label="Test size",
            parameter_type="number",
            required=True,
            default=0.25,
            description="Proportion of data used for testing.",
        ),
        StepParameter(
            name="random_state",
            label="Random state",
            parameter_type="number",
            required=True,
            default=42,
            description="Random seed for train/test split.",
        ),
    ]

    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        parameters = parameters or {}

        target_column = parameters.get("target_column")
        feature_columns = parameters.get("feature_columns")
        test_size = float(parameters.get("test_size", 0.25))
        random_state = int(parameters.get("random_state", 42))

        if test_size <= 0 or test_size >= 1:
            raise ValueError("test_size must be between 0 and 1.")

        clean_dataframe, valid_features, target_column, skipped_columns = prepare_regression_data(
            dataframe=dataframe,
            feature_columns=feature_columns,
            target_column=target_column,
        )

        x_train, x_test, y_train, y_test = split_regression_data(
            clean_dataframe=clean_dataframe,
            feature_columns=valid_features,
            target_column=target_column,
            test_size=test_size,
            random_state=random_state,
        )

        ones_train = np.ones((x_train.shape[0], 1))
        ones_test = np.ones((x_test.shape[0], 1))

        x_train_with_intercept = np.hstack(
            [ones_train, x_train]
        )
        x_test_with_intercept = np.hstack(
            [ones_test, x_test]
        )

        beta = np.linalg.pinv(
            x_train_with_intercept.T @ x_train_with_intercept
        ) @ x_train_with_intercept.T @ y_train

        y_pred = x_test_with_intercept @ beta

        intercept = float(beta[0])

        coefficients = {
            column: round(float(value), 6)
            for column, value in zip(valid_features, beta[1:])
        }

        condition_number = float(
            np.linalg.cond(x_train_with_intercept)
        )

        metrics = build_regression_metrics(
            method="linear_regression",
            implementation="custom",
            target_column=target_column,
            feature_columns=valid_features,
            skipped_columns=skipped_columns,
            train_rows=len(x_train),
            test_rows=len(x_test),
            y_test=y_test,
            y_pred=y_pred,
            coefficients=coefficients,
            intercept=intercept,
            extra_metrics={
                "test_size": test_size,
                "random_state": random_state,
                "condition_number": round(condition_number, 6),
            },
        )

        warnings = []
        if skipped_columns:
            warnings.append(
                f"Skipped non-numeric, missing, or target columns: {skipped_columns}."
            )

        if condition_number > 1000:
            warnings.append(
                "High condition number detected. The regression may be numerically unstable."
            )

        return StepResult(
            step_name=self.name,
            category=self.category,
            output_type=self.output_type,
            parameters={
                "target_column": target_column,
                "feature_columns": valid_features,
                "test_size": test_size,
                "random_state": random_state,
            },
            metrics=metrics,
            warnings=warnings,
            interpretation="Fitted linear regression using a custom normal equation implementation.",
        )