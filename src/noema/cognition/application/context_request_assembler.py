"""Assemble a ContextRequest from one canonical cognitive-state observation."""

from datetime import timedelta

from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.domain.context import ContextStamp, ContextVersionMarker
from noema.cognition.domain.context_composition import (
    ContextRequest,
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.modes import CognitiveMode


class ContextRequestAssembler:
    """Bridge the canonical runtime cognitive state into a ``ContextRequest``.

    ADR-0028 fixes that the workspace and situation versions carried by a
    ``ContextStamp`` are observed from the canonical snapshots as one logical
    event, before the ``ContextRequest`` that will contain the stamp is built.
    This assembler binds one runtime-instance ``CognitiveStateOwner``, performs
    exactly one ``current_snapshots()`` observation per assembly, derives the
    two observed versions, applies ``ContextVersionMarker.UNMATERIALIZED`` for
    the identity/goal/policy dimensions (no materialized versioned owner exists
    for those under current accepted authority, ADR-0027), constructs the
    ``ContextStamp``, and forwards every other ``ContextRequest`` field from the
    explicit caller input.

    It selects no context policy, composes no context, builds no
    ``ContextPackage`` or ``ReasoningRequest``, chooses no cognitive mode,
    strategy or budget, performs no I/O, and owns no canonical cognitive state.
    """

    __slots__ = ("_state_owner",)

    def __init__(
        self,
        *,
        state_owner: CognitiveStateOwner,
    ) -> None:
        """Bind the runtime-instance owner this assembler observes."""
        if not isinstance(state_owner, CognitiveStateOwner):
            raise TypeError("state_owner must be a CognitiveStateOwner")
        self._state_owner = state_owner

    def assemble(
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
    ) -> ContextRequest:
        """Observe the canonical pair once and return a ``ContextRequest``.

        The ``ContextStamp`` is built here from a single
        ``CognitiveStateOwner.current_snapshots()`` observation; a caller cannot
        supply it. Every other field is forwarded to ``ContextRequest``
        unchanged; ``ContextStamp`` and ``ContextRequest`` own their own
        validation, so an invalid caller value raises the corresponding domain
        error unwrapped.
        """
        workspace, situation = self._state_owner.current_snapshots()
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
            max_tokens=max_tokens,
            context_stamp=context_stamp,
        )
