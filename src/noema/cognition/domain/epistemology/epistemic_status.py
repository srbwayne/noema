"""Epistemic classifications assigned explicitly to claims."""

from enum import Enum


class EpistemicStatus(Enum):
    """Current epistemic status of a claim."""

    OBSERVATION = "observation"
    FACT = "fact"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    ASSUMPTION = "assumption"
    PREDICTION = "prediction"
    OPINION = "opinion"
    UNKNOWN = "unknown"
    CONFLICTED = "conflicted"
