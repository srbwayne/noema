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
    CanonicalInputIngestor,
    CognitiveBudgetAdmittingReasoningExecutor,
    CognitiveBudgetTimeBoundReasoningExecutor,
    CognitiveStateOwner,
    ContextPackagePreparer,
    ContextRequestAssembler,
    DirectReasoningOperation,
    PriorTaskContextMaterializer,
    PriorTaskContextProjector,
    PriorTaskReasoningInputMaterializer,
    ReasoningEngine,
    ReasoningStrategyAdmittingDirectOperation,
    RuntimeContentReferenceAuthority,
)
from noema.cognition.domain.context_composition import ContextComposer, ContextCompositionPolicy
from noema.cognition.domain.reasoning import ReasoningStrategySelector
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

__all__ = ["open_direct_runtime", "open_strategy_aware_direct_runtime"]


@asynccontextmanager
async def open_direct_runtime(
    *,
    workspace_budget: WorkspaceBudget,
    ollama_host: str,
    model_resource: ModelResourceCapabilities,
    prior_task_context_enabled: bool,
    context_composition_policy: ContextCompositionPolicy | None,
) -> AsyncIterator[DirectReasoningOperation]:
    """Construct one first-DIRECT runtime graph and scope its provider client.

    Receives already-resolved configuration only: a ``WorkspaceBudget`` for a
    fresh runtime-instance ``CognitiveWorkspace``/``SituationModel`` pair (the
    owner receives already-valid initial snapshots, per ADR-0028), an explicit
    Ollama host string, the single ``ModelResourceCapabilities`` candidate
    this runtime will offer for selection, and the process boundary's
    already-resolved prior-TASK context activation decision (ADR-0031):
    ``prior_task_context_enabled`` and, when enabled, one already-validated
    ``ContextCompositionPolicy`` -- this function never receives raw
    ``minimum_relevance``/``max_slices`` values and constructs no
    ``ContextCompositionPolicy`` of its own; the process boundary already
    converted them into their domain object. It selects no other runtime
    policy of its own: the required capability
    (``ModelCapability.TEXT_GENERATION``) and the singleton candidate set are
    fixed realizations of already-frozen decisions, not choices made here.

    ``ollama_host`` has no owning domain value object, so this function
    rejects a non-string or blank value before constructing any provider
    client -- an unchecked blank host would otherwise silently fall back to
    the ``OLLAMA_HOST`` environment variable or the Ollama SDK's own default,
    bypassing the explicit host this runtime was configured with. The exact
    supplied string is otherwise passed through unchanged, with no
    stripping, scheme insertion, or other normalization.

    ``prior_task_context_enabled`` must be an exact ``bool``, and it must be
    paired consistently with ``context_composition_policy``: ``True`` requires
    an actual ``ContextCompositionPolicy``, ``False`` requires ``None``. An
    inconsistent pair raises ``TypeError`` rather than being silently repaired.

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
    ``generate``, and it never contacts a real Ollama server; in particular,
    entering it registers no runtime content and ingests no canonical task.
    Two concurrently or sequentially opened contexts are fully independent
    runtime instances, each with its own ``CognitiveWorkspace``,
    ``SituationModel``, ``CognitiveStateOwner``, ``RuntimeContentReferenceAuthority``,
    and provider client, even when given the same immutable
    ``workspace_budget``/``model_resource``/``context_composition_policy``
    configuration objects.
    """
    if not isinstance(ollama_host, str):
        raise TypeError("ollama_host must be a string")
    if not ollama_host.strip():
        raise ValueError("ollama_host must be a non-empty string")
    if not isinstance(prior_task_context_enabled, bool):
        raise TypeError("prior_task_context_enabled must be a bool")
    if prior_task_context_enabled:
        if not isinstance(context_composition_policy, ContextCompositionPolicy):
            raise TypeError(
                "context_composition_policy must be a ContextCompositionPolicy when "
                "prior_task_context_enabled is True"
            )
    elif context_composition_policy is not None:
        raise TypeError(
            "context_composition_policy must be None when prior_task_context_enabled is False"
        )

    async with AsyncClient(host=ollama_host) as client:
        workspace = CognitiveWorkspace(budget=workspace_budget)
        situation = SituationModel()
        state_owner = CognitiveStateOwner(workspace=workspace, situation=situation)
        runtime_content_authority = RuntimeContentReferenceAuthority()
        canonical_input_ingestor = CanonicalInputIngestor(state_owner=state_owner)
        context_request_assembler = ContextRequestAssembler()
        prior_task_context_projector = PriorTaskContextProjector(
            runtime_content_authority=runtime_content_authority
        )
        context_composer: ContextComposer | None = None
        if prior_task_context_enabled:
            assert context_composition_policy is not None  # narrowed above
            context_composer = ContextComposer(policy=context_composition_policy)
        context_package_preparer = ContextPackagePreparer(
            state_owner=state_owner,
            context_request_assembler=context_request_assembler,
            prior_task_context_projector=prior_task_context_projector,
            context_composer=context_composer,
            prior_task_context_enabled=prior_task_context_enabled,
        )

        prior_task_context_materializer = PriorTaskContextMaterializer(
            runtime_content_authority=runtime_content_authority
        )
        input_materializer = PriorTaskReasoningInputMaterializer(
            context_materializer=prior_task_context_materializer
        )

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
        model_reasoning_executor = ModelReasoningExecutor(
            execution_engine=execution_engine,
            selection_request=selection_request,
            input_materializer=input_materializer,
        )
        time_bound_reasoning_executor = CognitiveBudgetTimeBoundReasoningExecutor(
            inner_executor=model_reasoning_executor,
        )
        budget_admitting_reasoning_executor = CognitiveBudgetAdmittingReasoningExecutor(
            inner_executor=time_bound_reasoning_executor,
        )
        reasoning_engine = ReasoningEngine(executor=budget_admitting_reasoning_executor)

        operation = DirectReasoningOperation(
            runtime_content_authority=runtime_content_authority,
            canonical_input_ingestor=canonical_input_ingestor,
            context_package_preparer=context_package_preparer,
            reasoning_engine=reasoning_engine,
        )

        yield operation


