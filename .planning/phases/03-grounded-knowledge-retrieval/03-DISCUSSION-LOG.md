# Phase 03: Grounded Knowledge Retrieval - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-08  
**Phase:** 03-grounded-knowledge-retrieval  
**Areas discussed:** Trải nghiệm giao diện Hỏi - Đáp & Khung xem đoạn trích dẫn  

---

## 1. Lựa chọn chủ đề thảo luận chính cho Phase 03

| Option | Description | Selected |
|--------|-------------|----------|
| Trải nghiệm giao diện Hỏi - Đáp & Khung xem đoạn trích dẫn | Bố cục giao diện chat/Q&A, tương tác bấm vào citation để xem chi tiết đoạn trích dẫn/metadata, lưu trữ lịch sử phiên hỏi đáp | ✓ |
| Bộ lọc truy xuất & Cơ chế tra cứu mã định danh chính xác | Giao diện thanh lọc theo Dataset/Hệ thống/Thời gian, cơ chế ưu tiên hiển thị bản ghi khớp exact ID như DH001, mã lỗi | |
| Quản lý cấu hình Model & Cơ chế lập chỉ mục lại phía Admin | Giao diện cấu hình API key/model trên trang /configuration, chiến lược re-index toàn bộ dữ liệu qua Celery khi đổi model | |
| Chính sách xử lý khi thiếu thông tin hoặc bằng chứng mâu thuẫn | Hình thức cảnh báo trực quan vs văn bản LLM, ngưỡng similarity tối thiểu và chính sách chặn gọi LLM khi không có bằng chứng | |

**User's choice:** Trải nghiệm giao diện Hỏi - Đáp & Khung xem đoạn trích dẫn.  
**Notes:** Người dùng tập trung làm rõ trải nghiệm tương tác cốt lõi của tính năng Q&A tri thức và xem bằng chứng.

---

## 2. Bố cục màn hình Hỏi - Đáp và tương tác xem đoạn trích dẫn (Citation Preview)

| Option | Description | Selected |
|--------|-------------|----------|
| Bố cục 2 cột (Khuyến nghị) | Cột trái là luồng Hỏi - Đáp (hộp thoại + câu trả lời kèm thẻ citation [1], [2]); Cột phải là Panel chi tiết trích dẫn (mở ngay đoạn text, tên file, tọa độ trang/dòng/JSON khi bấm vào citation) | ✓ |
| Bố cục 1 cột tập trung | Bằng chứng trích dẫn hiển thị dạng thẻ bung mở (accordion) hoặc popover nổi ngay bên dưới câu trả lời của AI | |
| Bố cục 2 tab riêng biệt | Tab "Hỏi đáp tri thức" và Tab "Danh mục tài liệu/Bằng chứng trích dẫn" | |

**User's choice:** Bố cục 2 cột.  
**Notes:** Giúp người dùng vừa theo dõi được mạch câu trả lời, vừa đối chiếu song song văn bản trích dẫn gốc và tọa độ provenance mà không làm ngắt quãng luồng hội thoại.

---

## 3. Cơ chế lưu trữ lịch sử và quản lý phiên hỏi đáp (Chat History & Sessions)

| Option | Description | Selected |
|--------|-------------|----------|
| Lưu phiên theo tài khoản vào database (Khuyến nghị) | Có danh sách phiên trò chuyện để mở lại lịch sử hỏi đáp cũ, có nút "Cuộc trò chuyện mới" và duy trì ngữ cảnh theo phiên | ✓ |
| Phiên hội thoại tạm thời (In-memory/Session State) | Chỉ duy trì lịch sử trong phiên làm việc của trình duyệt, không lưu bền vững vào database khi refresh/đăng xuất | |
| Tra cứu độc lập theo từng lượt (Single-turn Q&A) | Mỗi câu hỏi là một lượt tra cứu độc lập, tập trung hiển thị câu trả lời và bằng chứng, không xâu chuỗi ngữ cảnh đa lượt | |

**User's choice:** Lưu phiên hỏi đáp theo tài khoản vào cơ sở dữ liệu.  
**Notes:** Cung cấp trải nghiệm hỏi đáp hiện đại, cho phép kỹ thuật viên xem lại các câu trả lời và bằng chứng trước đó.

---

## 4. Bộ lọc phạm vi truy xuất (Scope Filters) trên giao diện Hỏi - Đáp

| Option | Description | Selected |
|--------|-------------|----------|
| Mặc định toàn bộ dataset được cấp quyền + thanh bộ lọc tùy chọn (Khuyến nghị) | Mặc định tìm trên toàn bộ dataset được cấp quyền, có thanh bộ lọc tùy chọn (chọn Dataset, loại nguồn SOP/Log/Ticket, khoảng thời gian) có thể mở ra để thu hẹp phạm vi | ✓ |
| Bắt buộc chọn 1 Dataset cụ thể trước khi hỏi đáp | Mỗi cuộc trò chuyện sẽ chỉ giới hạn trong phạm vi 1 dataset đã chọn | |
| Tự động tìm kiếm trên toàn bộ dataset | Không cần thanh bộ lọc thủ công trên giao diện chat | |

**User's choice:** Mặc định tìm trên toàn bộ dataset được cấp quyền, có thanh bộ lọc tùy chọn.  
**Notes:** Linh hoạt cho người dùng: có thể hỏi nhanh câu hỏi tổng thể hoặc lọc sâu vào một dataset/loại nguồn nhất định.

---

## 5. Phản hồi khi thiếu thông tin hoặc bằng chứng mâu thuẫn (RAG-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Kết hợp cả hai (Khuyến nghị) | Câu trả lời của AI nêu rõ giới hạn + có Banner/Huy hiệu cảnh báo trực quan (màu vàng: 'Thiếu dữ liệu xác thực' / 'Phát hiện mâu thuẫn giữa các nguồn') để người dùng dễ nhận biết ngay | ✓ |
| Chỉ thể hiện bằng câu chữ tự nhiên của AI | System prompt yêu cầu AI nêu rõ phần chưa biết/mâu thuẫn, không dùng thêm banner cảnh báo UI riêng | |
| Từ chối sinh câu trả lời nếu không có bằng chứng | Khi độ tương đồng dưới ngưỡng, hệ thống hiển thị thông báo lỗi 'Không tìm thấy tài liệu phù hợp' và không gọi LLM | |

**User's choice:** Kết hợp cả hai.  
**Notes:** Đảm bảo tính trung thực tối đa (groundedness), kỹ thuật viên nhận biết tức thì tình trạng thiếu dữ liệu mà không bị nhầm lẫn giữa suy đoán và bằng chứng thực tế.

---

## the agent's Discretion

- Thiết kế chi tiết bảng lưu trữ lịch sử chat (`chat_sessions`, `chat_messages`, `chat_citations`) và index tìm kiếm.
- Chiến lược kết hợp exact match và dense vector search (hybrid retrieval) để xử lý chính xác `DH001` vs `DH010`.
- Thiết lập Provider adapters (OpenAI vs Fake Provider cho CI/test) và che giấu secret egress trước khi gọi API.

## Deferred Ideas

- Xuất cuộc trò chuyện sang tệp PDF (chuyển sang Phase 5).
- Tự động liên kết cuộc trò chuyện với phân tích Ticket/Sự cố chuyên sâu (chuyển sang Phase 4).
