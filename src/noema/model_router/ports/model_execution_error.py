"""Technical failure raised while executing a model resource."""


class ModelExecutionError(Exception):
    """Raised when model execution fails before a valid result is produced.

    Raised by a concrete ``ModelExecutor`` implementation when the
    underlying execution technology fails before a valid
    ``ModelExecutionResult`` can be produced (for example: an unavailable
    provider, a communication failure, a timeout, or a response that could
    not be translated into the result contract). It intentionally
    inherits directly from ``Exception`` rather than ``DomainError``,
    because a technical execution failure is not a violation of a domain
    invariant.
    """
