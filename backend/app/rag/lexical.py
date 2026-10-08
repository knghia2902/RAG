import re
from typing import Sequence

# Regex patterns for logistics and IT system identifiers per RAG-02
ORDER_ID_PATTERN = re.compile(r"\b([A-Z]{2,4}\d{3,8})\b", re.IGNORECASE)
ERROR_CODE_PATTERN = re.compile(r"\b((?:ERR|HTTP|STATUS)[-_]?\d{3,5})\b", re.IGNORECASE)
UUID_PATTERN = re.compile(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", re.IGNORECASE)
TRACKING_PATTERN = re.compile(r"\b((?:TRK|LOG|SO|PO)[-_][A-Z0-9]+)\b", re.IGNORECASE)


def extract_identifiers(query: str) -> list[str]:
    """Trích xuất danh sách các mã định danh chính xác từ câu hỏi.
    Ví dụ: 'DH001', 'ERR-502', UUID, tracking codes.
    """
    if not query:
        return []

    found = []
    for pattern in (ORDER_ID_PATTERN, ERROR_CODE_PATTERN, UUID_PATTERN, TRACKING_PATTERN):
        matches = pattern.findall(query)
        for m in matches:
            if m.upper() not in [x.upper() for x in found]:
                found.append(m)
    return found


def is_exact_match(text: str, identifier: str) -> bool:
    """Kiểm tra xem text có chứa đúng mã identifier với ranh giới từ phân tách hay không.
    Đảm bảo 'DH001' không khớp nhầm 'DH010' hoặc 'DH0011'.
    """
    if not text or not identifier:
        return False

    escaped = re.escape(identifier)
    pattern = rf"(?i)(?:\b|(?<=[^a-zA-Z0-9]))({escaped})(?:\b|(?=[^a-zA-Z0-9]))"
    return bool(re.search(pattern, text))


class LexicalMatcher:
    """Động cơ phát hiện và đối sánh chính xác mã định danh logistics/IT (RAG-02)."""

    def extract_identifiers(self, query: str) -> list[str]:
        return extract_identifiers(query)

    def is_exact_match(self, text: str, identifier: str) -> bool:
        return is_exact_match(text, identifier)

