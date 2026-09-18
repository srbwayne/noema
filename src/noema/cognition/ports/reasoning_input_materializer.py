"""The port contract for materializing a ReasoningRequest into model input text."""

from typing import Protocol

from noema.cognition.domain.reasoning import ReasoningRequest


class ReasoningInputMaterializer(Protocol):
    """Render one ``ReasoningRequest`` into flat, provider-neutral input text.

    This is the seam through which ``ModelReasoningExecutor`` obtains model
    input without depending on ``cognition.application`` or
    ``cognition.domain.context_composition`` -- its only Noema domain
    dependency is ``noema.cognition.domain.reasoning``. A concrete
    implementation renders ``request.problem_statement`` and
    ``request.context`` into one string; it is never expected to call a
    model or provider, or to depend on any specific provider's prompt
    syntax.
    """

    def materialize(
        self,
        request: ReasoningRequest,
    ) -> str:
        """Render the request's problem and context into one input string."""
        ...
