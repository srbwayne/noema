"""Domain contracts for the model_router bounded context."""

from noema.model_router.domain.errors import (
    InvalidModelResourceCapabilitiesError,
    InvalidModelResourceError,
)
from noema.model_router.domain.model_capability import ModelCapability
from noema.model_router.domain.model_resource import ModelResource
from noema.model_router.domain.model_resource_capabilities import (
    ModelResourceCapabilities,
)

__all__ = [
    "InvalidModelResourceCapabilitiesError",
    "InvalidModelResourceError",
    "ModelCapability",
    "ModelResource",
    "ModelResourceCapabilities",
]
