"""Shared domain primitives with demonstrated cross-context use."""

from noema.shared.domain.domain_error import DomainError
from noema.shared.domain.domain_event import DomainEvent

__all__ = ["DomainError", "DomainEvent"]
