"""The obligatory capability requirements for a future model selection."""

from dataclasses import dataclass

from noema.model_router.domain.errors import InvalidModelCapabilityRequirementsError
from noema.model_router.domain.model_capability import ModelCapability


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelCapabilityRequirements:
    """Represent the capabilities a future selection must treat as mandatory.

    This is independent of any concrete candidate resource: it does not
    reference a ``ModelResource`` and does not represent preference,
    ranking, weight, quality, priority, or fallback. An empty
    ``required_capabilities`` frozenset is valid and means no mandatory
    capability restriction has been declared.
    """

    required_capabilities: frozenset[ModelCapability]

    def __post_init__(self) -> None:
        """Require a strict frozenset of ModelCapability values."""
        if type(self.required_capabilities) is not frozenset:
            raise InvalidModelCapabilityRequirementsError(
                "required_capabilities must be a frozenset"
            )
        for capability in self.required_capabilities:
            if not isinstance(capability, ModelCapability):
                raise InvalidModelCapabilityRequirementsError(
                    "required_capabilities must contain only ModelCapability values"
                )
