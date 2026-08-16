import pytest

from noema.model_router.ports import ModelExecutionError
from noema.shared.domain import DomainError


def test_model_execution_error_inherits_directly_from_exception() -> None:
    assert ModelExecutionError.__bases__ == (Exception,)


def test_model_execution_error_is_not_a_domain_error() -> None:
    assert not issubclass(ModelExecutionError, DomainError)


def test_model_execution_error_can_be_raised_and_caught() -> None:
    with pytest.raises(ModelExecutionError):
        raise ModelExecutionError("technical execution failure")


def test_model_execution_error_can_be_raised_without_arguments() -> None:
    with pytest.raises(ModelExecutionError):
        raise ModelExecutionError


def test_model_execution_error_adds_no_instance_state() -> None:
    error = ModelExecutionError("failure")
    assert vars(error) == vars(Exception("failure"))
