"""The first DIRECT cognition application operation."""

from datetime import timedelta

from noema.cognition.application.canonical_input_ingestor import CanonicalInputIngestor
from noema.cognition.application.context_package_preparer import ContextPackagePreparer
from noema.cognition.application.direct_reasoning_request_assembler import (
    assemble_direct_reasoning_request,
)
from noema.cognition.application.reasoning_engine import ReasoningEngine
from noema.cognition.application.runtime_content_reference_authority import (
    RuntimeContentReferenceAuthority,
)
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

    Binds one ``RuntimeContentReferenceAuthority``, one
    ``CanonicalInputIngestor``, one ``ContextPackagePreparer``, and one
    ``ReasoningEngine`` and, for each ``execute`` call, joins exactly one
    runtime content-reference registration (M0-18), exactly one
    canonical-task ingestion (M0-16), exactly one ``ContextPackage``
    preparation (ADR-0031), exactly one DIRECT ``ReasoningRequest`` assembly
    (D1), and exactly one ``ReasoningEngine.reason`` execution, returning the
    resulting ``ReasoningOutcome`` unchanged.

    It selects no context policy, no ``CognitiveBudget`` values and no
    reasoning strategy, observes no canonical cognitive state directly,
    constructs no ``SituationEntry``, ``SituationDelta``, ``ContextPackage``,
    or ``ReasoningRequest`` itself, resolves no runtime content reference
    itself, materializes no model input, and performs no I/O of its own; any
    error raised by the authority, the ingestor, the preparer, the
    ``ReasoningRequest`` assembly, or the ``ReasoningEngine`` propagates
    unchanged. Registration is retained even if canonical ingestion or any
    later step then fails -- this operation never deletes, replaces, or
    otherwise compensates a successful registration, and a failure after a
    successful ingestion never triggers a second ingestion attempt or any
    compensating reversal.
    """

    __slots__ = (
        "_runtime_content_authority",
        "_canonical_input_ingestor",
        "_context_package_preparer",
        "_reasoning_engine",
    )

    def __init__(
        self,
        *,
        runtime_content_authority: RuntimeContentReferenceAuthority,
        canonical_input_ingestor: CanonicalInputIngestor,
        context_package_preparer: ContextPackagePreparer,
        reasoning_engine: ReasoningEngine,
    ) -> None:
        """Bind the authority, ingestor, preparer, and engine this operation delegates to."""
        if not isinstance(runtime_content_authority, RuntimeContentReferenceAuthority):
            raise TypeError("runtime_content_authority must be a RuntimeContentReferenceAuthority")
        if not isinstance(canonical_input_ingestor, CanonicalInputIngestor):
            raise TypeError("canonical_input_ingestor must be a CanonicalInputIngestor")
        if not isinstance(context_package_preparer, ContextPackagePreparer):
            raise TypeError("context_package_preparer must be a ContextPackagePreparer")
        if not isinstance(reasoning_engine, ReasoningEngine):
            raise TypeError("reasoning_engine must be a ReasoningEngine")
        self._runtime_content_authority = runtime_content_authority
        self._canonical_input_ingestor = canonical_input_ingestor
        self._context_package_preparer = context_package_preparer
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
        max_total_content_size: int,
        problem_ref: str,
        problem_statement: str,
        budget: CognitiveBudget,
    ) -> ReasoningOutcome:
        """Register the task content, ingest the canonical task, and execute once.

        Registers ``task_ref`` as denoting the exact ``problem_statement``
        through the bound ``RuntimeContentReferenceAuthority`` (M0-18) before
        retaining ``task_ref`` as the canonical current task (M0-16) through
        the bound ``CanonicalInputIngestor``; this ordering guarantees that
        whenever a TASK reference becomes canonical here, its exact payload
        is already resolvable through the authority, and that the bound
        ``ContextPackagePreparer``'s single canonical-state observation
        already reflects this operation's own TASK entry as the positionally
        latest one. It then prepares exactly one ``ContextPackage`` through
        the bound ``ContextPackagePreparer``; selects no context policy,
        budget values, or strategy; and returns the exact ``ReasoningOutcome``
        produced by the bound ``ReasoningEngine``. Any error raised while
        registering the content, ingesting the task, preparing the
        ``ContextPackage``, assembling the DIRECT ``ReasoningRequest``, or
        executing it propagates unwrapped, and a successful registration is
        never deleted, replaced, or otherwise compensated by a later failure.
        """
        self._runtime_content_authority.register(
            content_ref=task_ref,
            payload=problem_statement,
        )
        self._canonical_input_ingestor.ingest_task(task_ref=task_ref)

        context_package = self._context_package_preparer.prepare(
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
        )
        reasoning_request = assemble_direct_reasoning_request(
            context=context_package,
            problem_ref=problem_ref,
            problem_statement=problem_statement,
            budget=budget,
        )
        return await self._reasoning_engine.reason(reasoning_request)
