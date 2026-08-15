"""A declarative description of information missing from reasoning."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidInformationNeedError


@dataclass(frozen=True, slots=True, kw_only=True)
class InformationNeed:
    """Describe missing information without prescribing how to obtain it."""

    subject_ref: str
    description: str

    def __post_init__(self) -> None:
        """Validate opaque references and descriptions without normalization."""
        if not isinstance(self.subject_ref, str) or not self.subject_ref.strip():
            raise InvalidInformationNeedError("subject_ref must be a non-empty string")
        if not isinstance(self.description, str) or not self.description.strip():
            raise InvalidInformationNeedError("description must be a non-empty string")
