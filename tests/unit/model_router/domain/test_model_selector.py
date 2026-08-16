import pytest

from noema.model_router.domain import (
    AmbiguousModelSelectionError,
    InvalidModelSelectionRequestError,
    ModelCapability,
    ModelCapabilityRequirements,
    ModelResource,
    ModelResourceCapabilities,
    ModelSelectionDecision,
    ModelSelectionRequest,
    ModelSelector,
    NoEligibleModelResourceError,
)


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


def candidate(
    *, capabilities: frozenset[ModelCapability], **resource_changes: object
) -> ModelResourceCapabilities:
    return ModelResourceCapabilities(
        resource=resource(**resource_changes), capabilities=capabilities
    )


def requirements(*, required: frozenset[ModelCapability]) -> ModelCapabilityRequirements:
    return ModelCapabilityRequirements(required_capabilities=required)


def request(
    *, required: frozenset[ModelCapability], candidates: frozenset[ModelResourceCapabilities]
) -> ModelSelectionRequest:
    return ModelSelectionRequest(
        requirements=requirements(required=required), candidates=candidates
    )


def test_model_selector_is_stateless() -> None:
    selector = ModelSelector()
    assert selector.__slots__ == ()
    assert not hasattr(selector, "__dict__")


def test_model_selector_public_surface_is_only_select() -> None:
    forbidden = {
        "match",
        "matches",
        "eligible",
        "filter",
        "rank",
        "route",
        "choose",
        "best",
        "supports",
        "supports_all",
        "supports_any",
    }
    public_members = {name for name in vars(ModelSelector) if not name.startswith("_")}
    assert public_members == {"select"}
    assert public_members.isdisjoint(forbidden)


@pytest.mark.parametrize(
    "invalid_request",
    [
        None,
        {},
        object(),
    ],
)
def test_model_selector_rejects_non_selection_request(invalid_request: object) -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="ModelSelectionRequest"):
        ModelSelector().select(invalid_request)  # type: ignore[arg-type]


def test_model_selector_rejects_model_capability_requirements() -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="ModelSelectionRequest"):
        ModelSelector().select(requirements(required=frozenset()))  # type: ignore[arg-type]


def test_model_selector_rejects_model_resource() -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="ModelSelectionRequest"):
        ModelSelector().select(resource())  # type: ignore[arg-type]


def test_model_selector_rejects_model_resource_capabilities() -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="ModelSelectionRequest"):
        ModelSelector().select(candidate(capabilities=frozenset({ModelCapability.TEXT_GENERATION})))  # type: ignore[arg-type]


def test_model_selector_rejects_model_selection_decision() -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="ModelSelectionRequest"):
        ModelSelector().select(ModelSelectionDecision(selected_resource=resource()))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "required",
    [frozenset(), frozenset({ModelCapability.TEXT_GENERATION})],
)
def test_model_selector_raises_no_eligible_for_empty_candidates(
    required: frozenset[ModelCapability],
) -> None:
    the_request = request(required=required, candidates=frozenset())
    with pytest.raises(NoEligibleModelResourceError, match="no candidate"):
        ModelSelector().select(the_request)


def test_model_selector_selects_single_exact_match() -> None:
    only_candidate = candidate(capabilities=frozenset({ModelCapability.TEXT_GENERATION}))
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({only_candidate}),
    )

    decision = ModelSelector().select(the_request)

    assert decision.selected_resource is only_candidate.resource


def test_model_selector_selects_single_superset_match() -> None:
    only_candidate = candidate(
        capabilities=frozenset(
            {
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STRUCTURED_OUTPUT,
                ModelCapability.TOOL_CALLING,
            }
        )
    )
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({only_candidate}),
    )

    decision = ModelSelector().select(the_request)

    assert decision.selected_resource is only_candidate.resource


def test_model_selector_raises_no_eligible_for_missing_required_capability() -> None:
    only_candidate = candidate(capabilities=frozenset({ModelCapability.TEXT_GENERATION}))
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING}),
        candidates=frozenset({only_candidate}),
    )

    with pytest.raises(NoEligibleModelResourceError):
        ModelSelector().select(the_request)


def test_model_selector_selects_the_one_eligible_among_many() -> None:
    eligible = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING}),
        resource_ref="resource:eligible",
    )
    ineligible_a = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        resource_ref="resource:ineligible-a",
    )
    ineligible_b = candidate(
        capabilities=frozenset({ModelCapability.STRUCTURED_OUTPUT}),
        resource_ref="resource:ineligible-b",
    )
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING}),
        candidates=frozenset({eligible, ineligible_a, ineligible_b}),
    )

    decision = ModelSelector().select(the_request)

    assert decision.selected_resource is eligible.resource


def test_model_selector_raises_ambiguous_for_two_eligible_candidates() -> None:
    candidate_a = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        resource_ref="resource:a",
    )
    candidate_b = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        resource_ref="resource:b",
    )
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({candidate_a, candidate_b}),
    )

    with pytest.raises(AmbiguousModelSelectionError, match="multiple candidates"):
        ModelSelector().select(the_request)


def test_model_selector_treats_exact_and_superset_as_equally_ambiguous() -> None:
    exact_match = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        resource_ref="resource:exact",
    )
    superset_match = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING}),
        resource_ref="resource:superset",
    )
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({exact_match, superset_match}),
    )

    with pytest.raises(AmbiguousModelSelectionError):
        ModelSelector().select(the_request)


def test_model_selector_empty_requirements_with_zero_candidates_is_no_eligible() -> None:
    the_request = request(required=frozenset(), candidates=frozenset())
    with pytest.raises(NoEligibleModelResourceError):
        ModelSelector().select(the_request)


