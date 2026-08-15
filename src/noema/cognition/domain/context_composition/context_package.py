"""An immutable context projection for a cognitive operation."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidContextPackageError

from .context_request import ContextRequest
from .context_slice import ContextSlice


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextPackage:
    """Contain context slices selected for one explicit request."""

    request: ContextRequest
    slices: tuple[ContextSlice, ...]

    def __post_init__(self) -> None:
        """Validate package invariants directly observable from request and slices."""
        if not isinstance(self.request, ContextRequest):
            raise InvalidContextPackageError("request must be a ContextRequest")
        if not isinstance(self.slices, tuple):
            raise InvalidContextPackageError("slices must be a tuple")
        if any(not isinstance(context_slice, ContextSlice) for context_slice in self.slices):
            raise InvalidContextPackageError("slices must contain only ContextSlice values")
        if len(self.slices) != len(set(self.slices)):
            raise InvalidContextPackageError("slices must not contain structural duplicates")

        included_types = {context_slice.slice_type for context_slice in self.slices}
        missing_types = set(self.request.required_slice_types) - included_types
        if missing_types:
            raise InvalidContextPackageError("slices must cover every required slice type")
        if included_types & set(self.request.forbidden_slice_types):
            raise InvalidContextPackageError("slices must not contain forbidden slice types")

        unauthorized_authority = any(
            context_slice.instruction_authority is not None
            and context_slice.instruction_authority not in self.request.allowed_authorities
            for context_slice in self.slices
        )
        if unauthorized_authority:
            raise InvalidContextPackageError(
                "instruction authorities must be allowed by the request"
            )
        if self.total_token_estimate > self.request.max_tokens:
            raise InvalidContextPackageError("total token estimate exceeds request max_tokens")

    @property
    def total_token_estimate(self) -> int:
        """Return the token estimate derived from the contained slices."""
        return sum(context_slice.token_estimate for context_slice in self.slices)
