import inspect
from typing import get_type_hints

import pytest

from noema.cognition.application import (
    RuntimeContentReferenceAuthority,
    RuntimeContentReferenceConflictError,
    RuntimeContentReferenceNotFoundError,
)

# --- class shape --------------------------------------------------------------


def test_authority_has_exact_slots() -> None:
    assert RuntimeContentReferenceAuthority.__slots__ == ("_content_by_ref",)


def test_authority_instances_have_no_dict() -> None:
    authority = RuntimeContentReferenceAuthority()
    assert not hasattr(authority, "__dict__")


def test_constructor_takes_no_arguments() -> None:
    authority = RuntimeContentReferenceAuthority()
    assert isinstance(authority, RuntimeContentReferenceAuthority)
    with pytest.raises(TypeError):
        RuntimeContentReferenceAuthority(object())  # type: ignore[call-arg]


# --- signatures -----------------------------------------------------------


def test_register_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(RuntimeContentReferenceAuthority.register)
    assert list(signature.parameters) == ["self", "content_ref", "payload"]
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty


def test_resolve_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(RuntimeContentReferenceAuthority.resolve)
    assert list(signature.parameters) == ["self", "content_ref"]
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty


def test_register_is_not_a_coroutine_function() -> None:
    assert not inspect.iscoroutinefunction(RuntimeContentReferenceAuthority.register)


def test_resolve_is_not_a_coroutine_function() -> None:
    assert not inspect.iscoroutinefunction(RuntimeContentReferenceAuthority.resolve)


def test_register_type_hints_are_exact() -> None:
    hints = get_type_hints(RuntimeContentReferenceAuthority.register)
    assert hints == {
        "content_ref": str,
        "payload": str,
        "return": type(None),
    }


def test_resolve_type_hints_are_exact() -> None:
    hints = get_type_hints(RuntimeContentReferenceAuthority.resolve)
    assert hints == {
        "content_ref": str,
        "return": str,
    }


# --- public surface -------------------------------------------------------


def test_public_surface_is_only_register_and_resolve() -> None:
    public_members = {
        name for name in vars(RuntimeContentReferenceAuthority) if not name.startswith("_")
    }
    assert public_members == {"register", "resolve"}


def test_forbidden_operations_are_not_exposed() -> None:
    for forbidden in (
        "get",
        "put",
        "save",
        "fetch",
        "contains",
        "exists",
        "delete",
        "remove",
        "replace",
        "update",
        "items",
        "keys",
        "values",
        "snapshot",
        "count",
        "clear",
        "register_many",
        "resolve_many",
    ):
        assert not hasattr(RuntimeContentReferenceAuthority, forbidden)


# --- registration -----------------------------------------------------------


def test_new_registration_resolves_to_the_exact_payload() -> None:
    authority = RuntimeContentReferenceAuthority()

    authority.register(content_ref="task:1", payload="the exact payload")

    assert authority.resolve(content_ref="task:1") == "the exact payload"


def test_registration_returns_none() -> None:
    authority = RuntimeContentReferenceAuthority()
    assert authority.register(content_ref="task:1", payload="payload") is None


def test_same_ref_same_payload_registered_twice_is_a_no_op() -> None:
    authority = RuntimeContentReferenceAuthority()

    authority.register(content_ref="task:1", payload="the exact payload")
    authority.register(content_ref="task:1", payload="the exact payload")

    assert authority.resolve(content_ref="task:1") == "the exact payload"


def test_same_ref_different_payload_raises_conflict() -> None:
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:1", payload="original")

    with pytest.raises(RuntimeContentReferenceConflictError):
        authority.register(content_ref="task:1", payload="different")


def test_conflict_retains_the_original_payload() -> None:
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:1", payload="original")

    with pytest.raises(RuntimeContentReferenceConflictError):
        authority.register(content_ref="task:1", payload="different")

    assert authority.resolve(content_ref="task:1") == "original"


def test_different_refs_may_map_to_the_same_payload() -> None:
    authority = RuntimeContentReferenceAuthority()

    authority.register(content_ref="task:1", payload="shared payload")
    authority.register(content_ref="task:2", payload="shared payload")

    assert authority.resolve(content_ref="task:1") == "shared payload"
    assert authority.resolve(content_ref="task:2") == "shared payload"


def test_same_ref_empty_payload_is_a_valid_registration() -> None:
    authority = RuntimeContentReferenceAuthority()

    authority.register(content_ref="task:1", payload="")

    assert authority.resolve(content_ref="task:1") == ""


def test_blank_whitespace_reference_is_accepted() -> None:
    authority = RuntimeContentReferenceAuthority()

    authority.register(content_ref="   ", payload="payload")

    assert authority.resolve(content_ref="   ") == "payload"


