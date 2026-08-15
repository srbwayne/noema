from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta

import pytest

from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextCandidate,
    ContextComposer,
    ContextCompositionPolicy,
    ContextPackageZone,
    ContextRequest,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.errors import (
    ContextCompositionUnsatisfiedError,
    InvalidContextComposerError,
)
from noema.cognition.domain.modes import CognitiveMode

ALL_AUTHORITIES = tuple(InstructionAuthority)


def request(**changes: object) -> ContextRequest:
    current = ContextRequest(
        role="reasoner",
        task_ref="task:operation",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(),
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.SECRET,
        minimum_trust=ContextTrustLevel.UNTRUSTED,
        allowed_authorities=ALL_AUTHORITIES,
        max_age=None,
        max_tokens=1000,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=2,
            identity_version=3,
            goal_version=4,
            policy_version=5,
        ),
    )
    return replace(current, **changes)


def context_slice(
    content_ref: str,
    *,
    slice_type: ContextSliceType = ContextSliceType.EVIDENCE,
    token_estimate: int = 10,
    sensitivity: ContextSensitivity = ContextSensitivity.PUBLIC,
    trust: ContextTrustLevel = ContextTrustLevel.TRUSTED,
    authority: InstructionAuthority | None = None,
) -> ContextSlice:
    return ContextSlice(
        slice_type=slice_type,
        content_ref=content_ref,
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=sensitivity,
        trust=trust,
        instruction_authority=authority,
        provenance_ref=f"source:{content_ref}",
        token_estimate=token_estimate,
    )


def candidate(
    content_ref: str,
    *,
    slice_type: ContextSliceType = ContextSliceType.EVIDENCE,
    relevance: float = 0.8,
    age: timedelta | None = timedelta(0),
    token_estimate: int = 10,
    sensitivity: ContextSensitivity = ContextSensitivity.PUBLIC,
    trust: ContextTrustLevel = ContextTrustLevel.TRUSTED,
    authority: InstructionAuthority | None = None,
) -> ContextCandidate:
    return ContextCandidate(
        context_slice=context_slice(
            content_ref,
            slice_type=slice_type,
            token_estimate=token_estimate,
            sensitivity=sensitivity,
            trust=trust,
            authority=authority,
        ),
        relevance=relevance,
        age=age,
    )


def policy(**changes: object) -> ContextCompositionPolicy:
    current = ContextCompositionPolicy(minimum_relevance=0.5, max_slices=10)
    return replace(current, **changes)


def composer(**policy_changes: object) -> ContextComposer:
    return ContextComposer(policy=policy(**policy_changes))


def compose_refs(
    candidates: tuple[ContextCandidate, ...],
    *,
    current_request: ContextRequest | None = None,
    current_composer: ContextComposer | None = None,
) -> tuple[str, ...]:
    package = (current_composer or composer()).compose(
        request=current_request or request(),
        candidates=candidates,
    )
    return tuple(context_slice.content_ref for context_slice in package.slices)


def required_choice(
    first: ContextCandidate,
    second: ContextCandidate,
) -> str:
    current_request = request(required_slice_types=(ContextSliceType.TASK,))
    return compose_refs((first, second), current_request=current_request)[0]


def test_context_composer_has_exact_policy_field_and_is_immutable() -> None:
    assert tuple(field.name for field in fields(ContextComposer)) == ("policy",)
    with pytest.raises(FrozenInstanceError):
        composer().policy = policy(max_slices=2)


@pytest.mark.parametrize("value", [None, {}, "policy"])
def test_context_composer_rejects_invalid_policy(value: object) -> None:
    with pytest.raises(InvalidContextComposerError, match="policy"):
        ContextComposer(policy=value)


@pytest.mark.parametrize("value", [None, {}, ()])
def test_context_composer_rejects_invalid_request(value: object) -> None:
    with pytest.raises(InvalidContextComposerError, match="request"):
        composer().compose(request=value, candidates=())


@pytest.mark.parametrize("value", [[], None, {}])
def test_context_composer_rejects_invalid_candidates_collection(value: object) -> None:
    with pytest.raises(InvalidContextComposerError, match="tuple"):
        composer().compose(request=request(), candidates=value)


@pytest.mark.parametrize("value", [context_slice("direct"), "candidate", None])
def test_context_composer_rejects_invalid_candidate_element(value: object) -> None:
    with pytest.raises(InvalidContextComposerError, match="ContextCandidate"):
        composer().compose(request=request(), candidates=(value,))


