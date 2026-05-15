from app.analysis_methods.base import PipelineStep
from app.analysis_methods.methods import (
    OutlierDetectionIQRStep,
    OutlierDetectionZScoreStep,
)
from app.analysis_methods.preprocessing import (
    DropMissingRowsStep,
    FillMissingValuesStep,
    SelectColumnsStep,
)
from app.analysis_methods.stats import (
    CorrelationMatrixStep,
    DescribeDatasetStep,
)


def get_available_steps() -> dict[str, PipelineStep]:
    """
    Returns all available pipeline steps indexed by their internal name.
    """
    steps: list[PipelineStep] = [
        DropMissingRowsStep(),
        FillMissingValuesStep(),
        SelectColumnsStep(),
        DescribeDatasetStep(),
        CorrelationMatrixStep(),
        OutlierDetectionIQRStep(),
        OutlierDetectionZScoreStep(),
    ]

    return {
        step.name: step
        for step in steps
    }


def get_step_by_name(step_name: str) -> PipelineStep:
    """
    Returns one pipeline step by name.
    """
    steps = get_available_steps()

    if step_name not in steps:
        raise ValueError(f"Unknown pipeline step: {step_name}")

    return steps[step_name]


def list_steps_metadata() -> list[dict]:
    """
    Returns metadata useful for UI display.
    """
    steps = get_available_steps()

    return [
        {
            "name": step.name,
            "display_name": step.display_name,
            "category": step.category,
            "description": step.description,
            "output_type": step.output_type,
            "parameters": [
                {
                    "name": parameter.name,
                    "label": parameter.label,
                    "parameter_type": parameter.parameter_type,
                    "required": parameter.required,
                    "default": parameter.default,
                    "options": parameter.options,
                    "description": parameter.description,
                }
                for parameter in step.parameters
            ],
        }
        for step in steps.values()
    ]