"""Noema command-line entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys
import tomllib
from pathlib import Path

from noema._process import (
    _execute_first_direct,
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
        description="Run one first-DIRECT Noema reasoning operation.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to an explicit first-DIRECT process configuration TOML file.",
    )
    parser.add_argument(
        "problem",
        help="The problem statement for this one reasoning operation.",
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
    """Run one first-DIRECT process invocation and return its exit status.

    ``0`` for a valid ``ReasoningOutcome`` of any semantic status, ``1`` for
    a technical ``ReasoningExecutionError``, and ``2`` for a CLI,
    configuration, or invocation-construction failure. Any other exception
    is an unexpected defect and propagates with its traceback intact.
    """
    parser = _build_parser()
    args = parser.parse_args()

    try:
        configuration = _load_first_direct_process_configuration(args.config)
    except (OSError, tomllib.TOMLDecodeError, _ProcessConfigurationError, DomainError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        outcome = asyncio.run(
            _execute_first_direct(
                configuration=configuration,
                problem_statement=args.problem,
            )
        )
    except ReasoningExecutionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (_ProcessConfigurationError, DomainError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    _render_outcome(outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
