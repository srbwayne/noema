"""Noema command-line entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys
import tomllib
from pathlib import Path

from noema._process import (
    _execute_first_direct_session,
    _load_first_direct_process_configuration,
    _ProcessConfigurationError,
)
from noema.cognition.domain.reasoning import ReasoningOutcome
from noema.cognition.ports import ReasoningExecutionError
from noema.shared.domain import DomainError


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the first-DIRECT CLI process."""
    parser = argparse.ArgumentParser(
        prog="noema",
        description="Run one or more sequential first-DIRECT Noema reasoning operations.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to an explicit first-DIRECT process configuration TOML file.",
    )
    parser.add_argument(
        "problems",
        nargs="+",
        help="One or more problem statements, executed sequentially in the given order.",
    )
    return parser


def _render_outcome(outcome: ReasoningOutcome) -> None:
    """Print a human-readable rendering of a valid ReasoningOutcome.

    Covers every ``ReasoningStatus`` a valid outcome may carry, without
    printing implementation metadata (``problem_ref``, ``strategy``,
    status label, or a need's opaque ``subject_ref``).
    """
    if outcome.conclusion is not None:
        print(outcome.conclusion)
    else:
        print(outcome.reason_summary)

    if outcome.information_needs:
        print()
        print("Information needed:")
        for need in outcome.information_needs:
            print(f"- {need.description}")


def main() -> int:
    """Run one first-DIRECT process session and return its exit status.

    A session attempts one or more problem statements, in order, within one
    runtime instance. ``0`` means every attempted operation returned a valid
    ``ReasoningOutcome`` (regardless of semantic status -- semantic
    incompleteness is not a process failure), ``1`` means an attempted
    operation raised a technical ``ReasoningExecutionError``, and ``2``
    means a CLI, configuration, or invocation-construction failure. The
    first raised exception aborts the remaining session immediately: no
    later problem statement is attempted, and no output is rendered for a
    failed session. Any other exception is an unexpected defect and
    propagates with its traceback intact.
    """
    parser = _build_parser()
    args = parser.parse_args()

    try:
        configuration = _load_first_direct_process_configuration(args.config)
    except (OSError, tomllib.TOMLDecodeError, _ProcessConfigurationError, DomainError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        outcomes = asyncio.run(
            _execute_first_direct_session(
                configuration=configuration,
                problem_statements=tuple(args.problems),
            )
        )
    except ReasoningExecutionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (_ProcessConfigurationError, DomainError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for index, outcome in enumerate(outcomes):
        if index:
            print()
        _render_outcome(outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