def test_model_selector_empty_requirements_with_one_candidate_selects_it() -> None:
    only_candidate = candidate(capabilities=frozenset())
    the_request = request(required=frozenset(), candidates=frozenset({only_candidate}))

    decision = ModelSelector().select(the_request)

    assert decision.selected_resource is only_candidate.resource


def test_model_selector_empty_requirements_with_two_candidates_is_ambiguous() -> None:
    candidate_a = candidate(capabilities=frozenset(), resource_ref="resource:a")
    candidate_b = candidate(capabilities=frozenset(), resource_ref="resource:b")
    the_request = request(required=frozenset(), candidates=frozenset({candidate_a, candidate_b}))

    with pytest.raises(AmbiguousModelSelectionError):
        ModelSelector().select(the_request)


def test_model_selector_empty_candidate_capabilities_ineligible_for_any_requirement() -> None:
    only_candidate = candidate(capabilities=frozenset())
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({only_candidate}),
    )

    with pytest.raises(NoEligibleModelResourceError):
        ModelSelector().select(the_request)


def test_model_selector_result_is_order_independent_for_single_eligible() -> None:
    eligible = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        resource_ref="resource:eligible",
    )
    ineligible = candidate(
        capabilities=frozenset({ModelCapability.STRUCTURED_OUTPUT}),
        resource_ref="resource:ineligible",
    )
    required = frozenset({ModelCapability.TEXT_GENERATION})

    first = ModelSelector().select(
        request(required=required, candidates=frozenset((eligible, ineligible)))
    )
    second = ModelSelector().select(
        request(required=required, candidates=frozenset((ineligible, eligible)))
    )

    assert first == second
    assert first.selected_resource is eligible.resource


def test_model_selector_ambiguity_is_order_independent() -> None:
    candidate_a = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}), resource_ref="resource:a"
    )
    candidate_b = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}), resource_ref="resource:b"
    )
    required = frozenset({ModelCapability.TEXT_GENERATION})

    with pytest.raises(AmbiguousModelSelectionError):
        ModelSelector().select(
            request(required=required, candidates=frozenset((candidate_a, candidate_b)))
        )
    with pytest.raises(AmbiguousModelSelectionError):
        ModelSelector().select(
            request(required=required, candidates=frozenset((candidate_b, candidate_a)))
        )


def test_model_selector_does_not_tie_break_by_resource_identity() -> None:
    candidate_a = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        resource_ref="resource:zzz-last",
        provider_ref="provider:zzz-last",
        model_ref="model:zzz-last",
    )
    candidate_b = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        resource_ref="resource:aaa-first",
        provider_ref="provider:aaa-first",
        model_ref="model:aaa-first",
    )
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({candidate_a, candidate_b}),
    )

    with pytest.raises(AmbiguousModelSelectionError):
        ModelSelector().select(the_request)


def test_model_selector_does_not_deduplicate_by_same_resource() -> None:
    shared_resource = resource()
    profile_a = ModelResourceCapabilities(
        resource=shared_resource,
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
    )
    profile_b = ModelResourceCapabilities(
        resource=shared_resource,
        capabilities=frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING}),
    )
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({profile_a, profile_b}),
    )

    with pytest.raises(AmbiguousModelSelectionError):
        ModelSelector().select(the_request)


def test_model_selector_is_reusable_and_stateless_across_calls() -> None:
    selector = ModelSelector()
    only_candidate = candidate(capabilities=frozenset({ModelCapability.TEXT_GENERATION}))
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({only_candidate}),
    )

    first_decision = selector.select(the_request)

    other_candidate = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING}),
        resource_ref="resource:other",
    )
    other_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING}),
        candidates=frozenset({other_candidate}),
    )
    second_decision = selector.select(other_request)

    third_decision = selector.select(the_request)

    assert first_decision.selected_resource is only_candidate.resource
    assert second_decision.selected_resource is other_candidate.resource
    assert third_decision == first_decision


def test_model_selector_is_deterministic_for_repeated_calls() -> None:
    selector = ModelSelector()
    only_candidate = candidate(capabilities=frozenset({ModelCapability.TEXT_GENERATION}))
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({only_candidate}),
    )

    assert selector.select(the_request) == selector.select(the_request)


def test_no_eligible_model_resource_error_inherits_directly_from_domain_error() -> None:
    from noema.shared.domain import DomainError

    assert NoEligibleModelResourceError.__bases__ == (DomainError,)


def test_ambiguous_model_selection_error_inherits_directly_from_domain_error() -> None:
    from noema.shared.domain import DomainError

    assert AmbiguousModelSelectionError.__bases__ == (DomainError,)


def test_existing_error_hierarchy_preserved() -> None:
    from noema.model_router.domain import (
        InvalidModelSelectionDecisionError,
        InvalidModelSelectionRequestError,
    )
    from noema.shared.domain import DomainError

    assert InvalidModelSelectionRequestError.__bases__ == (DomainError,)
    assert InvalidModelSelectionDecisionError.__bases__ == (DomainError,)


def test_existing_model_router_contracts_remain_intact() -> None:
    from dataclasses import fields

    assert tuple(field.name for field in fields(ModelResource)) == (
        "resource_ref",
        "provider_ref",
        "model_ref",
    )
    assert tuple(field.name for field in fields(ModelResourceCapabilities)) == (
        "resource",
        "capabilities",
    )
    assert tuple(field.name for field in fields(ModelCapabilityRequirements)) == (
        "required_capabilities",
    )
    assert tuple(field.name for field in fields(ModelSelectionRequest)) == (
        "requirements",
        "candidates",
    )
    assert tuple(field.name for field in fields(ModelSelectionDecision)) == ("selected_resource",)
    assert {member.name for member in ModelCapability} == {
        "TEXT_GENERATION",
        "STRUCTURED_OUTPUT",
        "TOOL_CALLING",
    }
