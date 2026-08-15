"""Sensitivity classifications for context slices."""

from enum import Enum


class ContextSensitivity(Enum):
    """Classify how restricted contextual information is."""

    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    SECRET = "secret"
