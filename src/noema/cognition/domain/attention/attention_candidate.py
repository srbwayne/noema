"""A stimulus prepared for pure attention evaluation."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from noema.cognition.domain.attention.attention_factors import AttentionFactors
from noema.cognition.domain.attention.attention_priority import AttentionPriority


@dataclass(frozen=True, slots=True, kw_only=True)
class AttentionCandidate:
    """Event metadata and signals required by the attention engine."""

    event_id: UUID
    priority: AttentionPriority
    factors: AttentionFactors
    candidate_id: UUID = field(default_factory=uuid4)
