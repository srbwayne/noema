"""The top-level composition root for one first-DIRECT Noema runtime instance.

This module is a dedicated outer assembly edge (ADR-0029): it is not a bounded
context, it owns no domain or application behavior, and no bounded-context
internal package may import it. It exists solely to construct one concrete
first-DIRECT runtime object graph from already-resolved configuration and to
scope the lifetime of the provider client that graph depends on.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ollama import AsyncClient

from noema.cognition.application import (
    CognitiveStateOwner,
    ContextRequestAssembler,
    DirectReasoningOperation,
    ReasoningEngine,
)
from noema.cognition.domain.situation import SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget
from noema.cognition.infrastructure import ModelReasoningExecutor
from noema.model_router.application import ModelExecutionEngine, ModelRouter
from noema.model_router.domain import (
    ModelCapability,
    ModelCapabilityRequirements,
    ModelResourceCapabilities,
    ModelSelectionRequest,
    ModelSelector,
)
from noema.model_router.infrastructure import OllamaModelExecutor

__all__ = ["open_direct_runtime"]


@asynccontextmanager
async def open_direct_runtime(
    *,
    workspace_budget: WorkspaceBudget,
    ollama_host: str,
    model_resource: ModelResourceCapabilities,
) -> AsyncIterator[DirectReasoningOperation]:
    """Construct one first-DIRECT runtime graph and scope its provider client.

    Receives already-resolved configuration only: a ``WorkspaceBudget`` for a
    fresh runtime-instance ``CognitiveWorkspace``/``SituationModel`` pair (the
    owner receives already-valid initial snapshots, per ADR-0028), an explicit
    Ollama host string, and the single ``ModelResourceCapabilities`` candidate
    this runtime will offer for selection. It selects no runtime policy of its
    own: the required capability (``ModelCapability.TEXT_GENERATION``) and the
    singleton candidate set are fixed realizations of already-frozen decisions,
    not choices made here.

    ``ollama_host`` has no owning domain value object, so this function
    rejects a non-string or blank value before constructing any provider
    client -- an unchecked blank host would otherwise silently fall back to
    the ``OLLAMA_HOST`` environment variable or the Ollama SDK's own default,
    bypassing the explicit host this runtime was configured with. The exact
    supplied string is otherwise passed through unchanged, with no
    stripping, scheme insertion, or other normalization.

    The Ollama ``AsyncClient`` this graph depends on is constructed and owned
    by this context: entering the context creates it, and exiting the
    context -- normally, or because the caller's code inside the context
    raised, or because a later step of this function's own construction
    raised -- deterministically closes it exactly once. No component of the
    constructed graph (``OllamaModelExecutor`` included) owns or exposes that
    lifecycle itself.

    The yielded ``DirectReasoningOperation`` is valid for use only while this
    context remains entered; its provider client is closed on exit, and nothing
    reopens it. Do not retain or call the yielded operation after the
    ``async with`` block exits.

    Entering this context constructs the graph only -- it never calls
    ``execute``, ``reason``, ``route``, ``select``, or the provider client's
    ``generate``, and it never contacts a real Ollama server. Two concurrently
    or sequentially opened contexts are fully independent runtime instances,
    each with its own ``CognitiveWorkspace``, ``SituationModel``,
    ``CognitiveStateOwner``, and provider client, even when given the same
    immutable ``workspace_budget``/``model_resource`` configuration objects.
    """
    if not isinstance(ollama_host, str):
        raise TypeError("ollama_host must be a string")
    if not ollama_host.strip():
        raise ValueError("ollama_host must be a non-empty string")

    async with AsyncClient(host=ollama_host) as client:
        workspace = CognitiveWorkspace(budget=workspace_budget)
        situation = SituationModel()
        state_owner = CognitiveStateOwner(workspace=workspace, situation=situation)
        context_request_assembler = ContextRequestAssembler(state_owner=state_owner)

        requirements = ModelCapabilityRequirements(
            required_capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        )
        selection_request = ModelSelectionRequest(
            requirements=requirements,
            candidates=frozenset({model_resource}),
        )

        ollama_executor = OllamaModelExecutor(
            provider_ref=model_resource.resource.provider_ref,
            client=client,
        )
        selector = ModelSelector()
        router = ModelRouter(selector=selector)
        execution_engine = ModelExecutionEngine(router=router, executor=ollama_executor)
        reasoning_executor = ModelReasoningExecutor(
            execution_engine=execution_engine,
            selection_request=selection_request,
        )
        reasoning_engine = ReasoningEngine(executor=reasoning_executor)

        operation = DirectReasoningOperation(
            context_request_assembler=context_request_assembler,
            reasoning_engine=reasoning_engine,
        )

        yield operation
