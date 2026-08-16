"""Domain contracts for the model_router bounded context."""

from noema.model_router.domain.errors import (
    InvalidModelCapabilityRequirementsError,
    InvalidModelResourceCapabilitiesError,
    InvalidModelResourceError,
    InvalidModelSelectionDecisionError,
    InvalidModelSelectionRequestError,
)
from noema.model_router.domain.model_capability import ModelCapability
from noema.model_router.domain.model_capability_requirements import (
    ModelCapabilityRequirements,
)
from noema.model_router.domain.model_resource import ModelResource
from noema.model_router.domain.model_resource_capabilities import (
    ModelResourceCapabilities,
)
from noema.model_router.domain.model_selection_decision import ModelSelectionDecision
from noema.model_router.domain.model_selection_request import ModelSelectionRequest

__all__ = [
    "InvalidModelCapabilityRequirementsError",
    "InvalidModelResourceCapabilitiesError",
    "InvalidModelResourceError",
    "InvalidModelSelectionDecisionError",
    "InvalidModelSelectionRequestError",
    "ModelCapability",
    "ModelCapabilityRequirements",
    "ModelResource",
    "ModelResourceCapabilities",
    "ModelSelectionDecision",
    "ModelSelectionRequest",
]
