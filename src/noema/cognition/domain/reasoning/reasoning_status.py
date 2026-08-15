"""Semantic statuses of structured reasoning outcomes."""

from enum import Enum


class ReasoningStatus(Enum):
    """Describe the semantic completeness of a reasoning outcome."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    NEEDS_INFORMATION = "needs_information"
    UNRESOLVED = "unresolved"
