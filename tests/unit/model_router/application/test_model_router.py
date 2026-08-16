import pytest

from noema.model_router.application import ModelRouter
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


class SpyModelSelector(ModelSelector):
    """A ModelSelector subclass recording calls and returning a fixed result."""

    def __init__(self, result: object) -> None:
        self._result = result
        self.received_requests: list[ModelSelectionRequest] = []
        self.call_count = 0

    def select(self, request: ModelSelectionRequest) -> ModelSelectionDecision:
        self.received_requests.append(request)
        self.call_count += 1
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result  # type: ignore[return-value]


def test_model_router_has_exact_slots() -> None:
    assert ModelRouter.__slots__ == ("_selector",)


def test_model_router_instances_have_no_dict() -> None:
    decision = ModelSelectionDecision(selected_resource=resource())
    router = ModelRouter(selector=SpyModelSelector(decision))
    assert not hasattr(router, "__dict__")


def test_model_router_constructor_is_keyword_only() -> None:
    selector = ModelSelector()
    with pytest.raises(TypeError):
        ModelRouter(selector)  # type: ignore[misc]
    ModelRouter(selector=selector)


@pytest.mark.parametrize(
    "invalid_selector",
    [None, object(), {}],
)
def test_model_router_rejects_non_model_selector(invalid_selector: object) -> None:
    with pytest.raises(TypeError, match="selector must be a ModelSelector"):
        ModelRouter(selector=invalid_selector)  # type: ignore[arg-type]


def test_model_router_rejects_model_selection_request_as_selector() -> None:
    with pytest.raises(TypeError, match="selector must be a ModelSelector"):
        ModelRouter(
            selector=request(  # type: ignore[arg-type]
                required=frozenset(), candidates=frozenset()
            )
        )


def test_model_router_rejects_model_selection_decision_as_selector() -> None:
    with pytest.raises(TypeError, match="selector must be a ModelSelector"):
        ModelRouter(selector=ModelSelectionDecision(selected_resource=resource()))  # type: ignore[arg-type]


def test_model_router_public_surface_is_only_route() -> None:
    forbidden = {
        "select",
        "match",
        "matches",
        "filter",
        "eligible",
        "rank",
        "choose",
        "best",
        "resolve",
        "dispatch",
        "execute",
        "invoke",
        "complete",
        "generate",
    }
    public_members = {name for name in vars(ModelRouter) if not name.startswith("_")}
    assert public_members == {"route"}
    assert public_members.isdisjoint(forbidden)


def test_model_router_does_not_call_selector_during_construction() -> None:
    spy = SpyModelSelector(ModelSelectionDecision(selected_resource=resource()))
    ModelRouter(selector=spy)
    assert spy.call_count == 0


def test_model_router_calls_selector_exactly_once() -> None:
    decision = ModelSelectionDecision(selected_resource=resource())
    spy = SpyModelSelector(decision)
    router = ModelRouter(selector=spy)
    the_request = request(required=frozenset(), candidates=frozenset())

    router.route(the_request)

    assert spy.call_count == 1


def test_model_router_passes_the_exact_request_object() -> None:
    decision = ModelSelectionDecision(selected_resource=resource())
    spy = SpyModelSelector(decision)
    router = ModelRouter(selector=spy)
    the_request = request(required=frozenset(), candidates=frozenset())

    router.route(the_request)

    assert len(spy.received_requests) == 1
    assert spy.received_requests[0] is the_request


def test_model_router_returns_the_exact_decision_object() -> None:
    decision = ModelSelectionDecision(selected_resource=resource())
    spy = SpyModelSelector(decision)
    router = ModelRouter(selector=spy)
    the_request = request(required=frozenset(), candidates=frozenset())

    result = router.route(the_request)

    assert result is decision


