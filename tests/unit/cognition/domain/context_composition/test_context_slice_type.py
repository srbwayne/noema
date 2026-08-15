from enum import Enum, IntEnum

from noema.cognition.domain.context_composition import ContextSliceType


def test_context_slice_type_has_exact_semantic_members() -> None:
    expected = {
        "IDENTITY": "identity",
        "GOAL": "goal",
        "TASK": "task",
        "SITUATION": "situation",
        "MEMORY": "memory",
        "EVIDENCE": "evidence",
        "CLAIM": "claim",
        "HYPOTHESIS": "hypothesis",
        "PLAN": "plan",
        "POLICY": "policy",
        "CONSTRAINT": "constraint",
        "EMOTION": "emotion",
        "SELF_MODEL": "self_model",
        "CAPABILITY": "capability",
        "TOOL": "tool",
        "HISTORY": "history",
        "ENVIRONMENT": "environment",
    }
    assert {member.name: member.value for member in ContextSliceType} == expected
    assert issubclass(ContextSliceType, Enum)
    assert not issubclass(ContextSliceType, IntEnum)
    assert all(not isinstance(member.value, int) for member in ContextSliceType)
