"""Explicit cognitive strategies available to future reasoning execution."""

from enum import Enum


class ReasoningStrategy(Enum):
    """Identify the strategy explicitly requested for reasoning."""

    DIRECT = "direct"
    DECOMPOSITION = "decomposition"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    SEARCH = "search"
    COUNTERFACTUAL = "counterfactual"
    CRITIQUE = "critique"
    TOOL_ASSISTED = "tool_assisted"
    MULTI_MODEL = "multi_model"
