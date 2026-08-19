"""Errors raised by prediction/counterfactual request invariants."""

from noema.shared.domain import DomainError


class InvalidPredictionRequestError(DomainError):
    """Raised when a prediction request violates its representation."""


class InvalidCounterfactualRequestError(DomainError):
    """Raised when a counterfactual request violates its representation."""


class InvalidPredictionCounterfactualResultError(DomainError):
    """Raised when a prediction/counterfactual result violates its representation."""
