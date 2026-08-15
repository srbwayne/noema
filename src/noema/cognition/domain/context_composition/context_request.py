"""Requirements for a future context composition operation."""

from dataclasses import dataclass
from datetime import timedelta

from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.errors import InvalidContextRequestError
from noema.cognition.domain.modes import CognitiveMode

from .context_sensitivity import ContextSensitivity
from .context_slice_type import ContextSliceType
from .context_trust_level import ContextTrustLevel
from .instruction_authority import InstructionAuthority


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextRequest:
    """Declare the bounded context required by a cognitive consumer."""

    role: str
    task_ref: str
    goal_ref: str | None
    mode: CognitiveMode
    required_slice_types: tuple[ContextSliceType, ...]
    forbidden_slice_types: tuple[ContextSliceType, ...]
    max_sensitivity: ContextSensitivity
    minimum_trust: ContextTrustLevel
    allowed_authorities: tuple[InstructionAuthority, ...]
    max_age: timedelta | None
    max_tokens: int
    context_stamp: ContextStamp

    def __post_init__(self) -> None:
        """Validate request types and invariants without coercion."""
        self._validate_non_empty_string("role", self.role)
        self._validate_non_empty_string("task_ref", self.task_ref)
        if self.goal_ref is not None:
            self._validate_non_empty_string("goal_ref", self.goal_ref)
        if not isinstance(self.mode, CognitiveMode):
            raise InvalidContextRequestError("mode must be a CognitiveMode")

        self._validate_unique_enum_tuple(
            "required_slice_types", self.required_slice_types, ContextSliceType
        )
        self._validate_unique_enum_tuple(
            "forbidden_slice_types", self.forbidden_slice_types, ContextSliceType
        )
        if set(self.required_slice_types) & set(self.forbidden_slice_types):
            raise InvalidContextRequestError(
                "required_slice_types and forbidden_slice_types must be disjoint"
            )

        if not isinstance(self.max_sensitivity, ContextSensitivity):
            raise InvalidContextRequestError("max_sensitivity must be a ContextSensitivity")
        if not isinstance(self.minimum_trust, ContextTrustLevel):
            raise InvalidContextRequestError("minimum_trust must be a ContextTrustLevel")
        self._validate_unique_enum_tuple(
            "allowed_authorities", self.allowed_authorities, InstructionAuthority
        )

        if self.max_age is not None and (
            not isinstance(self.max_age, timedelta) or self.max_age <= timedelta(0)
        ):
            raise InvalidContextRequestError("max_age must be None or a positive timedelta")
        if (
            isinstance(self.max_tokens, bool)
            or not isinstance(self.max_tokens, int)
            or self.max_tokens <= 0
        ):
            raise InvalidContextRequestError("max_tokens must be a positive int")
        if not isinstance(self.context_stamp, ContextStamp):
            raise InvalidContextRequestError("context_stamp must be a ContextStamp")

    @staticmethod
    def _validate_non_empty_string(name: str, value: object) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidContextRequestError(f"{name} must be a non-empty string")

    @staticmethod
    def _validate_unique_enum_tuple(
        name: str,
        values: object,
        expected_type: type[ContextSliceType] | type[InstructionAuthority],
    ) -> None:
        if not isinstance(values, tuple):
            raise InvalidContextRequestError(f"{name} must be a tuple")
        if any(not isinstance(value, expected_type) for value in values):
            raise InvalidContextRequestError(
                f"{name} must contain only {expected_type.__name__} values"
            )
        if len(values) != len(set(values)):
            raise InvalidContextRequestError(f"{name} must not contain duplicates")
