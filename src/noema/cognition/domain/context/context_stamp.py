"""Version snapshot for a cognitive operation."""

from dataclasses import dataclass
from enum import Enum

from noema.cognition.domain.errors import InvalidContextVersionError


class ContextVersionMarker(Enum):
    """An explicit non-integer state for a ContextStamp dimension without a materialized owner."""

    UNMATERIALIZED = "unmaterialized"


_MARKER_ELIGIBLE_FIELDS = frozenset({"identity_version", "goal_version", "policy_version"})


def _is_observed_version(value: object) -> bool:
    """Return whether value is a valid non-negative observed integer version."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


@dataclass(frozen=True, slots=True)
class ContextStamp:
    """Versions of cognitive state observed when an operation starts.

    ``workspace_version`` and ``situation_version`` name dimensions whose owner is
    currently materialized (``CognitiveWorkspace``, ``SituationModel``); each accepts
    only a non-negative observed integer version. ``identity_version``,
    ``goal_version``, and ``policy_version`` name dimensions whose owner is not
    currently materialized; each accepts a non-negative observed integer version or
    ``ContextVersionMarker.UNMATERIALIZED`` (ADR-0027). This admissibility scope is
    current accepted-authority scope, not a permanent statement about any dimension.
    """

    workspace_version: int
    situation_version: int
    identity_version: int | ContextVersionMarker
    goal_version: int | ContextVersionMarker
    policy_version: int | ContextVersionMarker

    def __post_init__(self) -> None:
        """Reject values that cannot represent an observed state, or an admissible marker."""
        versions = (
            ("workspace_version", self.workspace_version),
            ("situation_version", self.situation_version),
            ("identity_version", self.identity_version),
            ("goal_version", self.goal_version),
            ("policy_version", self.policy_version),
        )
        for name, version in versions:
            if name in _MARKER_ELIGIBLE_FIELDS and version is ContextVersionMarker.UNMATERIALIZED:
                continue
            if not _is_observed_version(version):
                if name in _MARKER_ELIGIBLE_FIELDS:
                    raise InvalidContextVersionError(
                        f"{name} must be a non-negative integer "
                        "or ContextVersionMarker.UNMATERIALIZED"
                    )
                raise InvalidContextVersionError(f"{name} must be greater than or equal to zero")
