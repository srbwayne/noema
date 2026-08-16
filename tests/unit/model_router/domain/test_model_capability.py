from enum import Enum, Flag, IntEnum, IntFlag

import pytest

from noema.model_router.domain import ModelCapability

EXACT_MEMBER_VALUES = {
    "TEXT_GENERATION": "text_generation",
    "STRUCTURED_OUTPUT": "structured_output",
    "TOOL_CALLING": "tool_calling",
}


def test_model_capability_has_exactly_the_approved_members_and_values() -> None:
    actual = {member.name: member.value for member in ModelCapability}
    assert actual == EXACT_MEMBER_VALUES


@pytest.mark.parametrize("name,value", list(EXACT_MEMBER_VALUES.items()))
def test_model_capability_member_maps_to_exact_value(name: str, value: str) -> None:
    assert ModelCapability[name].value == value


def test_model_capability_is_a_plain_enum() -> None:
    assert issubclass(ModelCapability, Enum)
    assert not issubclass(ModelCapability, IntEnum)
    assert not issubclass(ModelCapability, Flag)
    assert not issubclass(ModelCapability, IntFlag)


def test_model_capability_does_not_expose_ordering_or_ranking_metadata() -> None:
    forbidden = {
        "priority",
        "rank",
        "score",
        "weight",
        "precedence",
        "order",
        "cost",
        "latency",
    }
    declared_members = set(vars(ModelCapability))
    assert declared_members.isdisjoint(forbidden)


def test_model_capability_members_are_not_ordinally_comparable() -> None:
    with pytest.raises(TypeError):
        _ = ModelCapability.TEXT_GENERATION < ModelCapability.TOOL_CALLING  # type: ignore[operator]
