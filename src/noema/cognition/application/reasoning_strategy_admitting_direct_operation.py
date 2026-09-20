"""Admit an explicit reasoning-strategy demand before running the first DIRECT operation."""

from datetime import timedelta

from noema.cognition.application.direct_reasoning_operation import DirectReasoningOperation
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import (
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningStrategy,
    ReasoningStrategyDemand,
    ReasoningStrategySelector,
)


class UnsupportedReasoningStrategyError(Exception):
    """Raised when a validly resolved reasoning strategy cannot be executed.

    The selected ``ReasoningStrategy`` is perfectly valid domain state --
    ``ReasoningStrategySelector`` resolved it deterministically from an
    unambiguous demand. What is true instead is that this runtime
    composition (this admission wrapper plus ``DirectReasoningOperation``)
    supports executing only ``ReasoningStrategy.DIRECT`` today. This is an
    application-owned runtime-capability limitation, not a domain
    construction invariant, a provider/technical execution failure, or a
    cognitive budget-policy failure -- so it inherits directly from
    ``Exception`` rather than ``DomainError`` or ``ReasoningExecutionError``,
    exactly as ``UnsupportedPriorTaskContextSliceError`` already does for its
    own, structurally analogous "valid input this component cannot yet
    handle" case.
    """


class ReasoningStrategyAdmittingDirectOperation:
    """Admit an explicit ``ReasoningStrategyDemand`` before delegating to DIRECT.

    Wraps exactly one injected ``ReasoningStrategySelector`` and one injected
    ``DirectReasoningOperation``. It structurally implements no port -- it is
    a new, additive application entry point standing beside
    ``DirectReasoningOperation``, not a replacement for it -- and adds no
    reasoning-strategy semantics of its own: it delegates strategy
    resolution entirely to the unmodified ``ReasoningStrategySelector``.

    ``ReasoningStrategyDemand`` is caller-supplied per reasoning operation;
    this component never infers it from ``problem_statement`` or any other
    content, and a missing demand is never treated as equivalent to an
    explicit all-``False`` demand -- ``execute`` requires an actual
    ``ReasoningStrategyDemand`` instance.

    When the selector resolves the demand to ``ReasoningStrategy.DIRECT``,
    this delegates to the bound ``DirectReasoningOperation.execute`` exactly
    once, forwarding every argument unchanged, and returns its exact
    ``ReasoningOutcome`` by identity. When the selector resolves the demand
    to any other single strategy, this raises
    ``UnsupportedReasoningStrategyError`` -- because only DIRECT is
    executable in this runtime slice -- strictly before calling
    ``DirectReasoningOperation.execute``, so no content registration, no
    TASK ingestion, no context preparation, no ``CognitiveBudget``
    admission, and no provider work ever occurs for a denied demand; there
    is no specialized-to-DIRECT fallback. When the selector raises
    ``AmbiguousReasoningStrategyError`` (multiple active specialized
    requirements), that exact exception propagates unchanged, and
    ``DirectReasoningOperation.execute`` is likewise never called.
    """

    __slots__ = ("_selector", "_direct_operation")

    def __init__(
        self,
        *,
        selector: ReasoningStrategySelector,
        direct_operation: DirectReasoningOperation,
    ) -> None:
        """Bind the exact selector and DIRECT operation this admission delegates to."""
        if not isinstance(selector, ReasoningStrategySelector):
            raise TypeError("selector must be a ReasoningStrategySelector")
        if not isinstance(direct_operation, DirectReasoningOperation):
            raise TypeError("direct_operation must be a DirectReasoningOperation")
        self._selector = selector
        self._direct_operation = direct_operation

    async def execute(
        self,
        *,
        demand: ReasoningStrategyDemand,
        role: str,
        task_ref: str,
        goal_ref: str | None,
        mode: CognitiveMode,
        required_slice_types: tuple[ContextSliceType, ...],
        forbidden_slice_types: tuple[ContextSliceType, ...],
        max_sensitivity: ContextSensitivity,
        minimum_trust: ContextTrustLevel,
        allowed_authorities: tuple[InstructionAuthority, ...],
        max_age: timedelta | None,
        max_total_content_size: int,
        problem_ref: str,
        problem_statement: str,
        budget: CognitiveBudget,
    ) -> ReasoningOutcome:
        """Admit ``demand`` and, only if DIRECT, run the bound DIRECT operation.

        Rejects a non-``ReasoningStrategyDemand`` ``demand`` with
        ``TypeError`` before any resolution is attempted. Calls the bound
        ``ReasoningStrategySelector.select`` exactly once; an
        ``AmbiguousReasoningStrategyError`` it raises propagates unchanged.
        A resolved ``ReasoningStrategy.DIRECT`` delegates to the bound
        ``DirectReasoningOperation.execute`` exactly once with every other
        argument forwarded exactly as received, returning its exact
        ``ReasoningOutcome``; any exception it raises propagates unchanged.
        A resolved specialized strategy raises
        ``UnsupportedReasoningStrategyError`` without calling
        ``DirectReasoningOperation.execute`` at all.
        """
        if not isinstance(demand, ReasoningStrategyDemand):
            raise TypeError("demand must be a ReasoningStrategyDemand")

        decision = self._selector.select(demand)

        if decision.selected_strategy is not ReasoningStrategy.DIRECT:
            raise UnsupportedReasoningStrategyError(
                f"{decision.selected_strategy.name} is not executable by this "
                f"runtime composition (reason={decision.reason.name}); only "
                f"{ReasoningStrategy.DIRECT.name} is currently supported"
            )

        return await self._direct_operation.execute(
            role=role,
            task_ref=task_ref,
            goal_ref=goal_ref,
            mode=mode,
            required_slice_types=required_slice_types,
            forbidden_slice_types=forbidden_slice_types,
            max_sensitivity=max_sensitivity,
            minimum_trust=minimum_trust,
            allowed_authorities=allowed_authorities,
            max_age=max_age,
            max_total_content_size=max_total_content_size,
            problem_ref=problem_ref,
            problem_statement=problem_statement,
            budget=budget,
        )
