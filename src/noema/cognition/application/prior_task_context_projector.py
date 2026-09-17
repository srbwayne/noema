"""Project canonical prior TASK entries into reference-based context candidates."""

from noema.cognition.application.runtime_content_reference_authority import (
    RuntimeContentReferenceAuthority,
)
from noema.cognition.domain.context_composition import (
    ContextCandidate,
    ContextPackageZone,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
)
from noema.cognition.domain.situation import SituationEntry, SituationEntryKind, SituationModel


class PriorTaskContextProjector:
    """Project every canonical prior TASK entry into a ``ContextCandidate``.

    "Prior" excludes the positionally most-recent ``SituationEntryKind.TASK``
    entry in the supplied snapshot -- that entry is the current operation's
    own task, which already travels separately as
    ``ReasoningRequest.problem_statement`` and must never also be projected
    as context (it would otherwise duplicate the current task). Non-TASK
    entries are never projected. Projection introduces no ranking,
    reordering, or selection: candidates are returned in exact canonical
    Situation order and every classification field is a fixed, static value
    (zone, sensitivity, trust, instruction authority) established
    independently of payload content.

    This component performs no canonical-state observation of its own: it
    receives an already-observed ``SituationModel`` snapshot from its
    caller, so that a future integration can guarantee the same snapshot
    also backs the ``ContextRequest.context_stamp`` it will eventually
    accompany, rather than risking two independently-observed snapshots
    drifting apart. It resolves each prior entry's exact payload through the
    bound ``RuntimeContentReferenceAuthority`` -- read-only, purely to
    measure exact content size -- and never stores, returns, or otherwise
    exposes that payload text. It selects no context policy, applies no
    relevance judgment (every projected candidate's ``relevance`` is
    ``None``, meaning no relevance judgment exists), invokes no
    ``ContextComposer``, constructs no ``ContextPackage``, performs no I/O
    of its own beyond the authority's in-memory resolution, and mutates
    neither the supplied ``SituationModel`` nor the bound authority.
    """

    __slots__ = ("_runtime_content_authority",)

    def __init__(
        self,
        *,
        runtime_content_authority: RuntimeContentReferenceAuthority,
    ) -> None:
        """Bind the runtime-instance content authority this projector resolves through."""
        if not isinstance(runtime_content_authority, RuntimeContentReferenceAuthority):
            raise TypeError("runtime_content_authority must be a RuntimeContentReferenceAuthority")
        self._runtime_content_authority = runtime_content_authority

    def project(
        self,
        *,
        situation: SituationModel,
    ) -> tuple[ContextCandidate, ...]:
        """Return one ``ContextCandidate`` per canonical prior TASK entry.

        Identifies every ``SituationEntryKind.TASK`` entry in ``situation``,
        treats the positionally last one as the current task (excluded), and
        projects every other TASK entry, in canonical order, into a
        reference-based ``ContextCandidate``. Returns an empty tuple when
        ``situation`` contains zero or exactly one TASK entry -- with at
        most one TASK entry there is no prior task to project, and this is
        not a failure. Any error raised while resolving a prior entry's
        payload, or while constructing its ``ContextSlice`` or
        ``ContextCandidate``, propagates unchanged.
        """
        task_entries = situation.entries_of_kind(SituationEntryKind.TASK)
        if len(task_entries) < 2:
            return ()

        prior_entries = task_entries[:-1]
        return tuple(
            self._project_entry(entry=entry, situation=situation) for entry in prior_entries
        )

    def _project_entry(
        self,
        *,
        entry: SituationEntry,
        situation: SituationModel,
    ) -> ContextCandidate:
        payload = self._runtime_content_authority.resolve(content_ref=entry.content_ref)
        context_slice = ContextSlice(
            slice_type=ContextSliceType.TASK,
            content_ref=entry.content_ref,
            zone=ContextPackageZone.COGNITIVE_STATE,
            sensitivity=ContextSensitivity.SECRET,
            trust=ContextTrustLevel.UNVERIFIED,
            instruction_authority=None,
            provenance_ref=str(entry.entry_id),
            content_size=len(payload),
        )
        return ContextCandidate(
            context_slice=context_slice,
            relevance=None,
            age=situation.updated_at - entry.created_at,
        )
