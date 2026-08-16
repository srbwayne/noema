"""The identity of the model resource chosen by a successful selection."""

from dataclasses import dataclass

from noema.model_router.domain.errors import InvalidModelSelectionDecisionError
from noema.model_router.domain.model_resource import ModelResource


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelSelectionDecision:
    """Represent the resource chosen by a successful model selection.

    This is a success-only contract: it exists only when a resource has
    been selected. It carries only the selected resource's identity — not
    the request that produced it, not the candidate's declared
    capabilities, and not any status, reason, or ranking metadata.
    """

    selected_resource: ModelResource

    def __post_init__(self) -> None:
        """Require a ModelResource as the selected resource."""
        if not isinstance(self.selected_resource, ModelResource):
            raise InvalidModelSelectionDecisionError("selected_resource must be a ModelResource")
