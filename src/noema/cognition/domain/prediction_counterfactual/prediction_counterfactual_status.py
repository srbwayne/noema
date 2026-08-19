"""Semantic status of a Prediction / Counterfactual result."""

from enum import Enum


class PredictionCounterfactualStatus(Enum):
    """Classify the semantic outcome of a derivation."""

    DERIVED = "derived"
    INSUFFICIENT_KNOWLEDGE = "insufficient_knowledge"
