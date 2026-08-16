"""The first ReasoningExecutor implementation, backed by model execution."""

from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.ports import ReasoningExecutionError
from noema.model_router.application import ModelExecutionEngine
from noema.model_router.domain import (
    AmbiguousModelSelectionError,
    ModelSelectionRequest,
    NoEligibleModelResourceError,
)
from noema.model_router.ports import ModelExecutionError


class ModelReasoningExecutor:
    """Execute a DIRECT-strategy reasoning request through model execution.

    This is the first concrete ``ReasoningExecutor`` implementation. It
    bridges cognition to the ``model_router`` bounded context exclusively
    through ``ModelExecutionEngine`` — the frozen application boundary
    that already orchestrates selection and execution. This adapter does
    not select, route, or execute a model resource itself, does not
    inspect or construct model capabilities, and does not know that any
    particular provider (e.g. Ollama) exists.

    Only ``ReasoningStrategy.DIRECT`` is supported in this first
    integration, and only with an empty context package — every other
    strategy and every non-empty context package is rejected before any
    model execution is attempted.
    """

    __slots__ = ("_execution_engine", "_selection_request")

    def __init__(
        self,
        *,
        execution_engine: ModelExecutionEngine,
        selection_request: ModelSelectionRequest,
    ) -> None:
        """Bind this executor to the engine it delegates to and its fixed selection."""
        if not isinstance(selection_request, ModelSelectionRequest):
            raise TypeError("selection_request must be a ModelSelectionRequest")
        self._execution_engine = execution_engine
        self._selection_request = selection_request

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        """Execute request via model execution and return its ReasoningOutcome.

        Rejects any strategy other than ``DIRECT`` and any request whose
        context package carries context slices, both before any model
        execution is attempted. Translates ``ModelExecutionError``,
        ``NoEligibleModelResourceError``, and ``AmbiguousModelSelectionError``
        raised by the execution engine into ``ReasoningExecutionError``,
        preserving the original error as the cause. Any other exception
        propagates unchanged.
        """
        if request.strategy is not ReasoningStrategy.DIRECT:
            raise ReasoningExecutionError("model reasoning executor supports only DIRECT strategy")
        if request.context.slices:
            raise ReasoningExecutionError(
                "model reasoning executor does not support context slices"
            )

        try:
            result = await self._execution_engine.execute(
                selection_request=self._selection_request,
                input_text=request.problem_statement,
            )
        except (
            AmbiguousModelSelectionError,
            NoEligibleModelResourceError,
            ModelExecutionError,
        ) as exc:
            raise ReasoningExecutionError("model reasoning execution failed") from exc

        return ReasoningOutcome(
            problem_ref=request.problem_ref,
            strategy=request.strategy,
            status=ReasoningStatus.COMPLETED,
            conclusion=result.output_text,
            reason_summary="direct reasoning",
            information_needs=(),
        )
