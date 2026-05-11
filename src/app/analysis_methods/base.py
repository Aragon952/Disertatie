from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd


StepCategory = Literal[
    "preprocessing",
    "statistics",
    "machine_learning",
    "custom",
]


StepOutputType = Literal[
    "dataframe",
    "result",
]


@dataclass
class StepParameter:
    """
    Describes one configurable parameter for a pipeline step.
    """
    name: str
    label: str
    parameter_type: str
    required: bool = True
    default: Any | None = None
    options: list[Any] | None = None
    description: str = ""


@dataclass
class StepResult:
    """
    Standard output returned by every pipeline step.
    """
    step_name: str
    category: StepCategory
    output_type: StepOutputType
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    interpretation: str = ""
    output_data: pd.DataFrame | None = None


class PipelineStep(ABC):
    """
    Base class for every step in the application.

    A step can be:
    - preprocessing
    - statistics
    - machine learning
    - custom
    """

    name: str
    display_name: str
    category: StepCategory
    description: str
    output_type: StepOutputType
    parameters: list[StepParameter] = []

    @abstractmethod
    def run(
        self,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any] | None = None,
    ) -> StepResult:
        """
        Runs the step on a DataFrame.
        """
        raise NotImplementedError