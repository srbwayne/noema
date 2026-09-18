"""Prepare one coherent ContextPackage from a single canonical snapshot observation."""

from datetime import timedelta

from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.application.context_request_assembler import ContextRequestAssembler
from noema.cognition.application.prior_task_context_projector import PriorTaskContextProjector
from noema.cognition.domain.context_composition import (
    ContextComposer,
    ContextPackage,
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.modes import CognitiveMode


class ContextPackagePreparer:
    """Prepare one ``ContextPackage`` from one canonical cognitive-state observation.

    ADR-0031 introduces this component as the single production owner of
    per-operation canonical-state observation (ADR-0028's
    ``SNAPSHOT_COHERENCE_DESIGN=B``): it calls
    ``CognitiveStateOwner.current_snapshots()`` exactly once per ``prepare()``
    call and threads the exact returned ``workspace``/``situation`` pair into
    both ``ContextRequestAssembler.assemble`` (for the ``ContextStamp``) and,
    when prior-TASK context activation is enabled, ``PriorTaskContextProjector.project``
    (for candidate projection) -- guaranteeing both observe the same canonical
    state rather than risking two independently-observed, potentially
    divergent snapshots.

    When activation is disabled, this component never calls the projector or
    the composer, and returns an empty ``ContextPackage`` -- exactly the
    pre-integration first-DIRECT behavior. When enabled, it augments the
    caller-supplied ``required_slice_types`` with ``ContextSliceType.TASK``
    (never duplicating it, never reordering the caller's existing tuple)
    exactly when the projector returns at least one candidate, and only then
    invokes the bound ``ContextComposer``.

    It performs no current-content registration, no canonical-TASK ingestion,
    no model-input materialization, no reasoning execution, no provider/model
    call, no persistence, no relevance scoring, and selects no
    ``CognitiveBudget``.
    """

    __slots__ = (
        "_state_owner",
        "_context_request_assembler",
        "_prior_task_context_projector",
        "_context_composer",
        "_prior_task_context_enabled",
    )

    def __init__(
        self,
        *,
        state_owner: CognitiveStateOwner,
        context_request_assembler: ContextRequestAssembler,
        prior_task_context_projector: PriorTaskContextProjector,
        context_composer: ContextComposer | None,
        prior_task_context_enabled: bool,
    ) -> None:
        """Bind this preparer's collaborators and freeze its activation policy.

        ``prior_task_context_enabled`` and ``context_composer`` must be
        consistent: enabled requires a bound ``ContextComposer``; disabled
        requires ``None``. An inconsistent pair raises ``TypeError`` rather
        than being silently repaired.
        """
        if not isinstance(state_owner, CognitiveStateOwner):
            raise TypeError("state_owner must be a CognitiveStateOwner")
        if not isinstance(context_request_assembler, ContextRequestAssembler):
            raise TypeError("context_request_assembler must be a ContextRequestAssembler")
        if not isinstance(prior_task_context_projector, PriorTaskContextProjector):
            raise TypeError("prior_task_context_projector must be a PriorTaskContextProjector")
        if not isinstance(prior_task_context_enabled, bool):
            raise TypeError("prior_task_context_enabled must be a bool")
        if prior_task_context_enabled:
            if not isinstance(context_composer, ContextComposer):
                raise TypeError(
                    "context_composer must be a ContextComposer when "
                    "prior_task_context_enabled is True"
                )
        elif context_composer is not None:
            raise TypeError(
                "context_composer must be None when prior_task_context_enabled is False"
            )

        self._state_owner = state_owner
        self._context_request_assembler = context_request_assembler
        self._prior_task_context_projector = prior_task_context_projector
        self._context_composer = context_composer
        self._prior_task_context_enabled = prior_task_context_enabled

    def prepare(
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
    ) -> ContextPackage:
        """Observe the canonical snapshot pair once and return one ``ContextPackage``.

        Calls ``CognitiveStateOwner.current_snapshots()`` exactly once. When
        prior-TASK context activation is disabled, returns
        ``ContextPackage(request=context_request, slices=())`` directly,
        without calling the projector or the composer. When enabled, calls
        the projector exactly once; if it returns no candidates, TASK is not
        added to the required slice types and an empty package is returned
        without calling the composer; if it returns at least one candidate,
        TASK is appended to the required slice types (unless already
        present) and the bound ``ContextComposer`` is called exactly once,
        with its exact resulting ``ContextPackage`` returned unchanged. Any
        error raised by the projector, the assembler, or the composer
        propagates unchanged.
        """
        workspace, situation = self._state_owner.current_snapshots()

        if not self._prior_task_context_enabled:
            context_request = self._context_request_assembler.assemble(
                workspace=workspace,
                situation=situation,
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
            return ContextPackage(request=context_request, slices=())

        candidates = self._prior_task_context_projector.project(situation=situation)

        effective_required_slice_types = required_slice_types
        if candidates and ContextSliceType.TASK not in required_slice_types:
            effective_required_slice_types = (*required_slice_types, ContextSliceType.TASK)

        context_request = self._context_request_assembler.assemble(
            workspace=workspace,
            situation=situation,
            role=role,
            task_ref=task_ref,
            goal_ref=goal_ref,
            mode=mode,
            required_slice_types=effective_required_slice_types,
            forbidden_slice_types=forbidden_slice_types,
            max_sensitivity=max_sensitivity,
            minimum_trust=minimum_trust,
            allowed_authorities=allowed_authorities,
            max_age=max_age,
            max_total_content_size=max_total_content_size,
        )

        if not candidates:
            return ContextPackage(request=context_request, slices=())

        assert self._context_composer is not None  # noqa: S101 -- guaranteed by __init__
        return self._context_composer.compose(request=context_request, candidates=candidates)