def test_exact_whitespace_payload_is_preserved() -> None:
    authority = RuntimeContentReferenceAuthority()

    authority.register(content_ref="task:1", payload="  \n\t  ")

    assert authority.resolve(content_ref="task:1") == "  \n\t  "


# --- resolution ---------------------------------------------------------------


def test_unknown_reference_raises_not_found() -> None:
    authority = RuntimeContentReferenceAuthority()

    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority.resolve(content_ref="task:never-registered")


def test_registered_empty_string_is_distinct_from_missing() -> None:
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:1", payload="")

    assert authority.resolve(content_ref="task:1") == ""
    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority.resolve(content_ref="task:never-registered")


def test_repeated_resolution_returns_the_same_exact_value() -> None:
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:1", payload="stable payload")

    first = authority.resolve(content_ref="task:1")
    second = authority.resolve(content_ref="task:1")

    assert first == second == "stable payload"


def test_resolution_does_not_mutate_authority_state() -> None:
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:1", payload="payload")

    authority.resolve(content_ref="task:1")
    authority.resolve(content_ref="task:1")

    # A third, independent registration attempt with the same exact payload
    # must still be recognized as the identical association, proving
    # resolution introduced no hidden state change.
    authority.register(content_ref="task:1", payload="payload")
    assert authority.resolve(content_ref="task:1") == "payload"


# --- typing -------------------------------------------------------------------


@pytest.mark.parametrize("invalid_ref", [None, object(), 1, True, {}, ()])
def test_register_rejects_non_str_content_ref(invalid_ref: object) -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="content_ref"):
        authority.register(content_ref=invalid_ref, payload="payload")  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_payload", [None, object(), 1, True, {}, ()])
def test_register_rejects_non_str_payload(invalid_payload: object) -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="payload"):
        authority.register(content_ref="task:1", payload=invalid_payload)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_ref", [None, object(), 1, True, {}, ()])
def test_resolve_rejects_non_str_content_ref(invalid_ref: object) -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="content_ref"):
        authority.resolve(content_ref=invalid_ref)  # type: ignore[arg-type]


def test_invalid_type_register_does_not_mutate_state() -> None:
    authority = RuntimeContentReferenceAuthority()

    with pytest.raises(TypeError):
        authority.register(content_ref=1, payload="payload")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        authority.register(content_ref="task:1", payload=1)  # type: ignore[arg-type]

    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority.resolve(content_ref="task:1")


# --- secrecy --------------------------------------------------------------


def test_conflict_error_omits_existing_and_attempted_payload() -> None:
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:1", payload="EXISTING_DISTINCTIVE_PAYLOAD")

    with pytest.raises(RuntimeContentReferenceConflictError) as raised:
        authority.register(content_ref="task:1", payload="ATTEMPTED_DISTINCTIVE_PAYLOAD")

    message = str(raised.value)
    assert "EXISTING_DISTINCTIVE_PAYLOAD" not in message
    assert "ATTEMPTED_DISTINCTIVE_PAYLOAD" not in message
    assert "task:1" in message


def test_not_found_error_contains_no_payload_text() -> None:
    authority = RuntimeContentReferenceAuthority()

    with pytest.raises(RuntimeContentReferenceNotFoundError) as raised:
        authority.resolve(content_ref="task:missing-ref")

    assert "task:missing-ref" in str(raised.value)


# --- cross-instance independence ------------------------------------------


def test_two_authorities_are_independent() -> None:
    authority_a = RuntimeContentReferenceAuthority()
    authority_b = RuntimeContentReferenceAuthority()
    assert authority_a is not authority_b

    authority_a.register(content_ref="task:1", payload="payload A")

    assert authority_a.resolve(content_ref="task:1") == "payload A"
    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority_b.resolve(content_ref="task:1")


def test_second_authority_may_independently_register_the_same_reference() -> None:
    authority_a = RuntimeContentReferenceAuthority()
    authority_b = RuntimeContentReferenceAuthority()

    authority_a.register(content_ref="task:1", payload="payload A")
    authority_b.register(content_ref="task:1", payload="payload B")

    assert authority_a.resolve(content_ref="task:1") == "payload A"
    assert authority_b.resolve(content_ref="task:1") == "payload B"


# --- application export --------------------------------------------------


def test_application_package_exports_runtime_content_reference_authority() -> None:
    from noema.cognition import application

    assert "RuntimeContentReferenceAuthority" in application.__all__
    assert "RuntimeContentReferenceConflictError" in application.__all__
    assert "RuntimeContentReferenceNotFoundError" in application.__all__


def test_conflict_error_inherits_directly_from_exception() -> None:
    assert RuntimeContentReferenceConflictError.__bases__ == (Exception,)


def test_not_found_error_inherits_directly_from_exception() -> None:
    assert RuntimeContentReferenceNotFoundError.__bases__ == (Exception,)
