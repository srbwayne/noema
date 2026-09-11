"""Assemble the first DIRECT reasoning operation's ReasoningRequest."""

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import ContextPackage, ContextRequest
from noema.cognition.domain.reasoning import ReasoningRequest, ReasoningStrategy


def assemble_direct_reasoning_request(
    *,
    context_request: ContextRequest,
    problem_ref: str,
    problem_statement: str,
    budget: CognitiveBudget,
) -> ReasoningRequest:
    """Build the DIRECT-only ReasoningRequest for the first DIRECT operation path.

    Wraps ``context_request`` in an empty ``ContextPackage`` -- the only context
    shape the first concrete ``ReasoningExecutor`` (``ModelReasoningExecutor``)
    currently supports -- and returns a ``ReasoningRequest`` fixed to
    ``ReasoningStrategy.DIRECT``. Every other input is forwarded exactly as
    supplied; ``context_request`` and ``budget`` are retained by reference, not
    reconstructed. ``ContextPackage`` and ``ReasoningRequest`` own their own
    construction invariants, so an invalid ``context_request`` (for example one
    requiring non-empty context slices) or an invalid
    ``problem_ref``/``problem_statement``/``budget`` raises the corresponding
    domain error unwrapped.

    This function selects no context policy, invokes no ``ContextComposer``,
    chooses no budget values, selects no strategy dynamically, executes no
    reasoning, and performs no I/O.
    """
    context_package = ContextPackage(
        request=context_request,
        slices=(),
    )
    return ReasoningRequest(
        problem_ref=problem_ref,
        problem_statement=problem_statement,
        context=context_package,
        strategy=ReasoningStrategy.DIRECT,
        budget=budget,
    )
