"""Stateless selection of a model resource by mandatory capabilities."""

from noema.model_router.domain.errors import (
    AmbiguousModelSelectionError,
    InvalidModelSelectionRequestError,
    NoEligibleModelResourceError,
)
from noema.model_router.domain.model_selection_decision import ModelSelectionDecision
from noema.model_router.domain.model_selection_request import ModelSelectionRequest


class ModelSelector:
    """Select the single candidate whose declared capabilities are sufficient.

    A candidate is eligible when its declared capabilities are a superset
    of the request's required capabilities — extra declared capabilities
    never disqualify a candidate, and none is preferred over another for
    having more or fewer of them. Eligibility is resolved for every
    candidate before any decision is made, so no candidate is ever chosen
    by iteration order, identity, or any other tie-breaking rule: zero
    eligible candidates and two or more eligible candidates are both
    explicit failures.
    """

    __slots__ = ()

    def select(self, request: ModelSelectionRequest) -> ModelSelectionDecision:
        """Return the sole eligible candidate's resource, or raise explicitly."""
        if not isinstance(request, ModelSelectionRequest):
            raise InvalidModelSelectionRequestError("request must be a ModelSelectionRequest")

        required_capabilities = request.requirements.required_capabilities
        eligible_resources = tuple(
            candidate.resource
            for candidate in request.candidates
            if required_capabilities.issubset(candidate.capabilities)
        )

        if not eligible_resources:
            raise NoEligibleModelResourceError("no candidate satisfies required capabilities")
        if len(eligible_resources) > 1:
            raise AmbiguousModelSelectionError("multiple candidates satisfy required capabilities")

        return ModelSelectionDecision(selected_resource=eligible_resources[0])
