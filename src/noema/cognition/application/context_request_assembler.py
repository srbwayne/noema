"""Assemble a ContextRequest from one caller-supplied cognitive-state snapshot pair."""

from datetime import timedelta

from noema.cognition.domain.context import ContextStamp, ContextVersionMarker
from noema.cognition.domain.context_composition import (
    ContextRequest,
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.situation import SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace


class ContextRequestAssembler:
    """Bridge an explicit canonical snapshot pair into a ``ContextRequest``.

    ADR-0031 makes this assembler snapshot-parameterized: it performs zero
    canonical-state observations of its own. Its caller (``ContextPackagePreparer``)
    observes the canonical ``CognitiveWorkspace``/``SituationModel`` pair exactly
    once per context preparation and supplies that exact pair here, so the
    ``ContextStamp`` this assembler builds is guaranteed to reflect the same
    observation any candidate projection sharing that preparation also used --
    rather than risking two independently-observed, potentially divergent
    snapshots (ADR-0028's coherence guarantee, realized by ADR-0031's
    single-observation-per-preparation contract).

    It selects no context policy, composes no context, builds no
    ``ContextPackage`` or ``ReasoningRequest``, chooses no cognitive mode,
    strategy or budget, performs no I/O, and owns no canonical cognitive state.
    """

    __slots__ = ()

    def assemble(
        self,
        *,
        workspace: CognitiveWorkspace,
        situation: SituationModel,
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
    ) -> ContextRequest:
        """Build a ``ContextRequest`` from the exact caller-supplied snapshot pair.

        The ``ContextStamp`` is built from ``workspace.version`` and
        ``situation.version`` exactly as supplied -- this assembler performs no
        observation of its own and clones neither snapshot. Every other field
        is forwarded to ``ContextRequest`` unchanged; ``ContextRequest`` owns
        its own validation, so an invalid caller value raises the
        corresponding domain error unwrapped.
        """
        if not isinstance(workspace, CognitiveWorkspace):
            raise TypeError("workspace must be a CognitiveWorkspace")
        if not isinstance(situation, SituationModel):
            raise TypeError("situation must be a SituationModel")

        context_stamp = ContextStamp(
            workspace_version=workspace.version,
            situation_version=situation.version,
            identity_version=ContextVersionMarker.UNMATERIALIZED,
            goal_version=ContextVersionMarker.UNMATERIALIZED,
            policy_version=ContextVersionMarker.UNMATERIALIZED,
        )
        return ContextRequest(
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
            context_stamp=context_stamp,
        )
