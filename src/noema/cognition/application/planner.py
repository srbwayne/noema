"""The application boundary that produces one structural plan."""

from noema.cognition.domain.planning import Plan, PlanningRequest
from noema.cognition.ports import PlanningExecutionError, PlanningExecutor


class Planner:
    """Delegate one planning request to its executor and return its plan.

    The planner has exactly one dependency: a ``PlanningExecutor``. It
    does not decompose a goal, materialize context, consume budget, or
    execute a resulting plan itself — that remains ``PlanningExecutor``'s
    exclusive responsibility. This boundary only connects the request to
    the executor: it delegates once and validates that the executor
    honored its own contract before returning its plan unchanged.
    """

    __slots__ = ("_executor",)

    def __init__(
        self,
        *,
        executor: PlanningExecutor,
    ) -> None:
        """Inject the planning executor this component delegates to."""
        self._executor = executor

    async def plan(
        self,
        request: PlanningRequest,
    ) -> Plan:
        """Delegate request to the injected executor and return its plan.

        Calls the injected executor exactly once with the exact
        ``request`` object received. Any error raised while executing
        (including ``PlanningExecutionError``) propagates unchanged. A
        returned value that is not a ``Plan``, or whose ``goal_ref`` does
        not match the request's ``goal_ref``, is also reported as a
        ``PlanningExecutionError`` — the executor broke its own contract.
        A structurally valid, correlated plan is returned as-is,
        regardless of whether it has any steps.
        """
        if not isinstance(request, PlanningRequest):
            raise TypeError("request must be a PlanningRequest")

        plan = await self._executor.execute(request)

        if not isinstance(plan, Plan):
            raise PlanningExecutionError("executor must return a Plan")
        if plan.goal_ref != request.goal_ref:
            raise PlanningExecutionError("executor plan goal_ref must match request goal_ref")

        return plan
