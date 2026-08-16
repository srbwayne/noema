"""Domain contracts for the model_router bounded context."""

from noema.model_router.domain.errors import InvalidModelResourceError
from noema.model_router.domain.model_resource import ModelResource

__all__ = [
    "InvalidModelResourceError",
    "ModelResource",
]
