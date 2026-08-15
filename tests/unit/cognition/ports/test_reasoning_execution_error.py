import pytest

from noema.cognition.ports import ReasoningExecutionError
from noema.shared.domain import DomainError


def test_reasoning_execution_error_inherits_directly_from_exception() -> None:
    assert ReasoningExecutionError.__bases__ == (Exception,)


def test_reasoning_execution_error_is_not_a_domain_error() -> None:
    assert not issubclass(ReasoningExecutionError, DomainError)


def test_reasoning_execution_error_can_be_raised_and_caught() -> None:
    with pytest.raises(ReasoningExecutionError):
        raise ReasoningExecutionError("technical execution failure")


def test_reasoning_execution_error_can_be_raised_without_arguments() -> None:
    with pytest.raises(ReasoningExecutionError):
        raise ReasoningExecutionError


def test_reasoning_execution_error_adds_no_instance_state() -> None:
    error = ReasoningExecutionError("failure")
    assert vars(error) == vars(Exception("failure"))
