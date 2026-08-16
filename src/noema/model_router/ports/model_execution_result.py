"""The provider-neutral output of a successful model execution."""

from dataclasses import dataclass

from noema.model_router.domain import ModelResource


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelExecutionResult:
    """Represent the successful output of executing a model resource.

    This is a success-only contract: it exists only when execution
    produced a result. It carries no status, error, retry, or provider
    metadata, and no raw provider response — a concrete adapter must
    translate technical failures into ``ModelExecutionError`` instead of
    returning an invalid result.
    """

    resource: ModelResource
    output_text: str

    def __post_init__(self) -> None:
        """Require a ModelResource and a non-empty output_text, unnormalized."""
        if not isinstance(self.resource, ModelResource):
            raise TypeError("resource must be a ModelResource")
        if not isinstance(self.output_text, str):
            raise TypeError("output_text must be a string")
        if not self.output_text.strip():
            raise ValueError("output_text must be a non-empty string")
