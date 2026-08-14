"""Semantic kinds of information active in cognition."""

from enum import Enum


class CognitiveItemKind(Enum):
    """Kind of information referenced by a cognitive item."""

    OBSERVATION = "observation"
    GOAL = "goal"
    TASK = "task"
    MEMORY = "memory"
    CLAIM = "claim"
    HYPOTHESIS = "hypothesis"
    EVIDENCE = "evidence"
    CONSTRAINT = "constraint"
    PLAN = "plan"
    QUESTION = "question"
    CONTEXT = "context"
