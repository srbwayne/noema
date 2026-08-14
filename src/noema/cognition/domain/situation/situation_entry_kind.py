"""Kinds of information in the current believed situation."""

from enum import Enum


class SituationEntryKind(Enum):
    """Semantic category of a situation entry."""

    ACTOR = "actor"
    ENTITY = "entity"
    RESOURCE = "resource"
    ENVIRONMENT = "environment"
    GOAL = "goal"
    TASK = "task"
    EVENT = "event"
    CONSTRAINT = "constraint"
    RISK = "risk"
    OBSERVATION = "observation"
    UNKNOWN = "unknown"
    QUESTION = "question"
    CAUSAL_RELATION = "causal_relation"
