"""Private shared mapping from specialized demand fields to strategy decisions.

This module is the single source of truth for the association between a
``ReasoningStrategyDemand`` specialized requirement field, its
``ReasoningStrategy``, and its ``ReasoningStrategyReason``. Both
``ReasoningStrategySelector`` and ``ReasoningCoordinator`` resolve specialized
requirements through this module so the mapping cannot drift between them.

Not exported by the ``reasoning`` package.
"""

from .reasoning_strategy import ReasoningStrategy
from .reasoning_strategy_decision import ReasoningStrategyDecision
from .reasoning_strategy_demand import ReasoningStrategyDemand
from .reasoning_strategy_reason import ReasoningStrategyReason

_SPECIALIZED_REQUIREMENTS = (
    (
        "requires_decomposition",
        ReasoningStrategy.DECOMPOSITION,
        ReasoningStrategyReason.DECOMPOSITION_REQUIRED,
    ),
    (
        "requires_hypothesis_testing",
        ReasoningStrategy.HYPOTHESIS_TESTING,
        ReasoningStrategyReason.HYPOTHESIS_TESTING_REQUIRED,
    ),
    (
        "requires_causal_reasoning",
        ReasoningStrategy.CAUSAL,
        ReasoningStrategyReason.CAUSAL_REASONING_REQUIRED,
    ),
    (
        "requires_comparison",
        ReasoningStrategy.COMPARATIVE,
        ReasoningStrategyReason.COMPARISON_REQUIRED,
    ),
    ("requires_search", ReasoningStrategy.SEARCH, ReasoningStrategyReason.SEARCH_REQUIRED),
    (
        "requires_counterfactual",
        ReasoningStrategy.COUNTERFACTUAL,
        ReasoningStrategyReason.COUNTERFACTUAL_REQUIRED,
    ),
    ("requires_critique", ReasoningStrategy.CRITIQUE, ReasoningStrategyReason.CRITIQUE_REQUIRED),
    (
        "requires_tool_assistance",
        ReasoningStrategy.TOOL_ASSISTED,
        ReasoningStrategyReason.TOOL_ASSISTANCE_REQUIRED,
    ),
    (
        "requires_multi_model",
        ReasoningStrategy.MULTI_MODEL,
        ReasoningStrategyReason.MULTI_MODEL_REQUIRED,
    ),
)


def specialized_strategy_decisions(
    demand: ReasoningStrategyDemand,
) -> tuple[ReasoningStrategyDecision, ...]:
    """Return a Decision for every active specialized requirement in demand.

    The returned tuple's order is an internal, deterministic processing
    detail only. It carries no precedence, priority, or execution-order
    meaning; callers that expose a public multi-strategy result must convert
    it to a frozenset.
    """
    return tuple(
        ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)
        for field_name, strategy, reason in _SPECIALIZED_REQUIREMENTS
        if getattr(demand, field_name)
    )
