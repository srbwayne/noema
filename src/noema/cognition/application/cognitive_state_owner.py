"""Runtime authority for the canonical CognitiveWorkspace and SituationModel."""

from noema.cognition.domain.situation import SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace


class InvalidCognitiveStateReplacementError(Exception):
    """Raised when a replacement snapshot does not continue the canonical lineage.

    This is a runtime lifecycle-continuity violation, not a domain invariant
    violation: the replacement snapshot may itself be structurally valid while
    still failing to continue the canonical Workspace or Situation lineage --
    a different logical identifier, a stale or skipped version, or a different
    object claiming the current version. It inherits directly from ``Exception``
    rather than ``DomainError`` for that reason.
    """


class CognitiveStateOwner:
    """Hold the canonical current Workspace and Situation for one runtime instance.

    ADR-0028 gives one logical owner the lifetime of a runtime instance and makes
    it the single canonical source of both the current ``CognitiveWorkspace`` and
    the current ``SituationModel``. The owner receives already-valid initial
    snapshots, retains each immutable exact-successor replacement snapshot as the
    new canonical snapshot, and exposes the canonical pair for downstream
    observation.

    The owner performs no domain transition, constructs no snapshot, produces no
    ``ContextStamp``, composes no context, runs no reasoning, wires no object
    graph, persists nothing, and synchronizes no concurrent callers. Two
    independently constructed owners are fully independent.
    """

    __slots__ = ("_workspace", "_situation")

    def __init__(
        self,
        *,
        workspace: CognitiveWorkspace,
        situation: SituationModel,
    ) -> None:
        """Retain the already-valid initial Workspace and Situation snapshots."""
        if not isinstance(workspace, CognitiveWorkspace):
            raise TypeError("workspace must be a CognitiveWorkspace")
        if not isinstance(situation, SituationModel):
            raise TypeError("situation must be a SituationModel")
        self._workspace = workspace
        self._situation = situation

    def current_snapshots(self) -> tuple[CognitiveWorkspace, SituationModel]:
        """Return the canonical current Workspace and Situation as one ordered pair."""
        return (self._workspace, self._situation)

    def replace_workspace(self, replacement: CognitiveWorkspace) -> None:
        """Retain replacement as canonical iff it is an exact successor of the current Workspace.

        The current canonical Workspace itself is accepted as a no-op. Any other
        replacement must carry the same ``workspace_id`` and exactly the next
        ``version``; a different identifier, a stale or equal version, a
        different object at the current version, or a skipped version raises
        ``InvalidCognitiveStateReplacementError``. The owner runs no Workspace
        domain transition.
        """
        if not isinstance(replacement, CognitiveWorkspace):
            raise TypeError("replacement must be a CognitiveWorkspace")
        if replacement is self._workspace:
            return
        if replacement.workspace_id != self._workspace.workspace_id:
            raise InvalidCognitiveStateReplacementError(
                "replacement workspace_id must match the canonical workspace_id"
            )
        if replacement.version != self._workspace.version + 1:
            raise InvalidCognitiveStateReplacementError(
                "replacement workspace version must be exactly the next canonical version"
            )
        self._workspace = replacement

    def replace_situation(self, replacement: SituationModel) -> None:
        """Retain replacement as canonical iff it is an exact successor of the current Situation.

        The current canonical Situation itself is accepted as a no-op. Any other
        replacement must carry the same ``situation_id`` and exactly the next
        ``version``; a different identifier, a stale or equal version, a
        different object at the current version, or a skipped version raises
        ``InvalidCognitiveStateReplacementError``. The owner runs no Situation
        domain transition.
        """
        if not isinstance(replacement, SituationModel):
            raise TypeError("replacement must be a SituationModel")
        if replacement is self._situation:
            return
        if replacement.situation_id != self._situation.situation_id:
            raise InvalidCognitiveStateReplacementError(
                "replacement situation_id must match the canonical situation_id"
            )
        if replacement.version != self._situation.version + 1:
            raise InvalidCognitiveStateReplacementError(
                "replacement situation version must be exactly the next canonical version"
            )
        self._situation = replacement
