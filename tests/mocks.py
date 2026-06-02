"""Re-Export für Tests; Implementierung in services.mock_llm."""

from backend.ai.services.mock_llm import MockEmbeddingClient, MockLLM

__all__ = ["MockEmbeddingClient", "MockLLM"]
