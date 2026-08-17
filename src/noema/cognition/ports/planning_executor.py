"""The port contract for producing a structural plan from a planning request."""

from typing import Protocol

from noema.cognition.domain.planning import Plan, PlanningRequest


class PlanningExecutor(Protocol):
    """Produce one structural ``Plan`` from one ``PlanningRequest``.

    ``PlanningExecutor`` is not the Planner: it represents only the
    concrete technology or strategy capable of turning a valid
    ``PlanningRequest`` into a valid ``Plan``. A future application
    boundary decides how and when this port is used.

    A successful execution returns a ``Plan``. A concrete implementation
    must translate technical failures of the underlying execution
    technology into ``PlanningExecutionError`` — provider- or
    technology-specific exceptions must not cross this port.
    """

    async def execute(
        self,
        request: PlanningRequest,
    ) -> Plan:
        """Execute the request and return its structural plan."""
        ...
