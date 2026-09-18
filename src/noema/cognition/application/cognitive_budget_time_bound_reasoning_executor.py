"""Enforce a reasoning request's own CognitiveBudget.max_time deadline."""

import asyncio

from noema.cognition.domain.budget import CognitiveBudgetTimeExceededError
from noema.cognition.domain.reasoning import ReasoningOutcome, ReasoningRequest
from noema.cognition.ports import ReasoningExecutor


class CognitiveBudgetTimeBoundReasoningExecutor:
    """Decorate a ``ReasoningExecutor`` with a per-request cognitive deadline.

    ADR-0033's bounded enforcement slice: this is the only production
    component that reads ``ReasoningRequest.budget.max_time``. It
    structurally implements the ``ReasoningExecutor`` port (a ``Protocol``,
    so this class deliberately does not inherit from it or validate its
    injected inner executor with ``isinstance`` -- the same structural
    pattern already used by ``CognitiveBudgetAdmittingReasoningExecutor``
    and ``ReasoningEngine``) and wraps exactly one inner
    ``ReasoningExecutor``.

    Each ``execute`` call opens its own local ``asyncio.timeout`` scope of
    ``request.budget.max_time.total_seconds()`` seconds around exactly the
    inner ``execute`` call. It holds no mutable timer state and accumulates
    nothing across calls, so two independent calls -- sequential or
    concurrent -- sharing the same immutable budget object each receive a
    fresh, fully independent deadline.

    ``max_steps``, ``max_llm_calls``, ``max_tool_calls``, ``max_cost``,
    ``max_tokens``, and ``max_search_depth`` are NOT enforced by this
    component.
    """

    __slots__ = ("_inner_executor",)

    def __init__(
        self,
        *,
        inner_executor: ReasoningExecutor,
    ) -> None:
        """Bind the exact inner executor this decorator delegates timed execution to."""
        self._inner_executor = inner_executor

    async def execute(
        self,
        request: ReasoningRequest,
    ) -> ReasoningOutcome:
        """Execute ``request`` through the inner executor within its own deadline.

        Rejects a non-``ReasoningRequest`` with ``TypeError`` before any
        timeout scope is opened. Otherwise opens an ``asyncio.timeout`` scope
        of ``request.budget.max_time.total_seconds()`` seconds around exactly
        the inner ``execute`` call.

        When the inner executor completes before the deadline, returns its
        exact ``ReasoningOutcome`` by identity, unwrapped. When the deadline
        expires, the inner execution is cancelled and, only once this
        decorator's own timeout scope confirms it actually expired, raises
        ``CognitiveBudgetTimeExceededError`` with the original
        ``TimeoutError`` preserved as ``__cause__``. A raw ``TimeoutError``
        the inner executor raises independently of this deadline propagates
        unchanged, since the timeout scope it did not expire proves this
        decorator's own deadline is not responsible. External cancellation
        (``asyncio.CancelledError`` delivered by a caller, not by this
        decorator's own timeout scope) always propagates unchanged. Any
        other exception the inner executor raises propagates unchanged.
        """
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        timeout_context = asyncio.timeout(request.budget.max_time.total_seconds())

        try:
            async with timeout_context:
                return await self._inner_executor.execute(request)
        except TimeoutError as exc:
            if not timeout_context.expired():
                raise
            raise CognitiveBudgetTimeExceededError(
                f"{request.strategy} exceeded max_time={request.budget.max_time}"
            ) from exc
