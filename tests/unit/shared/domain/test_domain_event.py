from dataclasses import FrozenInstanceError
from datetime import UTC
from uuid import uuid4

import pytest

from noema.shared.domain import DomainEvent


def test_domain_event_generates_unique_ids() -> None:
    first_event = DomainEvent()
    second_event = DomainEvent()

    assert first_event.event_id
    assert first_event.event_id != second_event.event_id


def test_domain_event_occurs_in_utc() -> None:
    event = DomainEvent()

    assert event.occurred_at.tzinfo is not None
    assert event.occurred_at.tzinfo is UTC
    assert event.occurred_at.utcoffset() == UTC.utcoffset(event.occurred_at)


def test_domain_event_accepts_correlation_and_causation_ids() -> None:
    correlation_id = uuid4()
    causation_id = uuid4()

    event = DomainEvent(correlation_id=correlation_id, causation_id=causation_id)

    assert event.correlation_id == correlation_id
    assert event.causation_id == causation_id


def test_domain_event_is_immutable() -> None:
    event = DomainEvent()

    with pytest.raises(FrozenInstanceError):
        event.event_id = uuid4()
