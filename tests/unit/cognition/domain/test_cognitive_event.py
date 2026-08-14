from dataclasses import dataclass

from noema.cognition.domain.events import CognitiveEvent
from noema.shared.domain import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class SampleCognitiveEvent(CognitiveEvent):
    description: str


def test_cognitive_event_inherits_domain_event_metadata() -> None:
    event = SampleCognitiveEvent(description="test event")

    assert isinstance(event, DomainEvent)
    assert event.event_id
    assert event.occurred_at.tzinfo is not None
    assert event.description == "test event"