def test_context_composer_rejects_duplicate_structural_context_slices() -> None:
    shared = context_slice("shared")
    first = ContextCandidate(context_slice=shared, relevance=0.6, age=None)
    second = ContextCandidate(context_slice=shared, relevance=0.9, age=timedelta(0))
    with pytest.raises(InvalidContextComposerError, match="duplicate"):
        composer().compose(request=request(), candidates=(first, second))


def test_context_composer_accepts_same_content_ref_for_distinct_slices() -> None:
    first = candidate("shared", trust=ContextTrustLevel.TRUSTED)
    second = replace(
        first,
        context_slice=replace(first.context_slice, trust=ContextTrustLevel.UNVERIFIED),
    )
    package = composer().compose(request=request(), candidates=(first, second))
    assert first.context_slice.content_ref == second.context_slice.content_ref
    assert first.context_slice != second.context_slice
    assert package.slices == (first.context_slice, second.context_slice)


@pytest.mark.parametrize(
    "maximum,current,eligible",
    [
        (ContextSensitivity.PUBLIC, ContextSensitivity.PUBLIC, True),
        (ContextSensitivity.PUBLIC, ContextSensitivity.INTERNAL, False),
        (ContextSensitivity.PUBLIC, ContextSensitivity.PRIVATE, False),
        (ContextSensitivity.PUBLIC, ContextSensitivity.SECRET, False),
        (ContextSensitivity.INTERNAL, ContextSensitivity.PUBLIC, True),
        (ContextSensitivity.INTERNAL, ContextSensitivity.INTERNAL, True),
        (ContextSensitivity.INTERNAL, ContextSensitivity.PRIVATE, False),
        (ContextSensitivity.INTERNAL, ContextSensitivity.SECRET, False),
        (ContextSensitivity.PRIVATE, ContextSensitivity.PUBLIC, True),
        (ContextSensitivity.PRIVATE, ContextSensitivity.INTERNAL, True),
        (ContextSensitivity.PRIVATE, ContextSensitivity.PRIVATE, True),
        (ContextSensitivity.PRIVATE, ContextSensitivity.SECRET, False),
        (ContextSensitivity.SECRET, ContextSensitivity.PUBLIC, True),
        (ContextSensitivity.SECRET, ContextSensitivity.INTERNAL, True),
        (ContextSensitivity.SECRET, ContextSensitivity.PRIVATE, True),
        (ContextSensitivity.SECRET, ContextSensitivity.SECRET, True),
    ],
)
def test_context_composer_applies_sensitivity_precedence(
    maximum: ContextSensitivity,
    current: ContextSensitivity,
    eligible: bool,
) -> None:
    refs = compose_refs(
        (candidate("sensitivity", sensitivity=current),),
        current_request=request(max_sensitivity=maximum),
    )
    assert bool(refs) is eligible


@pytest.mark.parametrize(
    "minimum,current,eligible",
    [
        (ContextTrustLevel.UNTRUSTED, ContextTrustLevel.UNTRUSTED, True),
        (ContextTrustLevel.UNTRUSTED, ContextTrustLevel.UNVERIFIED, True),
        (ContextTrustLevel.UNTRUSTED, ContextTrustLevel.TRUSTED, True),
        (ContextTrustLevel.UNVERIFIED, ContextTrustLevel.UNTRUSTED, False),
        (ContextTrustLevel.UNVERIFIED, ContextTrustLevel.UNVERIFIED, True),
        (ContextTrustLevel.UNVERIFIED, ContextTrustLevel.TRUSTED, True),
        (ContextTrustLevel.TRUSTED, ContextTrustLevel.UNTRUSTED, False),
        (ContextTrustLevel.TRUSTED, ContextTrustLevel.UNVERIFIED, False),
        (ContextTrustLevel.TRUSTED, ContextTrustLevel.TRUSTED, True),
    ],
)
def test_context_composer_applies_trust_precedence(
    minimum: ContextTrustLevel,
    current: ContextTrustLevel,
    eligible: bool,
) -> None:
    refs = compose_refs(
        (candidate("trust", trust=current),),
        current_request=request(minimum_trust=minimum),
    )
    assert bool(refs) is eligible


