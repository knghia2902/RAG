import base64
import os
import tempfile
from unittest.mock import MagicMock
from uuid import uuid4
import pytest
from app.llm.citation_verifier import CitationVerifier
from app.llm.contracts import GenerationRequest
from app.providers.gemini_llm import GeminiLLMAdapter
from app.providers.openai_llm import OpenAILLMAdapter
from app.rag.contracts import EvidenceChunk, SourceLocator
from app.rag.retrieval import enrich_chunks_with_images, extract_representative_images


def test_prepare_multimodal_images_base64_conversion():
    """Kiểm tra việc chuyển đổi ảnh từ storage_path hoặc base64 có sẵn sang payload base64 chuẩn."""
    adapter = OpenAILLMAdapter(api_key="fake-key")

    # 1. Ảnh có sẵn base64 data
    img1 = {
        "image_id": str(uuid4()),
        "mime_type": "image/png",
        "b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "caption": "Sơ đồ luồng 1",
        "api_url": "/api/v1/datasets/d1/sources/s1/images/img1",
    }

    # 2. Ảnh từ file vật lý trên đĩa
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(b"PNG_FAKE_RAW_BYTES_TEST")
        tmp_path = tmp.name

    try:
        img2 = {
            "image_id": str(uuid4()),
            "mime_type": "image/png",
            "storage_path": tmp_path,
            "caption": "Sơ đồ kiến trúc 2",
            "api_url": "/api/v1/datasets/d1/sources/s1/images/img2",
        }

        prepared = adapter.prepare_multimodal_images([img1, img2])
        assert len(prepared) == 2
        assert prepared[0]["b64"] == img1["b64"]
        assert prepared[0]["caption"] == "Sơ đồ luồng 1"
        assert prepared[1]["b64"] == base64.b64encode(b"PNG_FAKE_RAW_BYTES_TEST").decode("utf-8")
        assert prepared[1]["caption"] == "Sơ đồ kiến trúc 2"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_multimodal_image_limit_enforced_to_max_3():
    """Kiểm tra giới hạn tối đa 3 ảnh/request để bảo vệ token budget và latency (T-07-04)."""
    adapter = GeminiLLMAdapter(api_key="fake-gemini-key")

    # Tạo 5 ảnh giả lập
    images = [
        {
            "image_id": str(uuid4()),
            "mime_type": "image/png",
            "b64": f"b64_image_{i}",
            "caption": f"Ảnh {i}",
            "api_url": f"/api/v1/datasets/d/sources/s/images/{i}",
        }
        for i in range(1, 6)
    ]

    prepared = adapter.prepare_multimodal_images(images)
    assert len(prepared) == 3
    assert [p["caption"] for p in prepared] == ["Ảnh 1", "Ảnh 2", "Ảnh 3"]


def test_build_multimodal_messages_structure():
    """Kiểm tra cấu trúc tin nhắn Gemini Multimodal Vision: system prompt và inline image_url base64 parts."""
    adapter = GeminiLLMAdapter(api_key="fake-gemini-key")
    src_id = uuid4()
    ds_id = uuid4()

    loc = SourceLocator(source_id=src_id, source_version=1, page=2)
    chunk = EvidenceChunk(
        dataset_id=ds_id,
        locator=loc,
        text="Quy trình đấu nối cổng quang Switch SW-01 theo sơ đồ.",
    )

    img = {
        "image_id": str(uuid4()),
        "mime_type": "image/jpeg",
        "b64": "/9j/4AAQSkZJRg==",
        "caption": "Sơ đồ đấu nối Switch",
        "api_url": f"/api/v1/datasets/{ds_id}/sources/{src_id}/images/img-01",
    }

    messages = adapter.build_multimodal_messages(
        question="Cách đấu nối cổng quang Switch SW-01 như thế nào?",
        evidence=[chunk],
        images=[img],
    )

    assert len(messages) == 2
    system_msg = messages[0]
    user_msg = messages[1]

    # Kiểm tra system prompt hướng dẫn trích dẫn ảnh
    assert system_msg["role"] == "system"
    assert "Markdown: ![Mô tả ảnh](IMAGE_API_URL)" in system_msg["content"]

    # Kiểm tra user content dạng multimodal array
    assert user_msg["role"] == "user"
    assert isinstance(user_msg["content"], list)
    assert len(user_msg["content"]) == 2

    # Phần 1 là text
    text_part = user_msg["content"][0]
    assert text_part["type"] == "text"
    assert "Quy trình đấu nối cổng quang" in text_part["text"]
    assert "Sơ đồ đấu nối Switch" in text_part["text"]
    assert f"/api/v1/datasets/{ds_id}/sources/{src_id}/images/img-01" in text_part["text"]

    # Phần 2 là image_url với base64
    img_part = user_msg["content"][1]
    assert img_part["type"] == "image_url"
    assert img_part["image_url"]["url"] == "data:image/jpeg;base64,/9j/4AAQSkZJRg=="


