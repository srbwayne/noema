from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.cognition.domain.errors import InvalidInformationNeedError
from noema.cognition.domain.reasoning import InformationNeed


def test_information_need_has_exact_required_fields() -> None:
    contract_fields = fields(InformationNeed)
    assert tuple(field.name for field in contract_fields) == ("subject_ref", "description")
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_information_need_accepts_valid_values_without_normalizing() -> None:
    need = InformationNeed(subject_ref=" subject:123 ", description=" Need fact A ")
    assert need.subject_ref == " subject:123 "
    assert need.description == " Need fact A "


@pytest.mark.parametrize("field_name", ["subject_ref", "description"])
@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_information_need_rejects_invalid_strings(field_name: str, value: object) -> None:
    values: dict[str, object] = {"subject_ref": "subject:123", "description": "Need fact"}
    values[field_name] = value
    with pytest.raises(InvalidInformationNeedError, match=field_name):
        InformationNeed(**values)


def test_information_need_is_frozen_slotted_keyword_only_and_structurally_equal() -> None:
    first = InformationNeed(subject_ref="subject:123", description="Need fact")
    second = InformationNeed(subject_ref="subject:123", description="Need fact")
    assert first == second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.description = "Changed"
    with pytest.raises(TypeError):
        InformationNeed("subject:123", "Need fact")
