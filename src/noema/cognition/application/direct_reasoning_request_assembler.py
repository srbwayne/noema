"""Assemble the first DIRECT reasoning operation's ReasoningRequest."""

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import ContextPackage
from noema.cognition.domain.reasoning import ReasoningRequest, ReasoningStrategy


def assemble_direct_reasoning_request(
    *,
    context: ContextPackage,
    problem_ref: str,
    problem_statement: str,
    budget: CognitiveBudget,
) -> ReasoningRequest:
    """Build the DIRECT-only ReasoningRequest carrying the exact supplied ContextPackage.

    Retains ``context`` by reference -- it neither constructs nor rebuilds any
    ``ContextPackage``, inspects no slice, and composes no context -- and
    returns a ``ReasoningRequest`` fixed to ``ReasoningStrategy.DIRECT``.
    Every other input is forwarded exactly as supplied; ``context`` and
    ``budget`` are retained by reference, not reconstructed.
    ``ReasoningRequest`` owns its own construction invariants, so an invalid
    ``context``/``problem_ref``/``problem_statement``/``budget`` raises the
    corresponding domain error unwrapped.

    This function selects no context policy, invokes no ``ContextComposer``,
    chooses no budget values, selects no strategy dynamically, executes no
    reasoning, and performs no I/O.
    """
    return ReasoningRequest(
        problem_ref=problem_ref,
        problem_statement=problem_statement,
        context=context,
        strategy=ReasoningStrategy.DIRECT,
        budget=budget,
    )
