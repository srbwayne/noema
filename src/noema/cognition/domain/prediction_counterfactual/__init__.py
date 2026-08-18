"""Contracts for scenario-specific prediction and counterfactual derivation."""

from .counterfactual_request import CounterfactualRequest
from .prediction_request import PredictionRequest

__all__ = [
    "CounterfactualRequest",
    "PredictionRequest",
]
