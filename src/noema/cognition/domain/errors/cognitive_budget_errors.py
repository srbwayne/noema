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


class CognitiveBudgetTimeExceededError(DomainError):
    """Raised when reasoning execution outlives its own ``CognitiveBudget.max_time``.

    Distinct from ``CognitiveBudgetExhaustedError``: that error means known
    demand could not be admitted before reasoning ever began; this error
    means the ``CognitiveBudget`` is valid, admission already passed, and
    reasoning execution actually began, but ``request.budget.max_time``
    elapsed before it completed. This is a cognition budget-policy failure,
    not malformed configuration, not a static admission failure, not a
    provider/technical execution failure (``ReasoningExecutionError``'s
    exclusive category), and not semantic reasoning incompleteness.
    """
