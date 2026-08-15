from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.context_composition import ContextSensitivity


def test_context_sensitivity_has_exact_semantic_members() -> None:
    assert tuple(ContextSensitivity.__members__) == (
        "PUBLIC",
        "INTERNAL",
        "PRIVATE",
        "SECRET",
    )
    assert tuple(member.value for member in ContextSensitivity) == (
        "public",
        "internal",
        "private",
        "secret",
    )
    assert issubclass(ContextSensitivity, Enum)
    assert not issubclass(ContextSensitivity, IntEnum)
    assert not issubclass(ContextSensitivity, StrEnum)
    assert all(not isinstance(member.value, int) for member in ContextSensitivity)
