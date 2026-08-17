"""Technical failure raised while executing a planning request."""


class PlanningExecutionError(Exception):
    """Signal a technical execution failure, not a domain invariant violation.

    Raised by a concrete ``PlanningExecutor`` implementation when the
    underlying execution technology fails before a valid ``Plan`` can be
    produced (for example: an unavailable planning resource, a
    communication failure, or a response that could not be translated
    into the ``Plan`` contract). It intentionally inherits directly from
    ``Exception`` rather than ``DomainError``, because a technical
    execution failure is not a violation of a domain invariant.
    """