@pytest.mark.parametrize("relevance,eligible", [(0.49, False), (0.5, True), (0.51, True)])
def test_context_composer_applies_relevance_boundary(relevance: float, eligible: bool) -> None:
    refs = compose_refs((candidate("relevance", relevance=relevance),))
    assert bool(refs) is eligible


@pytest.mark.parametrize("age", [None, timedelta(days=100)])
def test_context_composer_does_not_filter_freshness_without_max_age(
    age: timedelta | None,
) -> None:
    assert compose_refs((candidate("freshness", age=age),)) == ("freshness",)


@pytest.mark.parametrize(
    "age,eligible",
    [
        (None, False),
        (timedelta(minutes=4, seconds=59), True),
        (timedelta(minutes=5), True),
        (timedelta(minutes=5, seconds=1), False),
    ],
)
def test_context_composer_applies_freshness_boundary(
    age: timedelta | None,
    eligible: bool,
) -> None:
    refs = compose_refs(
        (candidate("freshness", age=age),),
        current_request=request(max_age=timedelta(minutes=5)),
    )
    assert bool(refs) is eligible


def test_context_composer_accepts_data_without_authority() -> None:
    assert compose_refs(
        (candidate("data", authority=None),),
        current_request=request(allowed_authorities=()),
    ) == ("data",)


def test_context_composer_accepts_allowed_authority() -> None:
    assert compose_refs(
        (candidate("control", authority=InstructionAuthority.SYSTEM_POLICY),),
        current_request=request(allowed_authorities=(InstructionAuthority.SYSTEM_POLICY,)),
    ) == ("control",)


def test_context_composer_excludes_disallowed_authority() -> None:
    assert (
        compose_refs(
            (candidate("control", authority=InstructionAuthority.USER_EXPLICIT),),
            current_request=request(allowed_authorities=(InstructionAuthority.SYSTEM_POLICY,)),
        )
        == ()
    )


def test_context_composer_hard_excludes_forbidden_type() -> None:
    forbidden = candidate(
        "forbidden",
        slice_type=ContextSliceType.MEMORY,
        relevance=1.0,
        age=timedelta(0),
        sensitivity=ContextSensitivity.PUBLIC,
        trust=ContextTrustLevel.TRUSTED,
        authority=None,
    )
    assert (
        compose_refs(
            (forbidden,),
            current_request=request(forbidden_slice_types=(ContextSliceType.MEMORY,)),
        )
        == ()
    )


@pytest.mark.parametrize(
    "required_candidate,request_changes",
    [
        (None, {}),
        (candidate("low-relevance", slice_type=ContextSliceType.TASK, relevance=0.49), {}),
        (
            candidate(
                "sensitive",
                slice_type=ContextSliceType.TASK,
                sensitivity=ContextSensitivity.SECRET,
            ),
            {"max_sensitivity": ContextSensitivity.PUBLIC},
        ),
        (
            candidate(
                "untrusted",
                slice_type=ContextSliceType.TASK,
                trust=ContextTrustLevel.UNTRUSTED,
            ),
            {"minimum_trust": ContextTrustLevel.TRUSTED},
        ),
        (
            candidate("stale", slice_type=ContextSliceType.TASK, age=timedelta(minutes=6)),
            {"max_age": timedelta(minutes=5)},
        ),
        (
            candidate("unknown-age", slice_type=ContextSliceType.TASK, age=None),
            {"max_age": timedelta(minutes=5)},
        ),
        (
            candidate(
                "authority",
                slice_type=ContextSliceType.TASK,
                authority=InstructionAuthority.USER_EXPLICIT,
            ),
            {"allowed_authorities": ()},
        ),
    ],
    ids=[
        "no-candidate",
        "relevance",
        "sensitivity",
        "trust",
        "stale",
        "unknown-age",
        "authority",
    ],
)
def test_context_composer_never_bypasses_eligibility_for_required_types(
    required_candidate: ContextCandidate | None,
    request_changes: dict[str, object],
) -> None:
    required_request = request(
        required_slice_types=(ContextSliceType.TASK,),
        **request_changes,
    )
    candidates = () if required_candidate is None else (required_candidate,)
    with pytest.raises(ContextCompositionUnsatisfiedError):
        composer().compose(request=required_request, candidates=candidates)


def test_required_ranking_prefers_lower_token_estimate_first() -> None:
    assert (
        required_choice(
            candidate("large", slice_type=ContextSliceType.TASK, token_estimate=20, relevance=1.0),
            candidate("small", slice_type=ContextSliceType.TASK, token_estimate=10, relevance=0.5),
        )
        == "small"
    )


