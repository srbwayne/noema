"""Version snapshot for a cognitive operation."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidContextVersionError


@dataclass(frozen=True, slots=True)
class ContextStamp:
    """Versions of cognitive state observed when an operation starts."""

    workspace_version: int
    situation_version: int
    identity_version: int
    goal_version: int
    policy_version: int

    def __post_init__(self) -> None:
        """Reject versions that cannot represent an observed state."""
        versions = (
            ("workspace_version", self.workspace_version),
            ("situation_version", self.situation_version),
            ("identity_version", self.identity_version),
            ("goal_version", self.goal_version),
            ("policy_version", self.policy_version),
        )
        for name, version in versions:
            if version < 0:
                raise InvalidContextVersionError(f"{name} must be greater than or equal to zero")
