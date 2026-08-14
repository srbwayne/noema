"""Framework-independent cognition domain model."""

from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.events import CognitiveEvent
from noema.cognition.domain.workspace import (
    CognitiveItem,
    CognitiveItemKind,
    CognitiveWorkspace,
    WorkspaceBudget,
    WorkspaceRegion,
)

__all__ = [
    "CognitiveEvent",
    "CognitiveItem",
    "CognitiveItemKind",
    "CognitiveWorkspace",
    "ContextStamp",
    "WorkspaceBudget",
    "WorkspaceRegion",
]
