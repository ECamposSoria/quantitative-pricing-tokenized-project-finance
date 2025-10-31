"""
Helper utilities to load canonical project datasets into validated models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from .params import ProjectParameters


def load_project_parameters(base_path: Union[str, Path]) -> ProjectParameters:
    """
    Load the default LEO IoT dataset and return a validated parameter bundle.

    Parameters
    ----------
    base_path:
        Directory containing `project_params.csv`, `tranches.csv`,
        `rcapex_schedule.csv`, and `debt_schedule.csv`.
    """
    return ProjectParameters.from_directory(base_path)


# Backwards compatibility with previous placeholder signature.
def load_project_data(base_path: Union[str, Path]) -> ProjectParameters:
    return load_project_parameters(base_path)
