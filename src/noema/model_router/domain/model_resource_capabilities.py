"""The declared capability set of a configured model resource."""

from dataclasses import dataclass

from noema.model_router.domain.errors import InvalidModelResourceCapabilitiesError
from noema.model_router.domain.model_capability import ModelCapability
from noema.model_router.domain.model_resource import ModelResource


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelResourceCapabilities:
    """Associate a model resource with the capabilities it declares.

    This represents declared capabilities only — not availability, health,
    performance, cost, privacy policy, or routing suitability. An empty
    ``capabilities`` frozenset is valid: existing as a ``ModelResource``
    does not imply any capability is declared.
    """

    resource: ModelResource
    capabilities: frozenset[ModelCapability]

    def __post_init__(self) -> None:
        """Require a ModelResource and a strict frozenset of capabilities."""
        if not isinstance(self.resource, ModelResource):
            raise InvalidModelResourceCapabilitiesError("resource must be a ModelResource")
        if type(self.capabilities) is not frozenset:
            raise InvalidModelResourceCapabilitiesError("capabilities must be a frozenset")
        for capability in self.capabilities:
            if not isinstance(capability, ModelCapability):
                raise InvalidModelResourceCapabilitiesError(
                    "capabilities must contain only ModelCapability values"
                )
