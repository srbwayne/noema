"""Concrete application-layer realization of the ReasoningInputMaterializer port."""

from noema.cognition.application.prior_task_context_materializer import (
    PriorTaskContextMaterializer,
)
from noema.cognition.domain.reasoning import ReasoningRequest


class PriorTaskReasoningInputMaterializer:
    """Adapt ``PriorTaskContextMaterializer`` to the ``ReasoningInputMaterializer`` port.

    This is the concrete realization of AF's seam D2: it lets
    ``ModelReasoningExecutor`` obtain materialized model input through a
    structural port contract, typed only against ``ReasoningRequest``,
    without ever importing ``PriorTaskContextMaterializer`` or
    ``cognition.application`` itself.

    It performs no logic beyond the exact delegation below: no policy, no
    selection, no mutation, and no provider or model knowledge.
    """

    __slots__ = ("_context_materializer",)

    def __init__(
        self,
        *,
        context_materializer: PriorTaskContextMaterializer,
    ) -> None:
        """Bind the concrete ``PriorTaskContextMaterializer`` this adapter delegates to."""
        if not isinstance(context_materializer, PriorTaskContextMaterializer):
            raise TypeError("context_materializer must be a PriorTaskContextMaterializer")
        self._context_materializer = context_materializer

    def materialize(
        self,
        request: ReasoningRequest,
    ) -> str:
        """Delegate exactly to the bound ``PriorTaskContextMaterializer``.

        Rejects a non-``ReasoningRequest`` ``request`` with ``TypeError``.
        Forwards ``request.problem_statement`` and ``request.context``
        unchanged; any error raised by the bound materializer propagates
        unchanged.
        """
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")
        return self._context_materializer.materialize(
            problem_statement=request.problem_statement,
            context=request.context,
        )
