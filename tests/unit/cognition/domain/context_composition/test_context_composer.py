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
        max_total_content_size=1000,
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
    content_size: int = 10,
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
        content_size=content_size,
    )


def candidate(
    content_ref: str,
    *,
    slice_type: ContextSliceType = ContextSliceType.EVIDENCE,
    relevance: float | None = 0.8,
    age: timedelta | None = timedelta(0),
    content_size: int = 10,
    sensitivity: ContextSensitivity = ContextSensitivity.PUBLIC,
    trust: ContextTrustLevel = ContextTrustLevel.TRUSTED,
    authority: InstructionAuthority | None = None,
) -> ContextCandidate:
    return ContextCandidate(
        context_slice=context_slice(
            content_ref,
            slice_type=slice_type,
            content_size=content_size,
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
        (
            candidate(
                "unknown-relevance-sensitive",
                slice_type=ContextSliceType.TASK,
                relevance=None,
                sensitivity=ContextSensitivity.SECRET,
            ),
            {"max_sensitivity": ContextSensitivity.PUBLIC},
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
        "unknown-relevance-fails-other-guardrail",
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


def test_unknown_relevance_required_candidate_satisfies_required_coverage() -> None:
    """A single unknown-relevance candidate may satisfy an unsatisfied required type."""
    required_request = request(required_slice_types=(ContextSliceType.TASK,))
    candidates = (candidate("unknown-task", slice_type=ContextSliceType.TASK, relevance=None),)
    assert compose_refs(candidates, current_request=required_request) == ("unknown-task",)


def test_unknown_relevance_candidate_is_ineligible_for_optional_enrichment() -> None:
    """Unknown relevance never reaches optional enrichment, regardless of budget room."""
    candidates = (candidate("unknown", relevance=None),)
    assert compose_refs(candidates) == ()


def test_unknown_relevance_required_candidate_never_becomes_optional_when_not_required() -> None:
    """Unknown relevance is not rescued by required_slice_types for a different type."""
    required_request = request(required_slice_types=(ContextSliceType.SITUATION,))
    candidates = (
        candidate(
            "unknown-task",
            slice_type=ContextSliceType.TASK,
            relevance=None,
        ),
        candidate(
            "situation",
            slice_type=ContextSliceType.SITUATION,
            relevance=0.9,
        ),
    )
    assert compose_refs(candidates, current_request=required_request) == ("situation",)


def test_known_relevance_wins_required_slot_over_unknown_and_surplus_is_not_optional() -> None:
    """Known relevance ranks ahead of unknown for the required slot; the losing

    unknown-relevance candidate of the same required type is not admitted as
    optional enrichment afterward -- required-type authority is coverage-bound.
    """
    required_request = request(required_slice_types=(ContextSliceType.TASK,))
    candidates = (
        candidate("known", slice_type=ContextSliceType.TASK, relevance=0.9),
        candidate("unknown", slice_type=ContextSliceType.TASK, relevance=None),
    )
    assert compose_refs(candidates, current_request=required_request) == ("known",)


def test_two_unknown_relevance_candidates_fall_through_to_age_and_surplus_is_excluded() -> None:
    """Two unknown-relevance candidates tie at the relevance dimension and are

    ranked by age; only the selected representative appears, the surplus
    unknown candidate is never optional enrichment.
    """
    required_request = request(required_slice_types=(ContextSliceType.TASK,))
    candidates = (
        candidate(
            "older",
            slice_type=ContextSliceType.TASK,
            relevance=None,
            age=timedelta(minutes=10),
        ),
        candidate(
            "newer",
            slice_type=ContextSliceType.TASK,
            relevance=None,
            age=timedelta(minutes=1),
        ),
    )
    assert compose_refs(candidates, current_request=required_request) == ("newer",)


def test_two_known_candidates_one_required_remainder_may_become_optional() -> None:
    """When two known-relevance candidates match one required type, the

    non-selected remainder may still be admitted as ordinary optional
    enrichment if capacity permits.
    """
    required_request = request(required_slice_types=(ContextSliceType.TASK,))
    candidates = (
        candidate("higher", slice_type=ContextSliceType.TASK, relevance=0.9),
        candidate("lower", slice_type=ContextSliceType.TASK, relevance=0.6),
    )
    assert compose_refs(candidates, current_request=required_request) == ("higher", "lower")


def test_unknown_relevance_satisfies_coverage_while_known_low_remains_excluded() -> None:
    """An unknown-relevance required candidate may satisfy coverage while a

    known below-threshold candidate of the same type remains permanently
    excluded, unaffected by the other candidate's unknown status.
    """
    required_request = request(required_slice_types=(ContextSliceType.TASK,))
    candidates = (
        candidate("unknown", slice_type=ContextSliceType.TASK, relevance=None),
        candidate("known-low", slice_type=ContextSliceType.TASK, relevance=0.4),
    )
    assert compose_refs(candidates, current_request=required_request) == ("unknown",)


def test_required_ranking_prefers_lower_content_size_first() -> None:
    assert (
        required_choice(
            candidate("large", slice_type=ContextSliceType.TASK, content_size=20, relevance=1.0),
            candidate("small", slice_type=ContextSliceType.TASK, content_size=10, relevance=0.5),
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


def test_required_ranking_then_prefers_known_relevance_over_unknown() -> None:
    assert (
        required_choice(
            candidate("unknown", slice_type=ContextSliceType.TASK, relevance=None),
            candidate("known", slice_type=ContextSliceType.TASK, relevance=0.5),
        )
        == "known"
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


def test_required_ranking_size_precedes_unknown_vs_known_relevance_preference() -> None:
    """content_size still precedes the relevance dimension even when one

    candidate's relevance is unknown -- the structural relevance-key
    discriminator must not accidentally outrank the size dimension that
    already precedes it.
    """
    assert (
        required_choice(
            candidate(
                "smaller-unknown",
                slice_type=ContextSliceType.TASK,
                content_size=1,
                relevance=None,
            ),
            candidate(
                "larger-known",
                slice_type=ContextSliceType.TASK,
                content_size=100,
                relevance=1.0,
            ),
        )
        == "smaller-unknown"
    )


def test_required_ranking_size_precedes_sensitivity_trust_and_relevance() -> None:
    """content_size, sensitivity, and trust all precede relevance in required

    ranking precedence -- a smaller-but-otherwise-worse candidate still wins.
    """
    assert (
        required_choice(
            candidate(
                "small-but-worse",
                slice_type=ContextSliceType.TASK,
                content_size=1,
                sensitivity=ContextSensitivity.SECRET,
                trust=ContextTrustLevel.UNTRUSTED,
                relevance=0.5,
            ),
            candidate(
                "large-but-better",
                slice_type=ContextSliceType.TASK,
                content_size=100,
                sensitivity=ContextSensitivity.PUBLIC,
                trust=ContextTrustLevel.TRUSTED,
                relevance=1.0,
            ),
        )
        == "small-but-worse"
    )


def test_required_coverage_minimizes_content_size_before_extra_relevance() -> None:
    candidates = (
        candidate("task-large", slice_type=ContextSliceType.TASK, relevance=1.0, content_size=90),
        candidate("task-small", slice_type=ContextSliceType.TASK, relevance=0.5, content_size=10),
        candidate("situation", slice_type=ContextSliceType.SITUATION, content_size=20),
    )
    package = composer().compose(
        request=request(
            required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION),
            max_total_content_size=30,
        ),
        candidates=candidates,
    )
    assert tuple(item.content_ref for item in package.slices) == ("task-small", "situation")
    assert package.total_content_size == 30


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


def test_required_coverage_rejects_minimum_content_size_above_budget() -> None:
    required_request = request(
        required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION),
        max_total_content_size=30,
    )
    candidates = (
        candidate("task", slice_type=ContextSliceType.TASK, content_size=20),
        candidate("situation", slice_type=ContextSliceType.SITUATION, content_size=20),
    )
    with pytest.raises(ContextCompositionUnsatisfiedError, match="max_total_content_size"):
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


def test_optional_ranking_then_prefers_lower_content_size() -> None:
    assert optional_choice(
        candidate("large", content_size=20),
        candidate("small", content_size=10),
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


def test_optional_content_size_overflow_is_skipped_not_a_break() -> None:
    current_request = request(
        required_slice_types=(ContextSliceType.TASK,),
        max_total_content_size=50,
    )
    candidates = (
        candidate("task", slice_type=ContextSliceType.TASK, content_size=20),
        candidate("large", relevance=1.0, content_size=40),
        candidate("fitting", relevance=0.9, content_size=30),
    )
    assert compose_refs(candidates, current_request=current_request) == ("task", "fitting")


def test_max_slices_bounds_zero_size_candidates() -> None:
    candidates = tuple(candidate(f"zero:{index}", content_size=0) for index in range(5))
    package = composer(max_slices=2).compose(request=request(), candidates=candidates)
    assert len(package.slices) == 2
    assert package.total_content_size == 0


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
        max_total_content_size=35,
    )
    candidates = (
        candidate("task", slice_type=ContextSliceType.TASK, content_size=10),
        candidate(
            "policy",
            slice_type=ContextSliceType.POLICY,
            authority=InstructionAuthority.SYSTEM_POLICY,
            content_size=10,
        ),
        candidate("evidence", content_size=15),
        candidate("memory", slice_type=ContextSliceType.MEMORY, relevance=1.0),
    )
    package = ContextComposer(policy=current_policy).compose(
        request=current_request,
        candidates=candidates,
    )
    assert len(package.slices) <= current_policy.max_slices
    assert package.total_content_size <= current_request.max_total_content_size
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
