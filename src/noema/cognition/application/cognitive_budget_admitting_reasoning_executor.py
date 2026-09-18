"""Admit or deny a reasoning request against its own declared CognitiveBudget."""

from noema.cognition.domain.budget import CognitiveBudgetExhaustedError
from noema.cognition.domain.reasoning import ReasoningOutcome, ReasoningRequest, ReasoningStrategy
from noema.cognition.ports import ReasoningExecutor

_DIRECT_REQUIRED_LLM_CALLS = 1


class CognitiveBudgetAdmittingReasoningExecutor:
    """Decorate a ``ReasoningExecutor`` with pre-execution budget admission.

    ADR-0032's first bounded enforcement slice: this is the only production
    component that reads ``ReasoningRequest.budget``. It structurally
    implements the ``ReasoningExecutor`` port (a ``Protocol``, so this class
    deliberately does not inherit from it or validate its injected inner
    executor with ``isinstance`` -- the same structural pattern
    ``ReasoningEngine`` already uses for its own injected executor) and wraps
    exactly one inner ``ReasoningExecutor``.

    For ``ReasoningStrategy.DIRECT`` -- the only strategy whose static
    resource demand is known today, always exactly one model-execution
    attempt -- it admits the request only when
    ``request.budget.max_llm_calls >= 1``; otherwise it raises
    ``CognitiveBudgetExhaustedError`` before calling the inner executor,
    which means before any input materialization, model routing, or provider
    execution occurs. For every other strategy it invents no demand and
    performs no admission check at all, delegating the exact request
    unchanged -- this component never pretends to enforce a budget dimension
    or strategy whose resource demand is not yet defined.

    It holds no mutable usage counter and accumulates nothing across calls:
    each ``execute`` call evaluates only the exact ``CognitiveBudget`` carried
    by that exact ``ReasoningRequest``, so two independent calls sharing the
    same immutable budget object are each admitted independently.

    ``max_time``, ``max_steps``, ``max_tool_calls``, ``max_cost``,
    ``max_tokens``, and ``max_search_depth`` are NOT enforced by this
    component.
    """

    __slots__ = ("_inner_executor",)

    def __init__(
        self,
        *,
        inner_executor: ReasoningExecutor,
    ) -> None:
        """Bind the exact inner executor this decorator delegates admitted requests to."""
        self._inner_executor = inner_executor

    async def execute(
        self,
        request: ReasoningRequest,
    ) -> ReasoningOutcome:
        """Admit ``request`` against its own budget, then delegate or deny.

        Rejects a non-``ReasoningRequest`` with ``TypeError``. For
        ``ReasoningStrategy.DIRECT`` with ``request.budget.max_llm_calls < 1``,
        raises ``CognitiveBudgetExhaustedError`` without calling the inner
        executor at all. Otherwise -- DIRECT with sufficient budget, or any
        non-DIRECT strategy -- calls the inner executor exactly once with the
        exact ``request`` object and returns its exact ``ReasoningOutcome``
        unchanged; any exception it raises propagates unwrapped.
        """
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        if (
            request.strategy is ReasoningStrategy.DIRECT
            and request.budget.max_llm_calls < _DIRECT_REQUIRED_LLM_CALLS
        ):
            raise CognitiveBudgetExhaustedError(
                "ReasoningStrategy.DIRECT requires max_llm_calls >= "
                f"{_DIRECT_REQUIRED_LLM_CALLS}, but the configured budget "
                f"has max_llm_calls={request.budget.max_llm_calls}"
            )

        return await self._inner_executor.execute(request)
