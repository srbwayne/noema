from enum import Enum, IntEnum

from noema.cognition.domain.context_composition import ContextSensitivity


def test_context_sensitivity_has_exact_semantic_members() -> None:
    assert {member.name: member.value for member in ContextSensitivity} == {
        "PUBLIC": "public",
        "INTERNAL": "internal",
        "PRIVATE": "private",
        "SECRET": "secret",
    }
    assert issubclass(ContextSensitivity, Enum)
    assert not issubclass(ContextSensitivity, IntEnum)
    assert all(not isinstance(member.value, int) for member in ContextSensitivity)
