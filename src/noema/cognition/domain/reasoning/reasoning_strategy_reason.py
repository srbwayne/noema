"""Structured reasons for selecting one reasoning strategy."""

from enum import Enum


class ReasoningStrategyReason(Enum):
    """Explain why a single cognitive strategy was selected."""

    DIRECT_SUFFICIENT = "direct_sufficient"
    DECOMPOSITION_REQUIRED = "decomposition_required"
    HYPOTHESIS_TESTING_REQUIRED = "hypothesis_testing_required"
    CAUSAL_REASONING_REQUIRED = "causal_reasoning_required"
    COMPARISON_REQUIRED = "comparison_required"
    SEARCH_REQUIRED = "search_required"
    COUNTERFACTUAL_REQUIRED = "counterfactual_required"
    CRITIQUE_REQUIRED = "critique_required"
    TOOL_ASSISTANCE_REQUIRED = "tool_assistance_required"
    MULTI_MODEL_REQUIRED = "multi_model_required"
