from typing import Any
from app.config import get_settings
from app.llm.contracts import LLMProvider
from app.rag.contracts import EmbeddingProvider

__all__ = [
    "GeminiLLMAdapter",
    "OpenAIEmbeddingAdapter",
    "OpenAILLMAdapter",
    "FakeEmbeddingAdapter",
    "FakeLLMAdapter",
    "get_embedding_provider",
    "get_llm_provider",
]


def __getattr__(name: str) -> Any:
    if name == "GeminiLLMAdapter":
        from app.providers.gemini_llm import GeminiLLMAdapter
        return GeminiLLMAdapter
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
    if settings.test_mode:
        from app.providers.fake import FakeLLMAdapter
        return FakeLLMAdapter(model=model or "fake-llm-mini")

    gemini_key = settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else ""
    openai_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""

    if settings.llm_provider == "gemini" or (gemini_key and settings.llm_provider != "openai"):
        if gemini_key:
            from app.providers.gemini_llm import GeminiLLMAdapter
            return GeminiLLMAdapter(api_key=gemini_key, model=model or "gemini-flash-lite-latest")
        from app.providers.fake import FakeLLMAdapter
        return FakeLLMAdapter(model=model or "fake-llm-mini")

    if openai_key:
        from app.providers.openai_llm import OpenAILLMAdapter
        return OpenAILLMAdapter(api_key=openai_key, model=model or "gpt-4o-mini")

    from app.providers.fake import FakeLLMAdapter
    return FakeLLMAdapter(model=model or "fake-llm-mini")
