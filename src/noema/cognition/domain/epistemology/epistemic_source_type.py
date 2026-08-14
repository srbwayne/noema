"""Infrastructure-independent kinds of epistemic sources."""

from enum import Enum


class EpistemicSourceType(Enum):
    """Category of the origin from which a claim was obtained."""

    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"
    MODEL = "model"
    MEMORY = "memory"
    DOCUMENT = "document"
