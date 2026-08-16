"""A provider-neutral request to execute an already-selected model resource."""

from dataclasses import dataclass

from noema.model_router.domain import ModelResource


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelExecutionRequest:
    """Bind an already-selected resource to the text it must execute.

    This is a minimal, provider-neutral execution call: it carries no
    prompt policy — no system prompt, message roles, chat history, or
    template — only the plain text to execute against the given resource.
    """

    resource: ModelResource
    input_text: str

    def __post_init__(self) -> None:
        """Require a ModelResource and a non-empty input_text, unnormalized."""
        if not isinstance(self.resource, ModelResource):
            raise TypeError("resource must be a ModelResource")
        if not isinstance(self.input_text, str):
            raise TypeError("input_text must be a string")
        if not self.input_text.strip():
            raise ValueError("input_text must be a non-empty string")
