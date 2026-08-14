"""Errors raised by cognition domain rules."""

from noema.cognition.domain.errors.attention_errors import (
    InvalidAttentionFactorError,
    InvalidAttentionPolicyError,
    InvalidAttentionWeightsError,
)
from noema.cognition.domain.errors.cognitive_budget_errors import (
    InvalidCognitiveBudgetError,
)
from noema.cognition.domain.errors.context_errors import InvalidContextVersionError
from noema.cognition.domain.errors.epistemic_errors import (
    DuplicateEpistemicClaimError,
    EpistemicClaimImmutableFieldError,
    EpistemicClaimNotFoundError,
    InvalidEpistemicClaimError,
    InvalidEpistemicConflictError,
    InvalidEpistemicDeltaError,
    InvalidEpistemicSourceError,
    InvalidEpistemicStateError,
    StaleEpistemicDeltaError,
)
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
    "DuplicateEpistemicClaimError",
    "DuplicateSituationEntryError",
    "EpistemicClaimImmutableFieldError",
    "EpistemicClaimNotFoundError",
    "InvalidAttentionFactorError",
    "InvalidAttentionPolicyError",
    "InvalidAttentionWeightsError",
    "InvalidCognitiveBudgetError",
    "InvalidCognitiveItemError",
    "InvalidContextVersionError",
    "InvalidEpistemicClaimError",
    "InvalidEpistemicConflictError",
    "InvalidEpistemicDeltaError",
    "InvalidEpistemicSourceError",
    "InvalidEpistemicStateError",
    "InvalidSituationDeltaError",
    "InvalidSituationEntryError",
    "InvalidSituationStateError",
    "InvalidWorkspaceBudgetError",
    "InvalidWorkspaceFocusError",
    "InvalidWorkspaceStateError",
    "SituationEntryKindMismatchError",
    "SituationEntryNotFoundError",
    "StaleEpistemicDeltaError",
    "StaleSituationDeltaError",
    "WorkspaceCapacityExceededError",
]
