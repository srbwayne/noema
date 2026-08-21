"""Semantic status of an Evaluation result."""

from enum import Enum


class EvaluationStatus(Enum):
    """Classify whether a utility judgment was reached."""

    JUDGED = "judged"
    NO_JUDGMENT = "no_judgment"
