from enum import Enum, IntEnum

from noema.cognition.domain.modes import CognitiveMode


def test_cognitive_mode_has_exactly_the_official_modes() -> None:
    assert tuple(CognitiveMode.__members__) == (
        "REFLEX",
        "FAST",
        "DELIBERATE",
        "DEEP",
    )


def test_cognitive_mode_is_enum_but_not_int_enum() -> None:
    assert issubclass(CognitiveMode, Enum)
    assert not issubclass(CognitiveMode, IntEnum)


def test_cognitive_mode_has_explicit_semantic_values() -> None:
    assert tuple(mode.value for mode in CognitiveMode) == (
        "reflex",
        "fast",
        "deliberate",
        "deep",
    )
    assert all(not isinstance(mode.value, int) for mode in CognitiveMode)
