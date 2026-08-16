"""A bounded request for a future model selection operation."""

from dataclasses import dataclass

from noema.model_router.domain.errors import InvalidModelSelectionRequestError
from noema.model_router.domain.model_capability_requirements import (
    ModelCapabilityRequirements,
)
from noema.model_router.domain.model_resource_capabilities import (
    ModelResourceCapabilities,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelSelectionRequest:
    """Bind mandatory requirements to the candidates offered to a selection.

    ``candidates`` is the explicit set of ``ModelResourceCapabilities``
    supplied to this request — not a registry, a discovery result, or a
    global resource pool. An empty ``candidates`` frozenset is valid:
    Noema remains semantically valid even when no model resource is
    currently active. This request does not decide a selection outcome.
    """

    requirements: ModelCapabilityRequirements
    candidates: frozenset[ModelResourceCapabilities]

    def __post_init__(self) -> None:
        """Require a ModelCapabilityRequirements and a strict candidates frozenset."""
        if not isinstance(self.requirements, ModelCapabilityRequirements):
            raise InvalidModelSelectionRequestError(
                "requirements must be a ModelCapabilityRequirements"
            )
        if type(self.candidates) is not frozenset:
            raise InvalidModelSelectionRequestError("candidates must be a frozenset")
        for candidate in self.candidates:
            if not isinstance(candidate, ModelResourceCapabilities):
                raise InvalidModelSelectionRequestError(
                    "candidates must contain only ModelResourceCapabilities values"
                )
