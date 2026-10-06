import ast
import importlib
from pathlib import Path
from uuid import uuid4
import pytest
from pydantic import ValidationError


def contracts():
    assert importlib.util.find_spec("app.rag"), "RAG contracts package is missing"
    return importlib.import_module("app.rag.contracts")


def test_packages_import_without_provider_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    for module in ("app.rag.contracts", "app.llm.contracts", "app.modules.log_analysis",
                   "app.modules.tickets", "app.modules.reports"):
        assert importlib.util.find_spec(module.split(".contracts")[0]), f"{module} package missing"
        importlib.import_module(module)


def test_core_imports_do_not_depend_on_provider_implementations():
    root = Path("app")
    for folder in ("auth", "database", "rag", "llm", "modules"):
        for path in (root / folder).rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                modules = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                assert not any(m.split(".")[0] in {"openai", "langchain", "langchain_core", "langchain_openai", "langchain_postgres"} for m in modules), str(path)
                if folder == "rag":
                    assert not any(m.startswith(("app.auth", "app.database", "app.api")) for m in modules), str(path)
    assert (root / "rag" / "contracts.py").exists(), "Boundary contract missing"


def test_locator_uuid_roundtrip_and_optional_locator():
    c = contracts()
    value = c.SourceLocator(source_id=uuid4(), source_version=1)
    assert c.SourceLocator.model_validate_json(value.model_dump_json()) == value
    assert value.page is None
    with pytest.raises(ValidationError):
        c.SourceLocator(source_version=1)


@pytest.mark.parametrize("field", ["source_version", "page", "row", "event", "record"])
def test_locator_integer_min_max_and_one_outside(field):
    c = contracts()
    for n in (1, 2147483647):
        data = {"source_id":uuid4(), "source_version":1, field:n}
        assert getattr(c.SourceLocator(**data), field) == n
    for n in (0,2147483648):
        with pytest.raises(ValidationError):
            c.SourceLocator(**{"source_id":uuid4(), "source_version":1, field:n})


@pytest.mark.parametrize("field", ["section", "sheet"])
def test_locator_text_bounds(field):
    c = contracts()
    for n in (1,512):
        assert getattr(c.SourceLocator(source_id=uuid4(), source_version=1, **{field:"x"*n}),field) == "x"*n
    for n in (0,513):
        with pytest.raises(ValidationError):
            c.SourceLocator(source_id=uuid4(), source_version=1, **{field:"x"*n})


def test_embedding_model_dimension_index_metadata_roundtrip():
    c = contracts()
    for length in (1,128):
        for dimension in (1,65536):
            value = c.EmbeddingIndex(model="x"*length, dimension=dimension, index_version=uuid4())
            assert c.EmbeddingIndex.model_validate_json(value.model_dump_json()) == value
    for model,dim in (("",1),("x"*129,1),("ok",0),("ok",65537)):
        with pytest.raises(ValidationError):
            c.EmbeddingIndex(model=model,dimension=dim,index_version=uuid4())
    with pytest.raises(ValidationError):
        c.EmbeddingIndex(model="ok",dimension=1,index_version="not-uuid")


def test_scope_query_chunk_and_generation_limits():
    c = contracts()
    llm = importlib.import_module("app.llm.contracts")
    locator = c.SourceLocator(source_id=uuid4(), source_version=1)
    ids = (uuid4(),)
    scope = c.AuthorizedScope(dataset_ids=ids)
    assert c.AuthorizedScope.model_validate_json(scope.model_dump_json()) == scope
    for ids in ((), tuple(uuid4() for _ in range(10001))):
        with pytest.raises(ValidationError): c.AuthorizedScope(dataset_ids=ids)
    assert len(c.AuthorizedScope(dataset_ids=tuple(uuid4() for _ in range(10000))).dataset_ids) == 10000
    for length in (1,8000):
        assert c.RetrievalRequest(query="x"*length,scope=scope).query == "x"*length
    for length in (0,8001):
        with pytest.raises(ValidationError): c.RetrievalRequest(query="x"*length,scope=scope)
    for length in (1,32000):
        assert c.EvidenceChunk(dataset_id=scope.dataset_ids[0],locator=locator,text="x"*length).text == "x"*length
    for length in (0,32001):
        with pytest.raises(ValidationError): c.EvidenceChunk(dataset_id=scope.dataset_ids[0],locator=locator,text="x"*length)
    evidence = c.EvidenceChunk(dataset_id=scope.dataset_ids[0],locator=locator,text="Selected evidence")
    request = llm.GenerationRequest(question="Why?", evidence=(evidence,))
    assert llm.GenerationRequest.model_validate_json(request.model_dump_json()) == request
    for size in (0,101):
        with pytest.raises(ValidationError): llm.GenerationRequest(question="Why?",evidence=(evidence,)*size)
    assert len(llm.GenerationRequest(question="Why?",evidence=(evidence,)*100).evidence) == 100
    for size in (1,8000):
        assert len(llm.GenerationRequest(question="x"*size,evidence=(evidence,)).question)==size
    for size in (0,8001):
        with pytest.raises(ValidationError): llm.GenerationRequest(question="x"*size,evidence=(evidence,))
    for size in (1,32000):
        assert len(llm.GenerationResult(text="x"*size,citations=(locator,)).text)==size
    for size in (0,32001):
        with pytest.raises(ValidationError): llm.GenerationResult(text="x"*size,citations=(locator,))
    for size in (1,100):
        assert len(llm.GenerationResult(text="Result",citations=(locator,)*size).citations)==size
    for size in (0,101):
        with pytest.raises(ValidationError): llm.GenerationResult(text="Result",citations=(locator,)*size)
    with pytest.raises(ValidationError): c.SourceLocator(source_id=uuid4(),source_version=1,unknown=True)


def test_rag_retriever_receives_scope_not_role():
    c = contracts()
    assert "scope" in c.RetrievalRequest.model_fields and "role" not in c.RetrievalRequest.model_fields
    for name in ("Parser", "Chunker", "EmbeddingProvider", "Retriever"):
        assert getattr(c,name)._is_protocol
    assert importlib.import_module("app.llm.contracts").LLMProvider._is_protocol
