from enum import Enum, IntEnum

from noema.cognition.domain.context_composition import InstructionAuthority


def test_instruction_authority_has_exact_semantic_members() -> None:
    assert {member.name: member.value for member in InstructionAuthority} == {
        "SYSTEM_POLICY": "system_policy",
        "AGENT_POLICY": "agent_policy",
        "USER_EXPLICIT": "user_explicit",
        "TASK_CONTROL": "task_control",
        "COGNITIVE_CONTROL": "cognitive_control",
        "EXTERNAL_DATA": "external_data",
        "UNTRUSTED_CONTENT": "untrusted_content",
    }
    assert issubclass(InstructionAuthority, Enum)
    assert not issubclass(InstructionAuthority, IntEnum)
    assert all(not isinstance(member.value, int) for member in InstructionAuthority)