def test_required_ranking_then_prefers_lower_sensitivity() -> None:
    assert (
        required_choice(
            candidate(
                "private", slice_type=ContextSliceType.TASK, sensitivity=ContextSensitivity.PRIVATE
            ),
            candidate(
                "public", slice_type=ContextSliceType.TASK, sensitivity=ContextSensitivity.PUBLIC
            ),
        )
        == "public"
    )


def test_required_ranking_then_prefers_higher_trust() -> None:
    assert (
        required_choice(
            candidate(
                "unverified", slice_type=ContextSliceType.TASK, trust=ContextTrustLevel.UNVERIFIED
            ),
            candidate("trusted", slice_type=ContextSliceType.TASK, trust=ContextTrustLevel.TRUSTED),
        )
        == "trusted"
    )


def test_required_ranking_then_prefers_higher_relevance() -> None:
    assert (
        required_choice(
            candidate("lower", slice_type=ContextSliceType.TASK, relevance=0.7),
            candidate("higher", slice_type=ContextSliceType.TASK, relevance=0.9),
        )
        == "higher"
    )


def test_required_ranking_then_prefers_known_age() -> None:
    assert (
        required_choice(
            candidate("unknown", slice_type=ContextSliceType.TASK, age=None),
            candidate("known", slice_type=ContextSliceType.TASK, age=timedelta(days=100)),
        )
        == "known"
    )


def test_required_ranking_then_prefers_lower_known_age() -> None:
    assert (
        required_choice(
            candidate("older", slice_type=ContextSliceType.TASK, age=timedelta(minutes=2)),
            candidate("newer", slice_type=ContextSliceType.TASK, age=timedelta(minutes=1)),
        )
        == "newer"
    )


def test_required_ranking_uses_input_position_as_final_tie_breaker() -> None:
    assert (
        required_choice(
            candidate("first", slice_type=ContextSliceType.TASK),
            candidate("second", slice_type=ContextSliceType.TASK),
        )
        == "first"
    )


def test_required_coverage_minimizes_tokens_before_extra_relevance() -> None:
    candidates = (
        candidate("task-large", slice_type=ContextSliceType.TASK, relevance=1.0, token_estimate=90),
        candidate("task-small", slice_type=ContextSliceType.TASK, relevance=0.5, token_estimate=10),
        candidate("situation", slice_type=ContextSliceType.SITUATION, token_estimate=20),
    )
    package = composer().compose(
        request=request(
            required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION),
            max_tokens=30,
        ),
        candidates=candidates,
    )
    assert tuple(item.content_ref for item in package.slices) == ("task-small", "situation")
    assert package.total_token_estimate == 30


def test_required_coverage_rejects_max_slices_shortfall() -> None:
    required_request = request(
        required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION)
    )
    candidates = (
        candidate("task", slice_type=ContextSliceType.TASK),
        candidate("situation", slice_type=ContextSliceType.SITUATION),
    )
    with pytest.raises(ContextCompositionUnsatisfiedError, match="max_slices"):
        composer(max_slices=1).compose(request=required_request, candidates=candidates)


def test_required_coverage_rejects_minimum_token_cost_above_budget() -> None:
    required_request = request(
        required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION),
        max_tokens=30,
    )
    candidates = (
        candidate("task", slice_type=ContextSliceType.TASK, token_estimate=20),
        candidate("situation", slice_type=ContextSliceType.SITUATION, token_estimate=20),
    )
    with pytest.raises(ContextCompositionUnsatisfiedError, match="max_tokens"):
        composer().compose(request=required_request, candidates=candidates)


def optional_choice(first: ContextCandidate, second: ContextCandidate) -> tuple[str, ...]:
    return compose_refs((first, second))


def test_optional_ranking_prefers_higher_relevance_first() -> None:
    assert optional_choice(
        candidate("lower", relevance=0.7), candidate("higher", relevance=0.9)
    ) == (
        "higher",
        "lower",
    )


def test_optional_ranking_then_prefers_higher_trust() -> None:
    assert optional_choice(
        candidate("unverified", trust=ContextTrustLevel.UNVERIFIED),
        candidate("trusted", trust=ContextTrustLevel.TRUSTED),
    ) == ("trusted", "unverified")


