"""The Ollama adapter for the provider-neutral model execution port."""

from ollama import AsyncClient

from noema.model_router.ports import (
    ModelExecutionError,
    ModelExecutionRequest,
    ModelExecutionResult,
)


class OllamaModelExecutor:
    """Execute a ``ModelExecutionRequest`` against a local Ollama server.

    This adapter does not select, route, or rank resources — it only
    executes an already-selected resource against an injected
    ``ollama.AsyncClient``. It does not construct, configure, or own the
    lifecycle of that client; it does not read environment variables or
    assume a default host. It translates every technical failure of the
    Ollama SDK into ``ModelExecutionError`` so that no provider-specific
    exception crosses this port.
    """

    __slots__ = ("_provider_ref", "_client")

    def __init__(self, *, provider_ref: str, client: AsyncClient) -> None:
        """Bind this adapter to the provider it serves and the client it uses."""
        if not isinstance(provider_ref, str):
            raise TypeError("provider_ref must be a string")
        if not provider_ref.strip():
            raise ValueError("provider_ref must be a non-empty string")
        self._provider_ref = provider_ref
        self._client = client

    async def execute(self, request: ModelExecutionRequest) -> ModelExecutionResult:
        """Execute request.resource against Ollama and return its result.

        Raises ``ModelExecutionError`` if the request's resource does not
        belong to this adapter's provider, if the underlying Ollama SDK
        call fails for any technical reason, or if the response it returns
        cannot be translated into a valid ``ModelExecutionResult``.
        """
        if request.resource.provider_ref != self._provider_ref:
            raise ModelExecutionError(
                "resource provider_ref does not match Ollama executor provider_ref"
            )

        try:
            response = await self._client.generate(
                model=request.resource.model_ref,
                prompt=request.input_text,
                stream=False,
            )
        except Exception as exc:
            raise ModelExecutionError("ollama execution failed") from exc

        output_text = response.response

        if not isinstance(output_text, str) or not output_text.strip():
            raise ModelExecutionError("ollama returned an invalid response")

        return ModelExecutionResult(resource=request.resource, output_text=output_text)
