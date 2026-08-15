"""A projectable unit of cognitive context."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidContextSliceError

from .context_package_zone import ContextPackageZone
from .context_sensitivity import ContextSensitivity
from .context_slice_type import ContextSliceType
from .context_trust_level import ContextTrustLevel
from .instruction_authority import InstructionAuthority


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextSlice:
    """Describe a context reference and its composition classifications."""

    slice_type: ContextSliceType
    content_ref: str
    zone: ContextPackageZone
    sensitivity: ContextSensitivity
    trust: ContextTrustLevel
    instruction_authority: InstructionAuthority | None
    provenance_ref: str
    token_estimate: int

    def __post_init__(self) -> None:
        """Validate slice types and invariants without coercion."""
        enum_fields = (
            ("slice_type", self.slice_type, ContextSliceType),
            ("zone", self.zone, ContextPackageZone),
            ("sensitivity", self.sensitivity, ContextSensitivity),
            ("trust", self.trust, ContextTrustLevel),
        )
        for name, value, expected_type in enum_fields:
            if not isinstance(value, expected_type):
                raise InvalidContextSliceError(f"{name} must be a {expected_type.__name__}")

        self._validate_non_empty_string("content_ref", self.content_ref)
        if self.instruction_authority is not None and not isinstance(
            self.instruction_authority, InstructionAuthority
        ):
            raise InvalidContextSliceError(
                "instruction_authority must be None or an InstructionAuthority"
            )
        self._validate_non_empty_string("provenance_ref", self.provenance_ref)
        if (
            isinstance(self.token_estimate, bool)
            or not isinstance(self.token_estimate, int)
            or self.token_estimate < 0
        ):
            raise InvalidContextSliceError("token_estimate must be a non-negative int")

    @staticmethod
    def _validate_non_empty_string(name: str, value: object) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidContextSliceError(f"{name} must be a non-empty string")
