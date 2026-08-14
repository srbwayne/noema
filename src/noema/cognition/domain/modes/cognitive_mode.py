"""Authorized cognitive processing depths."""

from enum import Enum


class CognitiveMode(Enum):
    """Depth and strategy authorized for a cognitive operation."""

    REFLEX = "reflex"
    FAST = "fast"
    DELIBERATE = "deliberate"
    DEEP = "deep"