def test_build_multimodal_messages_without_images_fallback():
    """Kiểm tra khi không có ảnh thì user content trả về dạng chuỗi văn bản thông thường."""
    adapter = OpenAILLMAdapter(api_key="fake-key")
    loc = SourceLocator(source_id=uuid4(), source_version=1)
    chunk = EvidenceChunk(
        dataset_id=uuid4(),
        locator=loc,
        text="Thông tin cấu hình dịch vụ WMS.",
    )

    messages = adapter.build_multimodal_messages(
        question="Cấu hình WMS ra sao?",
        evidence=[chunk],
        images=None,
    )

    assert len(messages) == 2
    assert isinstance(messages[1]["content"], str)
    assert "Thông tin cấu hình dịch vụ WMS" in messages[1]["content"]


def test_gemini_generate_passes_multimodal_payload():
    """Kiểm tra hàm generate của GeminiLLMAdapter truyền đúng messages multimodal tới OpenAI-compatible API."""
    adapter = GeminiLLMAdapter(api_key="fake-key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "Dựa trên sơ đồ [1], các cổng quang cần cắm vào module SFP+ 10Gbps.\n\n"
        "![Sơ đồ kết nối](/api/v1/datasets/d1/sources/s1/images/img-01)"
    )
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    adapter._client = mock_client

    src_id = uuid4()
    loc = SourceLocator(source_id=src_id, source_version=1, page=1)
    chunk = EvidenceChunk(
        dataset_id=uuid4(),
        locator=loc,
        text="Hướng dẫn cắm cổng quang module SFP+.",
    )
    img = {
        "image_id": "img-01",
        "mime_type": "image/png",
        "b64": "abc123base64",
        "caption": "Sơ đồ kết nối",
        "api_url": "/api/v1/datasets/d1/sources/s1/images/img-01",
    }

    result = adapter.generate_grounded_answer(
        question="Cắm cổng quang thế nào?",
        evidence=[chunk],
        images=[img],
    )

    assert "![Sơ đồ kết nối](/api/v1/datasets/d1/sources/s1/images/img-01)" in result.text
    assert len(result.citations) == 1
    assert result.citations[0].source_id == src_id

    # Kiểm tra lời gọi API
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gemini-flash-lite-latest"
    assert len(call_kwargs["messages"]) == 2
    user_payload = call_kwargs["messages"][1]["content"]
    assert isinstance(user_payload, list)
    assert user_payload[1]["type"] == "image_url"


def test_citation_verifier_preserves_markdown_image_links():
    """Kiểm tra CitationVerifier không làm hỏng cú pháp Markdown image links khi làm sạch trích dẫn văn bản."""
    loc = SourceLocator(source_id=uuid4(), source_version=1)
    chunk = EvidenceChunk(
        dataset_id=uuid4(),
        locator=loc,
        text="Hướng dẫn cấu hình địa chỉ IP máy chủ.",
    )

    raw_ai_text = (
        "Địa chỉ IP máy chủ được đặt tĩnh theo bước [1]. "
        "Chi tiết giao diện cấu hình như hình bên dưới:\n\n"
        "![Màn hình cấu hình mạng](/api/v1/datasets/d1/sources/s1/images/img-999)"
    )

    sanitized, citations = CitationVerifier.verify_citations(
        raw_answer=raw_ai_text,
        evidence=[chunk],
    )

    assert "[1]" in sanitized
    assert "![Màn hình cấu hình mạng](/api/v1/datasets/d1/sources/s1/images/img-999)" in sanitized
    assert len(citations) == 1


def test_enrich_chunks_with_images_and_representative_selection():
    """Kiểm tra làm giàu chunks với ảnh trích xuất và chọn top ảnh đại diện."""
    ds_id = uuid4()
    src_id = uuid4()
    loc1 = SourceLocator(source_id=src_id, source_version=1, page=3)
    loc2 = SourceLocator(source_id=src_id, source_version=1, page=5)

    chunk1 = EvidenceChunk(dataset_id=ds_id, locator=loc1, text="Nội dung trang 3")
    chunk2 = EvidenceChunk(dataset_id=ds_id, locator=loc2, text="Nội dung trang 5")

    def mock_lookup(dataset, source, version, page):
        if page == 3:
            return [{
                "image_id": "img-page-3",
                "storage_path": "/path/3.png",
                "mime_type": "image/png",
                "caption": "Hình ảnh trang 3",
                "api_url": f"/api/v1/datasets/{dataset}/sources/{source}/images/img-page-3",
            }]
        elif page == 5:
            return [{
                "image_id": "img-page-5",
                "storage_path": "/path/5.png",
                "mime_type": "image/png",
                "caption": "Hình ảnh trang 5",
                "api_url": f"/api/v1/datasets/{dataset}/sources/{source}/images/img-page-5",
            }]
        return []

    enriched = enrich_chunks_with_images(
        chunks=[chunk1, chunk2],
        image_lookup_fn=mock_lookup,
    )

    assert len(enriched) == 2
    assert len(enriched[0].images) == 1
    assert enriched[0].images[0]["image_id"] == "img-page-3"
    assert len(enriched[1].images) == 1
    assert enriched[1].images[0]["image_id"] == "img-page-5"

    # Chọn top ảnh đại diện
    representative = extract_representative_images(enriched, max_images=3)
    assert len(representative) == 2
    assert representative[0]["image_id"] == "img-page-3"
    assert representative[1]["image_id"] == "img-page-5"
