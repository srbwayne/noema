"""The application boundary that orchestrates selection and execution."""

from noema.model_router.application.model_router import ModelRouter
from noema.model_router.domain import ModelSelectionRequest
from noema.model_router.ports import (
    ModelExecutionError,
    ModelExecutionRequest,
    ModelExecutionResult,
    ModelExecutor,
)


class ModelExecutionEngine:
    """Route a selection request, then execute the resource it selects.

    The engine has exactly two dependencies: a ``ModelRouter`` and a
    ``ModelExecutor``. It does not select, route, or rank resources itself
    — that remains ``ModelRouter``'s (and, beneath it, ``ModelSelector``'s)
    exclusive responsibility — and it does not execute a resource directly
    — that remains ``ModelExecutor``'s exclusive responsibility. This
    boundary only connects the two: it routes once, builds the execution
    request from the selected resource, executes once, and validates that
    the executor honored its own contract before returning its result
    unchanged.
    """

    __slots__ = ("_router", "_executor")

    def __init__(
        self,
        *,
        router: ModelRouter,
        executor: ModelExecutor,
    ) -> None:
        """Inject the router and executor this engine orchestrates."""
        self._router = router
        self._executor = executor

    async def execute(
        self,
        selection_request: ModelSelectionRequest,
        input_text: str,
    ) -> ModelExecutionResult:
        """Route selection_request, execute its selected resource, and return the result.

        Calls the injected router exactly once with the exact
        ``selection_request`` object received, then calls the injected
        executor exactly once with an ``ModelExecutionRequest`` built from
        the selected resource and ``input_text`` unchanged. Any error
        raised while routing, while constructing the execution request, or
        by the executor itself (including ``ModelExecutionError``)
        propagates unchanged. A returned value that is not a
        ``ModelExecutionResult``, or whose ``resource`` does not equal the
        selected resource, is also reported as a ``ModelExecutionError`` —
        the executor broke its own contract. A structurally valid,
        correlated result is returned as-is.
        """
        decision = self._router.route(selection_request)

        execution_request = ModelExecutionRequest(
            resource=decision.selected_resource,
            input_text=input_text,
        )

        result = await self._executor.execute(execution_request)

        if not isinstance(result, ModelExecutionResult):
            raise ModelExecutionError("executor must return a ModelExecutionResult")
        if result.resource != decision.selected_resource:
            raise ModelExecutionError("executor result resource must match selected resource")

        return result
