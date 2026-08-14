"""Base event type for the cognitive system."""

from dataclasses import dataclass

from noema.shared.domain import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveEvent(DomainEvent):
    """Marker for events entering or circulating through cognition."""
