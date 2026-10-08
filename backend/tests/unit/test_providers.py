from uuid import uuid4
import pytest
from app.rag.contracts import EmbeddingIndex, EmbeddingProvider, EvidenceChunk, SourceLocator
from app.llm.contracts import GenerationRequest, GenerationResult, LLMProvider
from app.providers.fake import FakeEmbeddingAdapter, FakeLLMAdapter
from app.providers.openai_embedding import OpenAIEmbeddingAdapter
from app.providers.openai_llm import OpenAILLMAdapter


def test_fake_embedding_provider_protocol():
    adapter = FakeEmbeddingAdapter()
    assert isinstance(adapter, EmbeddingProvider)
    assert adapter.index.dimension == 1536
    assert adapter.index.model == "fake-embedding-small"

    vecs = adapter.embed(("Đoạn văn 1", "Đoạn văn 2"))
    assert len(vecs) == 2
    assert len(vecs[0]) == 1536
    assert len(vecs[1]) == 1536


def test_fake_llm_provider_protocol():
    adapter = FakeLLMAdapter()
    assert isinstance(adapter, LLMProvider)

    locator = SourceLocator(source_id=uuid4(), source_version=1, page=2)
    chunk = EvidenceChunk(dataset_id=uuid4(), locator=locator, text="Đơn hàng DH001 bị kẹt tại cổng phân loại")
    req = GenerationRequest(question="Tại sao đơn hàng chậm?", evidence=(chunk,))

    result = adapter.generate(req)
    assert isinstance(result, GenerationResult)
    assert "[1]" in result.text
    assert len(result.citations) == 1
    assert result.citations[0].page == 2


def test_openai_adapters_protocol():
    emb = OpenAIEmbeddingAdapter(api_key="sk-test-fake")
    assert isinstance(emb, EmbeddingProvider)
    assert emb.index.dimension == 1536
    assert emb.index.model == "text-embedding-3-small"

    llm = OpenAILLMAdapter(api_key="sk-test-fake")
    assert isinstance(llm, LLMProvider)
    assert llm.model == "gpt-4o-mini"
