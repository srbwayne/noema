"""The identity of a configured, substitutable model resource."""

from dataclasses import dataclass

from noema.model_router.domain.errors import InvalidModelResourceError

_REF_FIELDS = ("resource_ref", "provider_ref", "model_ref")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelResource:
    """Identify a model resource by opaque, uninterpreted references.

    ``resource_ref``, ``provider_ref``, and ``model_ref`` are opaque
    identifiers: no format, prefix, or naming convention is imposed or
    inferred. This is a runtime resource identity, not the agent's
    identity, cognition, or memory — Agent != LLM.
    """

    resource_ref: str
    provider_ref: str
    model_ref: str

    def __post_init__(self) -> None:
        """Require non-empty strings without coercion or normalization."""
        for field_name in _REF_FIELDS:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidModelResourceError(f"{field_name} must be a non-empty string")
