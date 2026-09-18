"""The first ReasoningExecutor implementation, backed by model execution."""

from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.ports import ReasoningExecutionError, ReasoningInputMaterializer
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

    Only ``ReasoningStrategy.DIRECT`` is supported in this integration.
    Model input is obtained by delegating the exact ``ReasoningRequest`` to
    the bound ``ReasoningInputMaterializer`` port (ADR-0031 seam D2) —
    this adapter never inspects ``request.context`` itself, never imports
    ``PriorTaskContextMaterializer`` or any ``cognition.application``
    module, and has no knowledge of how (or whether) prior-TASK context is
    rendered.
    """

    __slots__ = ("_execution_engine", "_selection_request", "_input_materializer")

    def __init__(
        self,
        *,
        execution_engine: ModelExecutionEngine,
        selection_request: ModelSelectionRequest,
        input_materializer: ReasoningInputMaterializer,
    ) -> None:
        """Bind this executor to the engine, selection, and materializer it delegates to."""
        if not isinstance(selection_request, ModelSelectionRequest):
            raise TypeError("selection_request must be a ModelSelectionRequest")
        self._execution_engine = execution_engine
        self._selection_request = selection_request
        self._input_materializer = input_materializer

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        """Execute request via model execution and return its ReasoningOutcome.

        Rejects any strategy other than ``DIRECT`` before any materialization
        or model execution is attempted. Obtains model input by calling the
        bound ``ReasoningInputMaterializer`` exactly once with the exact
        ``request``; any error it raises (for example
        ``RuntimeContentReferenceNotFoundError``,
        ``UnsupportedPriorTaskContextSliceError``, or
        ``PriorTaskContextMaterializationCoherenceError``) propagates
        unchanged — it is never translated to ``ReasoningExecutionError``,
        since it is not a provider/model execution failure, and no model
        execution is attempted when it occurs. Translates
        ``ModelExecutionError``, ``NoEligibleModelResourceError``, and
        ``AmbiguousModelSelectionError`` raised by the execution engine into
        ``ReasoningExecutionError``, preserving the original error as the
        cause. Any other exception propagates unchanged.
        """
        if request.strategy is not ReasoningStrategy.DIRECT:
            raise ReasoningExecutionError("model reasoning executor supports only DIRECT strategy")

        input_text = self._input_materializer.materialize(request)

        try:
            result = await self._execution_engine.execute(
                selection_request=self._selection_request,
                input_text=input_text,
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
