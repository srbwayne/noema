from dataclasses import FrozenInstanceError, fields, replace
from math import inf, nan

import pytest

from noema.cognition.domain.context_composition import ContextCompositionPolicy
from noema.cognition.domain.errors import InvalidContextCompositionPolicyError


def policy() -> ContextCompositionPolicy:
    return ContextCompositionPolicy(minimum_relevance=0.5, max_slices=10)


def test_context_composition_policy_has_exact_fields_without_defaults() -> None:
    policy_fields = fields(ContextCompositionPolicy)
    assert tuple(field.name for field in policy_fields) == ("minimum_relevance", "max_slices")
    assert all(field.default is field.default_factory for field in policy_fields)


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_context_composition_policy_accepts_normalized_minimum_relevance(value: float) -> None:
    assert replace(policy(), minimum_relevance=value).minimum_relevance == value


@pytest.mark.parametrize("value", [-0.01, 1.01, nan, inf, -inf, True, False, 0, 1, None])
def test_context_composition_policy_rejects_invalid_minimum_relevance(value: object) -> None:
    with pytest.raises(InvalidContextCompositionPolicyError, match="minimum_relevance"):
        replace(policy(), minimum_relevance=value)


@pytest.mark.parametrize("value", [1, 10, 100])
def test_context_composition_policy_accepts_positive_max_slices(value: int) -> None:
    assert replace(policy(), max_slices=value).max_slices == value


@pytest.mark.parametrize("value", [0, -1, True, False, 1.0, None])
def test_context_composition_policy_rejects_invalid_max_slices(value: object) -> None:
    with pytest.raises(InvalidContextCompositionPolicyError, match="max_slices"):
        replace(policy(), max_slices=value)


def test_context_composition_policy_is_immutable_and_structurally_equal() -> None:
    assert policy() == policy()
    with pytest.raises(FrozenInstanceError):
        policy().max_slices = 20