@asynccontextmanager
async def open_strategy_aware_direct_runtime(
    *,
    workspace_budget: WorkspaceBudget,
    ollama_host: str,
    model_resource: ModelResourceCapabilities,
    prior_task_context_enabled: bool,
    context_composition_policy: ContextCompositionPolicy | None,
) -> AsyncIterator[ReasoningStrategyAdmittingDirectOperation]:
    """Construct the same first-DIRECT runtime graph behind an explicit strategy-admission surface.

    Takes the exact same already-resolved configuration as
    ``open_direct_runtime`` and delegates to it entirely for runtime
    construction and provider-client lifecycle: this function enters
    ``open_direct_runtime`` itself, receives its exact yielded
    ``DirectReasoningOperation`` by identity, and constructs one
    ``ReasoningStrategySelector`` for this runtime. It builds no provider
    client of its own, constructs no second copy of the runtime graph, and
    owns none of the provider-client lifecycle -- ``open_direct_runtime``'s
    own ``async with`` scope still owns opening and deterministically
    closing the provider client exactly once, exactly as it already does for
    every other caller.

    The yielded ``ReasoningStrategyAdmittingDirectOperation`` is additive:
    ``open_direct_runtime`` itself is completely unchanged by this function's
    existence, remains independently usable exactly as before, and is not
    called by any existing caller of it as a side effect of this function
    being defined.
    """
    async with open_direct_runtime(
        workspace_budget=workspace_budget,
        ollama_host=ollama_host,
        model_resource=model_resource,
        prior_task_context_enabled=prior_task_context_enabled,
        context_composition_policy=context_composition_policy,
    ) as operation:
        reasoning_strategy_selector = ReasoningStrategySelector()
        yield ReasoningStrategyAdmittingDirectOperation(
            selector=reasoning_strategy_selector,
            direct_operation=operation,
        )
