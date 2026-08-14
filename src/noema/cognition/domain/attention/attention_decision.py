"""Immutable result of attention evaluation."""

from dataclasses import dataclass
from uuid import UUID

from noema.cognition.domain.attention.attention_disposition import AttentionDisposition
from noema.cognition.domain.attention.attention_priority import AttentionPriority


@dataclass(frozen=True, slots=True, kw_only=True)
class AttentionDecision:
    """Traceable priority, score, and disposition for a candidate."""

    candidate_id: UUID
    event_id: UUID
    priority: AttentionPriority
    score: float
    disposition: AttentionDisposition
