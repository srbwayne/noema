from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.context_composition import InstructionAuthority


def test_instruction_authority_has_exact_semantic_members() -> None:
    assert tuple(InstructionAuthority.__members__) == (
        "SYSTEM_POLICY",
        "AGENT_POLICY",
        "USER_EXPLICIT",
        "TASK_CONTROL",
        "COGNITIVE_CONTROL",
        "EXTERNAL_DATA",
        "UNTRUSTED_CONTENT",
    )
    assert tuple(member.value for member in InstructionAuthority) == (
        "system_policy",
        "agent_policy",
        "user_explicit",
        "task_control",
        "cognitive_control",
        "external_data",
        "untrusted_content",
    )
    assert issubclass(InstructionAuthority, Enum)
    assert not issubclass(InstructionAuthority, IntEnum)
    assert not issubclass(InstructionAuthority, StrEnum)
    assert all(not isinstance(member.value, int) for member in InstructionAuthority)
