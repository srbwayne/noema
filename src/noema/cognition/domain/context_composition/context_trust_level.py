"""Operational trust classifications for context slices."""

from enum import Enum


class ContextTrustLevel(Enum):
    """Classify operational trust in a slice's origin."""

    TRUSTED = "trusted"
    UNVERIFIED = "unverified"
    UNTRUSTED = "untrusted"
