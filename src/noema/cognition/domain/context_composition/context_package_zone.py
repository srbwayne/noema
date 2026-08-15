"""Structural zones for future context packages."""

from enum import Enum


class ContextPackageZone(Enum):
    """Identify the structural destination of a context slice."""

    CONTROL = "control"
    COGNITIVE_STATE = "cognitive_state"
    VERIFIED_KNOWLEDGE = "verified_knowledge"
    MEMORY = "memory"
    EXTERNAL_DATA = "external_data"
    TOOL_DATA = "tool_data"
