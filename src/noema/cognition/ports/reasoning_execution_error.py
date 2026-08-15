"""Technical failure raised while executing a reasoning request."""


class ReasoningExecutionError(Exception):
    """Signal a technical execution failure, not a domain invariant violation.

    Raised by a concrete ``ReasoningExecutor`` implementation when the
    underlying execution technology fails before a valid
    ``ReasoningOutcome`` can be produced (for example: an unavailable
    resource, a communication failure, or a response that could not be
    translated into the outcome contract). It intentionally inherits
    directly from ``Exception`` rather than ``DomainError``, because a
    technical execution failure is not a violation of a domain invariant.
    """
