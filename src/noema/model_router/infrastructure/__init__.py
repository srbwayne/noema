"""Provider adapters implementing the model_router bounded context's ports."""

from .ollama_model_executor import OllamaModelExecutor

__all__ = ["OllamaModelExecutor"]
