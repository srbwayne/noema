"""The application boundary that executes one single-strategy reasoning request."""

from noema.cognition.domain.reasoning import ReasoningOutcome, ReasoningRequest
from noema.cognition.ports import ReasoningExecutionError, ReasoningExecutor


class ReasoningEngine:
    """Execute a single-strategy reasoning request through its executor.

    The engine has exactly one dependency: a ``ReasoningExecutor``. It does
    not select a strategy, coordinate multiple strategies, or consume the
    request's budget; ``request.strategy`` already carries the single
    strategy to execute, and this step defines single-strategy execution
    only.
    """

    __slots__ = ("_executor",)

    def __init__(
        self,
        *,
        executor: ReasoningExecutor,
    ) -> None:
        """Inject the reasoning executor this engine delegates to."""
        self._executor = executor

    async def reason(
        self,
        request: ReasoningRequest,
    ) -> ReasoningOutcome:
        """Execute request once and return its correlated outcome.

        Calls the injected executor exactly once with the exact request
        object received. Any ``ReasoningExecutionError`` raised by the
        executor propagates unchanged. A returned value that is not a
        ``ReasoningOutcome``, or whose ``problem_ref``/``strategy`` does
        not correlate with the request, is also reported as a
        ``ReasoningExecutionError`` — the executor broke its own contract.
        A structurally valid, correlated outcome is returned as-is,
        regardless of its semantic ``ReasoningStatus`` (including
        UNRESOLVED, which is a valid outcome, not a technical failure).
        """
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        outcome = await self._executor.execute(request)

        if not isinstance(outcome, ReasoningOutcome):
            raise ReasoningExecutionError("executor must return a ReasoningOutcome")
        if outcome.problem_ref != request.problem_ref:
            raise ReasoningExecutionError(
                "executor outcome problem_ref must match request problem_ref"
            )
        if outcome.strategy is not request.strategy:
            raise ReasoningExecutionError("executor outcome strategy must match request strategy")

        return outcome
