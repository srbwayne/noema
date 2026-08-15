from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.reasoning import ReasoningStatus


def test_reasoning_status_has_exact_contract() -> None:
    assert tuple(ReasoningStatus.__members__) == (
        "COMPLETED",
        "PARTIAL",
        "NEEDS_INFORMATION",
        "UNRESOLVED",
    )
    assert tuple(member.value for member in ReasoningStatus) == (
        "completed",
        "partial",
        "needs_information",
        "unresolved",
    )
    assert len(ReasoningStatus) == 4
    assert issubclass(ReasoningStatus, Enum)
    assert not issubclass(ReasoningStatus, IntEnum)
    assert not issubclass(ReasoningStatus, StrEnum)
    assert all(not isinstance(member.value, int) for member in ReasoningStatus)
