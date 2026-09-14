import asyncio
import sys
import tomllib
from pathlib import Path

import pytest

from noema._process import _FirstDirectProcessConfiguration, _ProcessConfigurationError
from noema.cognition.domain.reasoning import (
    InformationNeed,
    ReasoningOutcome,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.ports import ReasoningExecutionError
from noema.main import _build_parser, main
from noema.shared.domain import DomainError


def _outcome(
    *,
    status: ReasoningStatus,
    conclusion: str | None,
    reason_summary: str = "a reason",
    information_needs: tuple[InformationNeed, ...] = (),
) -> ReasoningOutcome:
    return ReasoningOutcome(
        problem_ref="problem:1",
        strategy=ReasoningStrategy.DIRECT,
        status=status,
        conclusion=conclusion,
        reason_summary=reason_summary,
        information_needs=information_needs,
    )


class _NeverCalled:
    """Fails the test if invoked -- used to prove a code path is skipped."""

    def __call__(self, *args: object, **kwargs: object) -> object:
        pytest.fail("must not be called on this path")


def _forbid_loader_and_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("noema.main._load_first_direct_process_configuration", _NeverCalled())
    monkeypatch.setattr("noema.main._execute_first_direct_session", _NeverCalled())


# --- parser shape (§84) -------------------------------------------------------


def test_parser_requires_config_option() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["problem text"])


def test_parser_requires_problem_positional() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--config", "config.toml"])


def test_parser_rejects_unknown_option() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--config", "config.toml", "--unknown", "problem"])


def test_parser_forwards_config_and_single_problem_exactly() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--config", "config.toml", "solve this"])
    assert args.config == Path("config.toml")
    assert args.problems == ["solve this"]


def test_parser_forwards_multiple_problems_in_order() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--config", "config.toml", "first", "second"])
    assert args.problems == ["first", "second"]


# --- CLI-level no-argument / unknown-option / help behavior (§84) ------------


