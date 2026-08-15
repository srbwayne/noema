"""Errors raised by cognition domain rules."""

from noema.cognition.domain.errors.attention_errors import (
    InvalidAttentionFactorError,
    InvalidAttentionPolicyError,
    InvalidAttentionWeightsError,
)
from noema.cognition.domain.errors.cognitive_budget_errors import (
    InvalidCognitiveBudgetError,
)
from noema.cognition.domain.errors.cognitive_mode_errors import (
    InvalidCognitiveDemandError,
    InvalidCognitiveDemandWeightsError,
    InvalidCognitiveModeDecisionError,
    InvalidCognitiveModePolicyError,
)
from noema.cognition.domain.errors.context_composition_errors import (
    ContextCompositionUnsatisfiedError,
    InvalidContextCandidateError,
    InvalidContextComposerError,
    InvalidContextCompositionPolicyError,
    InvalidContextPackageError,
    InvalidContextRequestError,
    InvalidContextSliceError,
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
from noema.cognition.domain.errors.reasoning_errors import (
    AmbiguousReasoningStrategyError,
    InvalidInformationNeedError,
    InvalidReasoningOutcomeError,
    InvalidReasoningRequestError,
    InvalidReasoningStrategyDecisionError,
    InvalidReasoningStrategyDemandError,
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
    "AmbiguousReasoningStrategyError",
    "ContextCompositionUnsatisfiedError",
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
    "InvalidCognitiveDemandError",
    "InvalidCognitiveDemandWeightsError",
    "InvalidCognitiveModeDecisionError",
    "InvalidCognitiveModePolicyError",
    "InvalidCognitiveItemError",
    "InvalidContextCandidateError",
    "InvalidContextComposerError",
    "InvalidContextCompositionPolicyError",
    "InvalidContextPackageError",
    "InvalidContextRequestError",
    "InvalidContextSliceError",
    "InvalidContextVersionError",
    "InvalidEpistemicClaimError",
    "InvalidEpistemicConflictError",
    "InvalidEpistemicDeltaError",
    "InvalidEpistemicSourceError",
    "InvalidEpistemicStateError",
    "InvalidInformationNeedError",
    "InvalidReasoningOutcomeError",
    "InvalidReasoningRequestError",
    "InvalidReasoningStrategyDecisionError",
    "InvalidReasoningStrategyDemandError",
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
