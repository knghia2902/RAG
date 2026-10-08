from typing import Sequence
from app.rag.contracts import EvidenceChunk

SYSTEM_PROMPT = """Bạn là trợ lý phân tích tri thức và sự cố logistics chuyên nghiệp.
Nhiệm vụ của bạn là trả lời câu hỏi của kỹ thuật viên dựa CHÍNH XÁC trên các đoạn bằng chứng được cung cấp.

QUY TẮC CỐT LÕI:
1. BẰNG CHỨNG XÁC THỰC: Chỉ khẳng định các thông tin có bằng chứng trực tiếp trong các đoạn [Bằng chứng 1], [Bằng chứng 2],... bên dưới.
2. TRÍCH DẪN NGUỒN: Đặt số thứ tự trích dẫn trong ngoặc vuông (ví dụ: [1], [2]) ngay sau khẳng định, dữ kiện hoặc số liệu được trích xuất.
3. THIẾU DỮ LIỆU: Nếu các đoạn bằng chứng không chứa thông tin hoặc không đủ cơ sở để trả lời chắc chắn, bạn BẮT BUỘC phải nói rõ: "Không đủ dữ liệu xác thực để kết luận...", và liệt kê cụ thể các dữ liệu/thông tin còn thiếu. Tuyệt đối không tự suy diễn hoặc bịa đặt.
4. MÂU THUẪN NGUỒN: Nếu phát hiện sự mâu thuẫn giữa các bằng chứng (ví dụ: một nguồn báo hoàn thành, một nguồn báo thất bại), bạn BẮT BUỘC phải chỉ ra: "Phát hiện mâu thuẫn giữa các nguồn: [A] ghi nhận... trong khi [B] ghi nhận...".
5. PHÂN BIỆT RÕ RÀNG: Phân biệt rõ giữa sự kiện quan sát thực tế (observation), tiền lệ (precedent) và giả thuyết (hypothesis). Không bao giờ coi giả thuyết là nguyên nhân đã xác nhận.
"""


def build_evidence_context(evidence: Sequence[EvidenceChunk], max_tokens: int = 4000) -> str:
    """Định dạng danh sách EvidenceChunk thành các khối bằng chứng đánh số,

    đồng thời cắt tỉa theo ngân sách token/ký tự (SYS-03).
    Quy đổi an toàn: 1 token tiếng Việt ≈ 3 ký tự.
    """
    max_chars = max_tokens * 3
    blocks = []
    current_chars = 0

    for idx, chunk in enumerate(evidence, start=1):
        locator_desc = []
        loc = chunk.locator
        if loc.page:
            locator_desc.append(f"Trang {loc.page}")
        if loc.sheet:
            locator_desc.append(f"Sheet {loc.sheet}")
        if loc.row:
            locator_desc.append(f"Hàng {loc.row}")
        if loc.line_start:
            locator_desc.append(f"Dòng {loc.line_start}")
        if loc.json_path:
            locator_desc.append(f"Path {loc.json_path}")

        loc_str = f" ({', '.join(locator_desc)})" if locator_desc else ""
        header = f"[Bằng chứng {idx}]{loc_str}:"
        text = chunk.text.strip()
        block = f"{header}\n{text}\n"

        if current_chars + len(block) > max_chars and blocks:
            # Ngân sách đầy, dừng thêm chunk tiếp theo
            break

        blocks.append(block)
        current_chars += len(block)

    return "\n".join(blocks)


def build_user_prompt(question: str, evidence: Sequence[EvidenceChunk], max_tokens: int = 4000) -> str:
    """Tạo user prompt tiếng Việt đóng khung các bằng chứng và câu hỏi của kỹ thuật viên."""
    evidence_text = build_evidence_context(evidence, max_tokens=max_tokens)
    if not evidence_text:
        return (
            f"Câu hỏi của kỹ thuật viên: {question}\n\n"
            f"[Không tìm thấy đoạn bằng chứng nào trong phạm vi dữ liệu được cấp quyền]. "
            f"Hãy giải thích rõ ràng việc thiếu dữ liệu này."
        )

    return (
        f"Dưới đây là các đoạn bằng chứng được truy xuất từ tài liệu đã cấp quyền:\n\n"
        f"--- BẮT ĐẦU BẰNG CHỨNG ---\n"
        f"{evidence_text}\n"
        f"--- KẾT THÚC BẰNG CHỨNG ---\n\n"
        f"Câu hỏi của kỹ thuật viên: {question}\n\n"
        f"Hãy trả lời chi tiết, tuân thủ nghiêm ngặt các quy tắc trích dẫn [n], "
        f"chỉ rõ nếu có điểm thiếu dữ liệu hoặc có mâu thuẫn giữa các nguồn."
    )
