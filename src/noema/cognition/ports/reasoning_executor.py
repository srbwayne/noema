"""The port contract for executing a single-strategy reasoning request."""

from typing import Protocol

from noema.cognition.domain.reasoning import ReasoningOutcome, ReasoningRequest


class ReasoningExecutor(Protocol):
    """Execute one explicit-strategy reasoning request.

    ``request.strategy`` already carries the single strategy to execute, so
    this port represents executing one ``ReasoningRequest`` with one
    explicit strategy; it does not accept a multi-strategy coordination
    plan or a strategy demand.

    A successful execution returns a ``ReasoningOutcome``. A concrete
    implementation must translate technical failures of the underlying
    execution technology into ``ReasoningExecutionError`` — provider- or
    technology-specific exceptions must not cross this port.
    """

    async def execute(
        self,
        request: ReasoningRequest,
    ) -> ReasoningOutcome:
        """Execute the request and return its structured outcome."""
        ...
