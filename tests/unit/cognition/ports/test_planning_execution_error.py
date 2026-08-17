import pytest

from noema.cognition.ports import PlanningExecutionError
from noema.shared.domain import DomainError


def test_planning_execution_error_inherits_directly_from_exception() -> None:
    assert PlanningExecutionError.__bases__ == (Exception,)


def test_planning_execution_error_is_not_a_domain_error() -> None:
    assert not issubclass(PlanningExecutionError, DomainError)


def test_planning_execution_error_can_be_raised_and_caught() -> None:
    with pytest.raises(PlanningExecutionError):
        raise PlanningExecutionError("technical execution failure")


def test_planning_execution_error_can_be_raised_without_arguments() -> None:
    with pytest.raises(PlanningExecutionError):
        raise PlanningExecutionError


def test_planning_execution_error_adds_no_instance_state() -> None:
    error = PlanningExecutionError("failure")
    assert vars(error) == vars(Exception("failure"))
