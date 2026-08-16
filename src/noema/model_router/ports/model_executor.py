"""The port contract for executing an already-selected model resource."""

from typing import Protocol

from noema.model_router.ports.model_execution_request import ModelExecutionRequest
from noema.model_router.ports.model_execution_result import ModelExecutionResult


class ModelExecutor(Protocol):
    """Execute one provider-neutral request against an already-selected resource.

    The resource has already been chosen; this port does not select,
    route, rank, or validate the resource's declared capabilities — it
    only executes it.

    A successful execution returns a ``ModelExecutionResult``. A concrete
    implementation must translate technical failures of the underlying
    provider or execution technology into ``ModelExecutionError`` —
    provider- or technology-specific exceptions must not cross this port.
    """

    async def execute(
        self,
        request: ModelExecutionRequest,
    ) -> ModelExecutionResult:
        """Execute the request and return its result."""
        ...
