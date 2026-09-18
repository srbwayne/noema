"""Errors raised by cognitive processing budget invariants and admission."""

from noema.shared.domain import DomainError


class InvalidCognitiveBudgetError(DomainError):
    """Raised when a cognitive resource limit is invalid."""


class CognitiveBudgetExhaustedError(DomainError):
    """Raised when a valid CognitiveBudget cannot admit an operation's known demand.

    Distinct from ``InvalidCognitiveBudgetError``: the ``CognitiveBudget``
    itself is perfectly well-formed (every field individually valid); this
    error instead means the current operation's statically known resource
    demand exceeds what that otherwise-valid budget makes available (for
    example, a canonical DIRECT operation, which always requires exactly one
    model-execution attempt, paired with ``max_llm_calls=0``). This is a
    domain-policy admission failure, not a technical execution failure
    (``ReasoningExecutionError``'s exclusive category) and not semantic
    reasoning incompleteness (``ReasoningStatus.UNRESOLVED``'s exclusive
    category) -- no reasoning was ever attempted.
    """
