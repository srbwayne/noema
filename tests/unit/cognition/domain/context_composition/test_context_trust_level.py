from enum import Enum, IntEnum

from noema.cognition.domain.context_composition import ContextTrustLevel


def test_context_trust_level_has_exact_semantic_members() -> None:
    assert {member.name: member.value for member in ContextTrustLevel} == {
        "TRUSTED": "trusted",
        "UNVERIFIED": "unverified",
        "UNTRUSTED": "untrusted",
    }
    assert issubclass(ContextTrustLevel, Enum)
    assert not issubclass(ContextTrustLevel, IntEnum)
    assert all(not isinstance(member.value, int) for member in ContextTrustLevel)
