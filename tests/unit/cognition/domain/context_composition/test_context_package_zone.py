from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.context_composition import ContextPackageZone


def test_context_package_zone_has_exact_semantic_members() -> None:
    assert tuple(ContextPackageZone.__members__) == (
        "CONTROL",
        "COGNITIVE_STATE",
        "VERIFIED_KNOWLEDGE",
        "MEMORY",
        "EXTERNAL_DATA",
        "TOOL_DATA",
    )
    assert tuple(member.value for member in ContextPackageZone) == (
        "control",
        "cognitive_state",
        "verified_knowledge",
        "memory",
        "external_data",
        "tool_data",
    )
    assert issubclass(ContextPackageZone, Enum)
    assert not issubclass(ContextPackageZone, IntEnum)
    assert not issubclass(ContextPackageZone, StrEnum)
    assert all(not isinstance(member.value, int) for member in ContextPackageZone)
