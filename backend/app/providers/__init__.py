from app.config import get_settings
from app.llm.contracts import LLMProvider
from app.providers.fake import FakeEmbeddingAdapter, FakeLLMAdapter
from app.providers.openai_embedding import OpenAIEmbeddingAdapter
from app.providers.openai_llm import OpenAILLMAdapter
from app.rag.contracts import EmbeddingProvider

__all__ = [
    "OpenAIEmbeddingAdapter",
    "OpenAILLMAdapter",
    "FakeEmbeddingAdapter",
    "FakeLLMAdapter",
    "get_embedding_provider",
    "get_llm_provider",
]


def get_embedding_provider(model: str | None = None) -> EmbeddingProvider:
    settings = get_settings()
    key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    if settings.test_mode or not key:
        return FakeEmbeddingAdapter(model=model or "fake-embedding-small")
    return OpenAIEmbeddingAdapter(api_key=key, model=model or "text-embedding-3-small")


def get_llm_provider(model: str | None = None) -> LLMProvider:
    settings = get_settings()
    key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    if settings.test_mode or not key:
        return FakeLLMAdapter(model=model or "fake-llm-mini")
    return OpenAILLMAdapter(api_key=key, model=model or "gpt-4o-mini")

