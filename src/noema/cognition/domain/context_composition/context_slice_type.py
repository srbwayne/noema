"""Semantic types of context slices."""

from enum import Enum


class ContextSliceType(Enum):
    """Classify the cognitive information represented by a slice."""

    IDENTITY = "identity"
    GOAL = "goal"
    TASK = "task"
    SITUATION = "situation"
    MEMORY = "memory"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    HYPOTHESIS = "hypothesis"
    PLAN = "plan"
    POLICY = "policy"
    CONSTRAINT = "constraint"
    EMOTION = "emotion"
    SELF_MODEL = "self_model"
    CAPABILITY = "capability"
    TOOL = "tool"
    HISTORY = "history"
    ENVIRONMENT = "environment"
