"""Errors raised by model_router domain rules."""

from noema.model_router.domain.errors.model_capability_errors import (
    InvalidModelResourceCapabilitiesError,
)
from noema.model_router.domain.errors.model_capability_requirement_errors import (
    InvalidModelCapabilityRequirementsError,
)
from noema.model_router.domain.errors.model_resource_errors import (
    InvalidModelResourceError,
)
from noema.model_router.domain.errors.model_selection_errors import (
    InvalidModelSelectionDecisionError,
    InvalidModelSelectionRequestError,
)

__all__ = [
    "InvalidModelCapabilityRequirementsError",
    "InvalidModelResourceCapabilitiesError",
    "InvalidModelResourceError",
    "InvalidModelSelectionDecisionError",
    "InvalidModelSelectionRequestError",
]
