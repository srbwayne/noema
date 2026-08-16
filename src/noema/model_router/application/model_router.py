"""The application boundary that routes one model selection request."""

from noema.model_router.domain import ModelSelectionDecision, ModelSelectionRequest, ModelSelector


class ModelRouter:
    """Route a model selection request to its injected selector.

    The router has exactly one dependency: a ``ModelSelector``. All
    eligibility semantics — required-capability subset matching, zero
    eligible candidates, exactly one eligible candidate, multiple eligible
    candidates — remain exclusively the selector's responsibility. This
    boundary only delegates the request once and returns the selector's
    decision unchanged.
    """

    __slots__ = ("_selector",)

    def __init__(
        self,
        *,
        selector: ModelSelector,
    ) -> None:
        """Inject the model selector this router delegates to."""
        if not isinstance(selector, ModelSelector):
            raise TypeError("selector must be a ModelSelector")
        self._selector = selector

    def route(
        self,
        request: ModelSelectionRequest,
    ) -> ModelSelectionDecision:
        """Delegate request to the selector exactly once and return its decision."""
        return self._selector.select(request)
