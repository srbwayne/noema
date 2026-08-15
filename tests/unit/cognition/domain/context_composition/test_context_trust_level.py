from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.context_composition import ContextTrustLevel


def test_context_trust_level_has_exact_semantic_members() -> None:
    assert tuple(ContextTrustLevel.__members__) == (
        "TRUSTED",
        "UNVERIFIED",
        "UNTRUSTED",
    )
    assert tuple(member.value for member in ContextTrustLevel) == (
        "trusted",
        "unverified",
        "untrusted",
    )
    assert issubclass(ContextTrustLevel, Enum)
    assert not issubclass(ContextTrustLevel, IntEnum)
    assert not issubclass(ContextTrustLevel, StrEnum)
    assert all(not isinstance(member.value, int) for member in ContextTrustLevel)
