"""Authorized cognitive processing depths."""

from enum import Enum, auto


class CognitiveMode(Enum):
    """Depth and strategy authorized for a cognitive operation."""

    REFLEX = auto()
    FAST = auto()
    DELIBERATE = auto()
    DEEP = auto()
