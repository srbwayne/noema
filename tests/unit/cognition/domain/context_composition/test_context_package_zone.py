from enum import Enum, IntEnum

from noema.cognition.domain.context_composition import ContextPackageZone


def test_context_package_zone_has_exact_semantic_members() -> None:
    assert {member.name: member.value for member in ContextPackageZone} == {
        "CONTROL": "control",
        "COGNITIVE_STATE": "cognitive_state",
        "VERIFIED_KNOWLEDGE": "verified_knowledge",
        "MEMORY": "memory",
        "EXTERNAL_DATA": "external_data",
        "TOOL_DATA": "tool_data",
    }
    assert issubclass(ContextPackageZone, Enum)
    assert not issubclass(ContextPackageZone, IntEnum)
    assert all(not isinstance(member.value, int) for member in ContextPackageZone)