def test_main_no_args_exits_2_without_config_or_runtime_call(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _forbid_loader_and_runner(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["noema"])

    with pytest.raises(SystemExit) as raised:
        main()

    assert raised.value.code == 2
    assert capsys.readouterr().err != ""


def test_main_unknown_option_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _forbid_loader_and_runner(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["noema", "--nope", "problem"])

    with pytest.raises(SystemExit) as raised:
        main()

    assert raised.value.code == 2


def test_main_help_exits_0_without_config_or_runtime_call(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _forbid_loader_and_runner(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["noema", "--help"])

    with pytest.raises(SystemExit) as raised:
        main()

    assert raised.value.code == 0
    assert "usage" in capsys.readouterr().out.lower()


# --- success path (§85) -------------------------------------------------------


def _fake_configuration() -> _FirstDirectProcessConfiguration:
    # A placeholder identity; the loader itself is patched out in these tests.
    return object()  # type: ignore[return-value]


def test_main_success_forwards_config_path_and_problems_exactly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    received: dict[str, object] = {}

    def _fake_loader(path: Path) -> object:
        received["path"] = path
        return _fake_configuration()

    async def _fake_execute(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        received["configuration"] = configuration
        received["problem_statements"] = problem_statements
        return (_outcome(status=ReasoningStatus.COMPLETED, conclusion="the answer"),)

    monkeypatch.setattr("noema.main._load_first_direct_process_configuration", _fake_loader)
    monkeypatch.setattr("noema.main._execute_first_direct_session", _fake_execute)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "my-config.toml", "What is the answer?"])

    exit_code = main()

    assert exit_code == 0
    assert received["path"] == Path("my-config.toml")
    assert received["problem_statements"] == ("What is the answer?",)


def test_main_calls_asyncio_run_exactly_once_for_one_problem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0
    real_run = asyncio.run

    def _counting_run(coro: object) -> object:
        nonlocal call_count
        call_count += 1
        return real_run(coro)  # type: ignore[arg-type]

    monkeypatch.setattr("noema.main.asyncio.run", _counting_run)
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _fake_execute(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        return (_outcome(status=ReasoningStatus.COMPLETED, conclusion="ok"),)

    monkeypatch.setattr("noema.main._execute_first_direct_session", _fake_execute)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    exit_code = main()

    assert call_count == 1
    assert exit_code == 0


def test_main_calls_asyncio_run_exactly_once_for_multiple_problems(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0
    real_run = asyncio.run

    def _counting_run(coro: object) -> object:
        nonlocal call_count
        call_count += 1
        return real_run(coro)  # type: ignore[arg-type]

    monkeypatch.setattr("noema.main.asyncio.run", _counting_run)
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _fake_execute(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        return tuple(
            _outcome(status=ReasoningStatus.COMPLETED, conclusion="ok") for _ in problem_statements
        )

    monkeypatch.setattr("noema.main._execute_first_direct_session", _fake_execute)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "first", "second"])

    exit_code = main()

    assert call_count == 1
    assert exit_code == 0


def _run_main_with_outcomes(
    monkeypatch: pytest.MonkeyPatch, outcomes: tuple[ReasoningOutcome, ...]
) -> int:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _fake_execute(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        return outcomes

    monkeypatch.setattr("noema.main._execute_first_direct_session", _fake_execute)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "noema",
            "--config",
            "config.toml",
            *(f"problem-{index}" for index in range(len(outcomes))),
        ],
    )
    return main()


def _run_main_with_outcome(monkeypatch: pytest.MonkeyPatch, outcome: ReasoningOutcome) -> int:
    return _run_main_with_outcomes(monkeypatch, (outcome,))


def test_main_success_renders_stdout_and_empty_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = _run_main_with_outcome(
        monkeypatch, _outcome(status=ReasoningStatus.COMPLETED, conclusion="the answer")
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "the answer\n"
    assert captured.err == ""


# --- outcome rendering across all statuses (§86) -----------------------------


def test_main_completed_outcome_renders_conclusion_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = _run_main_with_outcome(
        monkeypatch, _outcome(status=ReasoningStatus.COMPLETED, conclusion="42")
    )

    assert exit_code == 0
    assert capsys.readouterr().out == "42\n"


def test_main_partial_outcome_exits_zero_and_renders_needs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    need = InformationNeed(subject_ref="internal-ref-1", description="clarify scope")
    exit_code = _run_main_with_outcome(
        monkeypatch,
        _outcome(
            status=ReasoningStatus.PARTIAL,
            conclusion="a partial answer",
            information_needs=(need,),
        ),
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "a partial answer" in out
    assert "Information needed:" in out
    assert "- clarify scope" in out
    assert "internal-ref-1" not in out


def test_main_needs_information_outcome_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    need = InformationNeed(subject_ref="internal-ref-2", description="need the budget")
    exit_code = _run_main_with_outcome(
        monkeypatch,
        _outcome(
            status=ReasoningStatus.NEEDS_INFORMATION,
            conclusion=None,
            reason_summary="cannot proceed without more information",
            information_needs=(need,),
        ),
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "cannot proceed without more information" in out
    assert "- need the budget" in out
    assert "internal-ref-2" not in out


def test_main_unresolved_outcome_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = _run_main_with_outcome(
        monkeypatch,
        _outcome(
            status=ReasoningStatus.UNRESOLVED,
            conclusion=None,
            reason_summary="could not resolve the problem",
        ),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "could not resolve the problem\n"


# --- multi-outcome rendering (M0-17 G3) --------------------------------------


def test_main_two_completed_outcomes_render_with_one_blank_line_separator(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = _run_main_with_outcomes(
        monkeypatch,
        (
            _outcome(status=ReasoningStatus.COMPLETED, conclusion="answer one"),
            _outcome(status=ReasoningStatus.COMPLETED, conclusion="answer two"),
        ),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "answer one\n\nanswer two\n"
    assert captured.err == ""


def test_main_mixed_valid_statuses_render_all_in_order_and_exit_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    need = InformationNeed(subject_ref="internal-ref-3", description="need more context")
    outcomes = (
        _outcome(status=ReasoningStatus.COMPLETED, conclusion="first answer"),
        _outcome(
            status=ReasoningStatus.NEEDS_INFORMATION,
            conclusion=None,
            reason_summary="cannot proceed",
            information_needs=(need,),
        ),
        _outcome(
            status=ReasoningStatus.UNRESOLVED, conclusion=None, reason_summary="could not resolve"
        ),
    )

    exit_code = _run_main_with_outcomes(monkeypatch, outcomes)

    out = capsys.readouterr().out
    assert exit_code == 0
    first_index = out.index("first answer")
    second_index = out.index("cannot proceed")
    need_index = out.index("- need more context")
    third_index = out.index("could not resolve")
    assert first_index < second_index < need_index < third_index
    assert "internal-ref-3" not in out


# --- expected error mapping (§87) --------------------------------------------


def test_main_loader_os_error_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _raise(path: Path) -> object:
        raise OSError("cannot read file")

    monkeypatch.setattr("noema.main._load_first_direct_process_configuration", _raise)
    monkeypatch.setattr("noema.main._execute_first_direct_session", _NeverCalled())
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "missing.toml", "problem"])

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.err.startswith("error: ")


def test_main_loader_toml_decode_error_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _raise(path: Path) -> object:
        raise tomllib.TOMLDecodeError("bad toml")

    monkeypatch.setattr("noema.main._load_first_direct_process_configuration", _raise)
    monkeypatch.setattr("noema.main._execute_first_direct_session", _NeverCalled())
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "bad.toml", "problem"])

    exit_code = main()

    assert exit_code == 2


def test_main_loader_process_configuration_error_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _raise(path: Path) -> object:
        raise _ProcessConfigurationError("bad schema")

    monkeypatch.setattr("noema.main._load_first_direct_process_configuration", _raise)
    monkeypatch.setattr("noema.main._execute_first_direct_session", _NeverCalled())
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    exit_code = main()

    assert exit_code == 2


def test_main_loader_domain_error_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _raise(path: Path) -> object:
        raise DomainError("invalid domain value")

    monkeypatch.setattr("noema.main._load_first_direct_process_configuration", _raise)
    monkeypatch.setattr("noema.main._execute_first_direct_session", _NeverCalled())
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    exit_code = main()

    assert exit_code == 2


def test_main_runner_process_configuration_error_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise _ProcessConfigurationError("bad host")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    exit_code = main()

    assert exit_code == 2


def test_main_runner_domain_error_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise DomainError("invalid runtime construction")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    exit_code = main()

    assert exit_code == 2


def test_main_reasoning_execution_error_exits_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise ReasoningExecutionError("technical failure")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err.startswith("error: ")


# --- failed-batch stdout emptiness (M0-17 G3) --------------------------------


def test_main_failed_batch_reasoning_execution_error_has_empty_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise ReasoningExecutionError("technical failure")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "first", "second"])

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "error: technical failure\n"


def test_main_failed_batch_domain_error_has_empty_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise DomainError("invalid runtime construction")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "first", "second"])

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid runtime construction\n"


# --- unexpected-exception propagation (§88) ----------------------------------


def test_main_unexpected_valueerror_from_runner_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise ValueError("unexpected defect")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    with pytest.raises(ValueError, match="unexpected defect"):
        main()


def test_main_unexpected_typeerror_from_runner_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise TypeError("unexpected defect")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    with pytest.raises(TypeError, match="unexpected defect"):
        main()


def test_main_unexpected_oserror_from_runner_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "noema.main._load_first_direct_process_configuration",
        lambda path: _fake_configuration(),
    )

    async def _raise(
        *, configuration: object, problem_statements: tuple[str, ...]
    ) -> tuple[ReasoningOutcome, ...]:
        raise OSError("unexpected defect during execution")

    monkeypatch.setattr("noema.main._execute_first_direct_session", _raise)
    monkeypatch.setattr(sys, "argv", ["noema", "--config", "config.toml", "problem"])

    with pytest.raises(OSError, match="unexpected defect during execution"):
        main()
