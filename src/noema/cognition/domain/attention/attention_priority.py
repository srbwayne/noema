"""Hard priority classes for attention decisions."""

from enum import Enum


class AttentionPriority(Enum):
    """Semantic priority evaluated before the soft attention score."""

    P0_CRITICAL = "p0_critical"
    P1_DIRECT = "p1_direct"
    P2_GOAL_RELEVANT = "p2_goal_relevant"
    P3_BACKGROUND = "p3_background"
    P4_NOISE = "p4_noise"
