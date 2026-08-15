from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.context_composition import ContextSliceType


def test_context_slice_type_has_exact_semantic_members() -> None:
    assert tuple(ContextSliceType.__members__) == (
        "IDENTITY",
        "GOAL",
        "TASK",
        "SITUATION",
        "MEMORY",
        "EVIDENCE",
        "CLAIM",
        "HYPOTHESIS",
        "PLAN",
        "POLICY",
        "CONSTRAINT",
        "EMOTION",
        "SELF_MODEL",
        "CAPABILITY",
        "TOOL",
        "HISTORY",
        "ENVIRONMENT",
    )
    assert tuple(member.value for member in ContextSliceType) == (
        "identity",
        "goal",
        "task",
        "situation",
        "memory",
        "evidence",
        "claim",
        "hypothesis",
        "plan",
        "policy",
        "constraint",
        "emotion",
        "self_model",
        "capability",
        "tool",
        "history",
        "environment",
    )
    assert issubclass(ContextSliceType, Enum)
    assert not issubclass(ContextSliceType, IntEnum)
    assert not issubclass(ContextSliceType, StrEnum)
    assert all(not isinstance(member.value, int) for member in ContextSliceType)
