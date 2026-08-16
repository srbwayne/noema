"""Declared capabilities a model resource may support."""

from enum import Enum


class ModelCapability(Enum):
    """Identify a capability a model resource declares support for.

    Declaration order carries no priority, preference, ranking, or
    suitability semantics.
    """

    TEXT_GENERATION = "text_generation"
    STRUCTURED_OUTPUT = "structured_output"
    TOOL_CALLING = "tool_calling"
