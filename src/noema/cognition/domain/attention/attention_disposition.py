"""Possible outcomes of attention evaluation."""

from enum import Enum


class AttentionDisposition(Enum):
    """Disposition assigned to an evaluated attention candidate."""

    IGNORE = "ignore"
    BUFFER = "buffer"
    ACTIVATE = "activate"
    INTERRUPT = "interrupt"
