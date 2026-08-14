"""Errors raised by cognition domain rules."""

from noema.cognition.domain.errors.attention_errors import (
    InvalidAttentionFactorError,
    InvalidAttentionPolicyError,
    InvalidAttentionWeightsError,
)
from noema.cognition.domain.errors.context_errors import InvalidContextVersionError
from noema.cognition.domain.errors.situation_errors import (
    DuplicateSituationEntryError,
    InvalidSituationDeltaError,
    InvalidSituationEntryError,
    InvalidSituationStateError,
    SituationEntryKindMismatchError,
    SituationEntryNotFoundError,
    StaleSituationDeltaError,
)
from noema.cognition.domain.errors.workspace_errors import (
    CognitiveItemNotFoundError,
    DuplicateCognitiveItemError,
    InvalidCognitiveItemError,
    InvalidWorkspaceBudgetError,
    InvalidWorkspaceFocusError,
    InvalidWorkspaceStateError,
    WorkspaceCapacityExceededError,
)

__all__ = [
    "CognitiveItemNotFoundError",
    "DuplicateCognitiveItemError",
    "DuplicateSituationEntryError",
    "InvalidAttentionFactorError",
    "InvalidAttentionPolicyError",
    "InvalidAttentionWeightsError",
    "InvalidCognitiveItemError",
    "InvalidContextVersionError",
    "InvalidSituationDeltaError",
    "InvalidSituationEntryError",
    "InvalidSituationStateError",
    "InvalidWorkspaceBudgetError",
    "InvalidWorkspaceFocusError",
    "InvalidWorkspaceStateError",
    "SituationEntryKindMismatchError",
    "SituationEntryNotFoundError",
    "StaleSituationDeltaError",
    "WorkspaceCapacityExceededError",
]
