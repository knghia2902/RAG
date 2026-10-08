---
phase: 03-grounded-knowledge-retrieval
plan: "05"
subsystem: chat-api-two-column-ui-and-live-scope-recheck
tags: [chat-api, sessions, live-scope-recheck, two-column-ui, evidence-preview, citations, model-config, tests]
requires: [03-04]
provides:
  - Chat management and query execution REST endpoints (GET/POST/DELETE /api/v1/chat/sessions, POST /api/v1/chat/query) in app.api.chat
  - Live Scope Recheck citation preview endpoint (GET /api/v1/chat/citations/preview) with immediate 403 revocation enforcement (D-05)
  - Next.js two-column Q&A page with chat history, scope filter bar, and yellow uncertainty/conflict banners in frontend/src/app/(workspace)/chat/page.tsx
  - Evidence Preview panel component with format-specific provenance badges in frontend/src/components/EvidencePreview.tsx
  - Sidebar navigation link "Hỏi đáp tri thức" for Admin and Technician roles
  - Admin Model Configuration view on /configuration page (SYS-02)
  - Integration tests for chat API, tenant isolation, and live scope recheck revocation
affects: [04-logistics-incident-and-ticket-analysis]
tech-stack:
  added: []
  patterns: [live scope recheck on citation preview, two-column grounded QA layout, pure HTML/CSS design system, responsive drawer/panel]
key-files:
  created:
    - backend/app/api/chat.py
    - frontend/src/components/EvidencePreview.tsx
    - frontend/src/app/(workspace)/chat/page.tsx
    - backend/tests/integration/test_chat_api.py
    - backend/tests/integration/test_live_scope_recheck.py
    - frontend/tests/e2e/chat-knowledge.spec.ts
  modified:
    - backend/app/api/schemas.py
    - backend/app/main.py
    - backend/app/providers/__init__.py
    - frontend/src/lib/contracts.ts
    - frontend/src/components/Sidebar.tsx
    - frontend/src/app/(workspace)/configuration/page.tsx
key-decisions:
  - "Live Scope Recheck (D-05, T-03-10): Mọi thao tác xem trước citation hoặc tải lịch sử tin nhắn đều kiểm tra lại quyền dataset hiện thời của tài khoản; nếu bị thu hồi, trả về 403 Forbidden và ẩn nội dung trích dẫn."
  - "Bảo vệ cách ly phiên chat (T-03-11): Người dùng chỉ có quyền đọc/xóa các phiên chat do chính mình tạo (ChatSession.account_id == account.id)."
  - "Giao diện tuân thủ 100% 03-UI-SPEC.md và globals.css: bố cục 2 cột, thẻ trích dẫn [1], [2] bấm mở panel bên phải, banner cảnh báo màu vàng khi thiếu dữ liệu hoặc mâu thuẫn, thanh lọc phạm vi tùy chỉnh."
  - "Trang Cấu hình (/configuration) hiển thị đầy đủ thông số model nhúng, dimension 1536, index version và model LLM mà không để lộ secret API key (SYS-02)."
requirements-completed: [RAG-01, RAG-04, RAG-05, SYS-02, SYS-05]
actuals:
  tokens: 48000
  tasks: 3
  commits: 1
duration: 20min
completed: 2026-10-08
status: complete
---

# Phase 3 Plan 05: Chat API, Live Scope Recheck & Two-Column UI Summary

**Hoàn thiện toàn bộ luồng Hỏi - Đáp tri thức đầu cuối (End-to-End Grounded Q&A): xây dựng Chat REST API với kiểm tra quyền thời gian thực (Live Scope Recheck), giao diện Next.js 2 cột hoàn chỉnh theo hợp đồng 03-UI-SPEC.md (hội thoại + panel bằng chứng nguồn, thanh lọc phạm vi, huy hiệu cảnh báo màu vàng), tích hợp điều hướng và màn hình cấu hình model cho Admin.**

## Hoàn thành các nhiệm vụ

### 1. Chat API Endpoints with Live Scope Recheck & Session Persistence (Task 03-05-01)
- Bổ sung DTO vào `backend/app/api/schemas.py`: `ChatSessionDTO`, `ChatMessageDTO`, `ChatQueryRequestDTO`, `ChatQueryResponseDTO`, `CitationPreviewResponseDTO`.
- Tạo router `backend/app/api/chat.py` với các endpoint:
  - `GET /sessions`: Lấy danh sách phiên chat của tài khoản hiện tại.
  - `POST /sessions`: Tạo phiên chat mới.
  - `DELETE /sessions/{session_id}`: Xóa phiên chat (bảo đảm cách ly chủ sở hữu).
  - `GET /sessions/{session_id}/messages`: Lấy lịch sử tin nhắn, tự động lọc bỏ citation của dataset đã mất quyền truy cập.
  - `POST /query`: Thực hiện truy xuất tri thức lai (Hybrid Retrieval) và sinh câu trả lời có trích dẫn qua `GroundedGenerator`.
  - `GET /citations/preview`: Kiểm tra quyền thời gian thực (Live Scope Recheck - D-05); nếu quyền bị thu hồi lập tức trả về 403 Forbidden.
- Đăng ký `chat.router` vào `backend/app/main.py`.
- Viết integration test `backend/tests/integration/test_chat_api.py` và `backend/tests/integration/test_live_scope_recheck.py`.

### 2. Next.js Two-Column Q&A Interface & Evidence Preview Panel (Task 03-05-02)
- Cập nhật `frontend/src/lib/contracts.ts` với các kiểu dữ liệu `ChatSession`, `ChatMessage`, `CitationItem`, `CitationPreviewDetail`, `ChatQueryRequest`, `ModelConfig`.
- Tạo component `frontend/src/components/EvidencePreview.tsx` hiển thị chi tiết tên nguồn, version `v{n}`, dataset, tọa độ provenance (Trang, Dòng, Sheet/Hàng, JSON Path) và đoạn trích nguyên bản.
- Tạo màn hình `frontend/src/app/(workspace)/chat/page.tsx` theo chuẩn thiết kế `03-UI-SPEC.md`:
  - Cột bên trái: Danh sách phiên chat và nút CTA `Tạo cuộc trò chuyện mới`.
  - Cột chính: Thanh bộ lọc phạm vi (Scope Filter), luồng tin nhắn với các banner cảnh báo màu vàng (RAG-05) khi thiếu dữ liệu hoặc có mâu thuẫn, thẻ trích dẫn `[1]`, `[2]`, và ô nhập câu hỏi.
  - Cột bên phải: `EvidencePreview` panel mở ra khi click vào thẻ trích dẫn.

### 3. Sidebar Navigation, Admin Model Configuration UI & End-to-End Verification (Task 03-05-03)
- Cập nhật `frontend/src/components/Sidebar.tsx` bổ sung liên kết `Hỏi đáp tri thức` (`/chat`) cho cả Quản trị viên và Kỹ thuật viên.
- Cập nhật `frontend/src/app/(workspace)/configuration/page.tsx` hiển thị thẻ Cấu hình mô hình AI (Model Configuration) theo SYS-02.
- Viết kịch bản kiểm thử E2E `frontend/tests/e2e/chat-knowledge.spec.ts`.
- Chạy `npm run build`: hoàn thành 100% không lỗi (Turbopack, TypeScript, static page generation).

## Self-Check: PASSED
- `test_module_boundaries.py`: PASSED (14/14 tests).
- Backend unit & integration tests: PASSED.
- `npm run build`: PASSED (exit code 0).
