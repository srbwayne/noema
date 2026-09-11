"""The first DIRECT cognition application operation."""

from datetime import timedelta

from noema.cognition.application.context_request_assembler import ContextRequestAssembler
from noema.cognition.application.direct_reasoning_request_assembler import (
    assemble_direct_reasoning_request,
)
from noema.cognition.application.reasoning_engine import ReasoningEngine
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import (
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import ReasoningOutcome


class DirectReasoningOperation:
    """Execute the first DIRECT reasoning operation end to end.

    Binds one ``ContextRequestAssembler`` and one ``ReasoningEngine`` and, for
    each ``execute`` call, joins exactly one canonical ``ContextRequest``
    assembly (C3), exactly one DIRECT ``ReasoningRequest`` assembly (D1), and
    exactly one ``ReasoningEngine.reason`` execution, returning the resulting
    ``ReasoningOutcome`` unchanged.

    It selects no context policy, no ``CognitiveBudget`` values and no
    reasoning strategy, observes no canonical cognitive state directly,
    constructs no ``ContextPackage`` or ``ReasoningRequest`` itself, and
    performs no I/O of its own; any domain or execution error raised by C3,
    D1, or the ``ReasoningEngine`` propagates unchanged.
    """

    __slots__ = (
        "_context_request_assembler",
        "_reasoning_engine",
    )

    def __init__(
        self,
        *,
        context_request_assembler: ContextRequestAssembler,
        reasoning_engine: ReasoningEngine,
    ) -> None:
        """Bind the assembler and engine this operation delegates to."""
        if not isinstance(context_request_assembler, ContextRequestAssembler):
            raise TypeError("context_request_assembler must be a ContextRequestAssembler")
        if not isinstance(reasoning_engine, ReasoningEngine):
            raise TypeError("reasoning_engine must be a ReasoningEngine")
        self._context_request_assembler = context_request_assembler
        self._reasoning_engine = reasoning_engine

    async def execute(
        self,
        *,
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
        max_tokens: int,
        problem_ref: str,
        problem_statement: str,
        budget: CognitiveBudget,
    ) -> ReasoningOutcome:
        """Assemble the DIRECT reasoning request and execute it once.

        Observes the canonical cognitive state exactly once, transitively,
        through the bound ``ContextRequestAssembler``; selects no context
        policy, budget values, or strategy; and returns the exact
        ``ReasoningOutcome`` produced by the bound ``ReasoningEngine``. Any
        error raised while assembling the ``ContextRequest``, assembling the
        DIRECT ``ReasoningRequest``, or executing it propagates unwrapped.
        """
        context_request = self._context_request_assembler.assemble(
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
            max_tokens=max_tokens,
        )
        reasoning_request = assemble_direct_reasoning_request(
            context_request=context_request,
            problem_ref=problem_ref,
            problem_statement=problem_statement,
            budget=budget,
        )
        return await self._reasoning_engine.reason(reasoning_request)
