"""Ingest the current first-DIRECT task into canonical runtime state."""

from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.domain.situation import SituationDelta, SituationEntry, SituationEntryKind


class CanonicalInputIngestor:
    """Retain the current first-DIRECT task as a canonical Situation entry.

    M0-16 (first-process fixed policy): every first-DIRECT invocation is
    treated as the task the runtime has been assigned, not as a judgment
    about the linguistic shape of its problem statement. This component
    represents that task with exactly one ``SituationEntryKind.TASK``
    entry whose ``content_ref`` is the exact, unmodified ``task_ref`` --
    never the raw problem text, and never ``problem_ref`` (which remains
    the reasoning-problem/outcome correlation identity, a separate role).

    It performs exactly one canonical observation, constructs the
    successor ``SituationModel`` through the domain's own ``apply``
    transition, and retains that successor through the bound
    ``CognitiveStateOwner``. It selects no Workspace policy, ingests no
    Workspace item, retries nothing, and rolls back nothing: a failure
    here propagates unchanged and a downstream failure after a successful
    ingestion never triggers a second attempt or a compensating reversal.
    """

    __slots__ = ("_state_owner",)

    def __init__(
        self,
        *,
        state_owner: CognitiveStateOwner,
    ) -> None:
        """Bind the runtime-instance owner this ingestor retains successors through."""
        if not isinstance(state_owner, CognitiveStateOwner):
            raise TypeError("state_owner must be a CognitiveStateOwner")
        self._state_owner = state_owner

    def ingest_task(self, *, task_ref: str) -> None:
        """Retain one canonical TASK Situation entry for ``task_ref``.

        Observes the canonical Situation exactly once, builds a single
        ``SituationDelta`` adding exactly one ``SituationEntryKind.TASK``
        entry whose ``content_ref`` is the exact ``task_ref`` value, applies
        it to produce an exact-successor ``SituationModel``, and retains
        that successor through ``CognitiveStateOwner.replace_situation``.
        The canonical Workspace is observed but never modified. Any error
        raised while constructing the entry, the delta, applying it, or
        replacing the canonical Situation propagates unchanged.
        """
        _, situation = self._state_owner.current_snapshots()

        task_entry = SituationEntry(
            kind=SituationEntryKind.TASK,
            content_ref=task_ref,
        )
        delta = SituationDelta(
            base_version=situation.version,
            added=(task_entry,),
        )
        successor = situation.apply(delta)

        self._state_owner.replace_situation(successor)