def test_optional_ranking_then_prefers_lower_sensitivity() -> None:
    assert optional_choice(
        candidate("private", sensitivity=ContextSensitivity.PRIVATE),
        candidate("public", sensitivity=ContextSensitivity.PUBLIC),
    ) == ("public", "private")


def test_optional_ranking_then_prefers_known_age() -> None:
    assert optional_choice(
        candidate("unknown", age=None),
        candidate("known", age=timedelta(days=100)),
    ) == ("known", "unknown")


def test_optional_ranking_then_prefers_lower_known_age() -> None:
    assert optional_choice(
        candidate("older", age=timedelta(minutes=2)),
        candidate("newer", age=timedelta(minutes=1)),
    ) == ("newer", "older")


def test_optional_ranking_then_prefers_lower_token_estimate() -> None:
    assert optional_choice(
        candidate("large", token_estimate=20),
        candidate("small", token_estimate=10),
    ) == ("small", "large")


def test_optional_ranking_uses_input_position_as_final_tie_breaker() -> None:
    assert optional_choice(candidate("first"), candidate("second")) == ("first", "second")


def test_required_selection_precedes_higher_relevance_optional() -> None:
    required_request = request(required_slice_types=(ContextSliceType.TASK,))
    candidates = (
        candidate("evidence", relevance=1.0),
        candidate("task", slice_type=ContextSliceType.TASK, relevance=0.5),
    )
    assert compose_refs(candidates, current_request=required_request) == ("task", "evidence")


def test_optional_token_overflow_is_skipped_not_a_break() -> None:
    current_request = request(
        required_slice_types=(ContextSliceType.TASK,),
        max_tokens=50,
    )
    candidates = (
        candidate("task", slice_type=ContextSliceType.TASK, token_estimate=20),
        candidate("large", relevance=1.0, token_estimate=40),
        candidate("fitting", relevance=0.9, token_estimate=30),
    )
    assert compose_refs(candidates, current_request=current_request) == ("task", "fitting")


def test_max_slices_bounds_zero_token_candidates() -> None:
    candidates = tuple(candidate(f"zero:{index}", token_estimate=0) for index in range(5))
    package = composer(max_slices=2).compose(request=request(), candidates=candidates)
    assert len(package.slices) == 2
    assert package.total_token_estimate == 0


def test_empty_candidates_produce_empty_package_without_required_types() -> None:
    package = composer().compose(request=request(), candidates=())
    assert package.slices == ()


def test_all_ineligible_candidates_produce_empty_package_without_required_types() -> None:
    package = composer().compose(
        request=request(),
        candidates=(candidate("low", relevance=0.49),),
    )
    assert package.slices == ()


def test_context_composer_is_deterministic() -> None:
    candidates = (candidate("first", relevance=0.8), candidate("second", relevance=0.7))
    current_composer = composer()
    first = current_composer.compose(request=request(), candidates=candidates)
    second = current_composer.compose(request=request(), candidates=candidates)
    assert first == second


def test_composed_package_preserves_all_final_invariants() -> None:
    current_policy = policy(max_slices=3)
    current_request = request(
        required_slice_types=(ContextSliceType.TASK,),
        forbidden_slice_types=(ContextSliceType.MEMORY,),
        allowed_authorities=(InstructionAuthority.SYSTEM_POLICY,),
        max_tokens=35,
    )
    candidates = (
        candidate("task", slice_type=ContextSliceType.TASK, token_estimate=10),
        candidate(
            "policy",
            slice_type=ContextSliceType.POLICY,
            authority=InstructionAuthority.SYSTEM_POLICY,
            token_estimate=10,
        ),
        candidate("evidence", token_estimate=15),
        candidate("memory", slice_type=ContextSliceType.MEMORY, relevance=1.0),
    )
    package = ContextComposer(policy=current_policy).compose(
        request=current_request,
        candidates=candidates,
    )
    assert len(package.slices) <= current_policy.max_slices
    assert package.total_token_estimate <= current_request.max_tokens
    assert all(
        item.slice_type not in current_request.forbidden_slice_types for item in package.slices
    )
    assert all(
        item.instruction_authority is None
        or item.instruction_authority in current_request.allowed_authorities
        for item in package.slices
    )
    assert all(
        any(item.slice_type is required_type for item in package.slices)
        for required_type in current_request.required_slice_types
    )