def test_model_router_with_real_selector_and_single_eligible_candidate() -> None:
    only_candidate = candidate(capabilities=frozenset({ModelCapability.TEXT_GENERATION}))
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({only_candidate}),
    )
    router = ModelRouter(selector=ModelSelector())

    decision = router.route(the_request)

    assert isinstance(decision, ModelSelectionDecision)
    assert decision.selected_resource is only_candidate.resource


@pytest.mark.parametrize("invalid_request", [None, {}, object()])
def test_model_router_propagates_invalid_request_error_with_real_selector(
    invalid_request: object,
) -> None:
    router = ModelRouter(selector=ModelSelector())
    with pytest.raises(InvalidModelSelectionRequestError):
        router.route(invalid_request)  # type: ignore[arg-type]


def test_model_router_propagates_no_eligible_error_with_real_selector() -> None:
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}), candidates=frozenset()
    )
    router = ModelRouter(selector=ModelSelector())

    with pytest.raises(NoEligibleModelResourceError):
        router.route(the_request)


def test_model_router_propagates_the_same_no_eligible_instance() -> None:
    expected_error = NoEligibleModelResourceError("sentinel")
    spy = SpyModelSelector(expected_error)
    router = ModelRouter(selector=spy)
    the_request = request(required=frozenset(), candidates=frozenset())

    with pytest.raises(NoEligibleModelResourceError) as raised:
        router.route(the_request)

    assert raised.value is expected_error


def test_model_router_propagates_ambiguous_error_with_real_selector() -> None:
    candidate_a = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}), resource_ref="resource:a"
    )
    candidate_b = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}), resource_ref="resource:b"
    )
    the_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({candidate_a, candidate_b}),
    )
    router = ModelRouter(selector=ModelSelector())

    with pytest.raises(AmbiguousModelSelectionError):
        router.route(the_request)


def test_model_router_propagates_the_same_ambiguous_instance() -> None:
    expected_error = AmbiguousModelSelectionError("sentinel")
    spy = SpyModelSelector(expected_error)
    router = ModelRouter(selector=spy)
    the_request = request(required=frozenset(), candidates=frozenset())

    with pytest.raises(AmbiguousModelSelectionError) as raised:
        router.route(the_request)

    assert raised.value is expected_error


def test_model_router_is_reusable_across_independent_requests() -> None:
    first_candidate = candidate(capabilities=frozenset({ModelCapability.TEXT_GENERATION}))
    first_request = request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({first_candidate}),
    )
    second_candidate = candidate(
        capabilities=frozenset({ModelCapability.TOOL_CALLING}), resource_ref="resource:second"
    )
    second_request = request(
        required=frozenset({ModelCapability.TOOL_CALLING}),
        candidates=frozenset({second_candidate}),
    )
    router = ModelRouter(selector=ModelSelector())

    first_decision = router.route(first_request)
    second_decision = router.route(second_request)

    assert first_decision.selected_resource is first_candidate.resource
    assert second_decision.selected_resource is second_candidate.resource


def test_model_router_does_not_cache_decisions() -> None:
    decision = ModelSelectionDecision(selected_resource=resource())
    spy = SpyModelSelector(decision)
    router = ModelRouter(selector=spy)
    the_request = request(required=frozenset(), candidates=frozenset())

    router.route(the_request)
    router.route(the_request)

    assert spy.call_count == 2


def test_model_router_application_exports_only_model_router() -> None:
    from noema.model_router import application

    assert application.__all__ == ["ModelRouter"]


def test_existing_model_router_domain_contracts_remain_intact() -> None:
    from dataclasses import fields

    assert tuple(field.name for field in fields(ModelResource)) == (
        "resource_ref",
        "provider_ref",
        "model_ref",
    )
    assert {member.name for member in ModelCapability} == {
        "TEXT_GENERATION",
        "STRUCTURED_OUTPUT",
        "TOOL_CALLING",
    }
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
    assert {name for name in vars(ModelSelector) if not name.startswith("_")} == {"select"}
