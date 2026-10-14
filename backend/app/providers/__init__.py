from typing import Any
from app.config import get_settings
from app.llm.contracts import LLMProvider
from app.rag.contracts import EmbeddingProvider

__all__ = [
    "OpenAIEmbeddingAdapter",
    "OpenAILLMAdapter",
    "FakeEmbeddingAdapter",
    "FakeLLMAdapter",
    "get_embedding_provider",
    "get_llm_provider",
]


def __getattr__(name: str) -> Any:
    if name == "OpenAIEmbeddingAdapter":
        from app.providers.openai_embedding import OpenAIEmbeddingAdapter
        return OpenAIEmbeddingAdapter
    if name == "OpenAILLMAdapter":
        from app.providers.openai_llm import OpenAILLMAdapter
        return OpenAILLMAdapter
    if name == "FakeEmbeddingAdapter":
        from app.providers.fake import FakeEmbeddingAdapter
        return FakeEmbeddingAdapter
    if name == "FakeLLMAdapter":
        from app.providers.fake import FakeLLMAdapter
        return FakeLLMAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_embedding_provider(model: str | None = None) -> EmbeddingProvider:
    settings = get_settings()
    key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    if settings.test_mode or not key:
        from app.providers.fake import FakeEmbeddingAdapter
        return FakeEmbeddingAdapter(model=model or "fake-embedding-small")
    from app.providers.openai_embedding import OpenAIEmbeddingAdapter
    return OpenAIEmbeddingAdapter(api_key=key, model=model or "text-embedding-3-small")


def get_llm_provider(model: str | None = None) -> LLMProvider:
    settings = get_settings()
    key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    if settings.test_mode or not key:
        from app.providers.fake import FakeLLMAdapter
        return FakeLLMAdapter(model=model or "fake-llm-mini")
    from app.providers.openai_llm import OpenAILLMAdapter
    return OpenAILLMAdapter(api_key=key, model=model or "gpt-4o-mini")
