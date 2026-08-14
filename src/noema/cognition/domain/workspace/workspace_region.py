"""Regions of the bounded cognitive workspace."""

from enum import Enum


class WorkspaceRegion(Enum):
    """Region in which an item is cognitively active."""

    ACTIVE_CONTEXT = "active_context"
    WORKING_STATE = "working_state"
    PERIPHERAL_BUFFER = "peripheral_buffer"
