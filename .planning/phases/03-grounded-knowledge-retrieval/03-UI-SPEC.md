---
phase: "03"
slug: "grounded-knowledge-retrieval"
status: approved
shadcn_initialized: false
preset: none
created: "2026-10-08"
reviewed_at: "2026-10-08"
---

# Phase 03 — UI Design Contract

> Hợp đồng trực quan và tương tác cho luồng Hỏi - Đáp tri thức có trích dẫn (Grounded Knowledge Retrieval) trong môi trường logistics. Giao diện tiếng Việt, kế thừa khung workspace Phase 1 và styling Phase 2.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — dùng CSS và HTML hiện có |
| Preset | not applicable |
| Component library | none |
| Icon library | none — không thêm bộ icon bên ngoài |
| Font | Arial, Helvetica, sans-serif (globals.css) |

Toàn bộ giao diện kế thừa layout workspace sẵn có: sidebar điều hướng bên trái (`#16394b`), vùng nội dung chính (`.main`, nền `#f3f6f8`), card nền trắng (`#ffffff`), các thẻ HTML native (`button`, `input`, `select`, `textarea`, `dialog`, `aside`, `article`, `section`), cùng các class hiện hữu `card`, `empty`, `muted`, `error`, `status`. Tuyệt đối không cài thêm thư viện UI bên ngoài hoặc bộ icon phụ thuộc.

### Contract Basis

| Source | Decisions used |
|--------|----------------|
| `03-CONTEXT.md` | D-01: Bố cục 2 cột (hội thoại + panel xem trước bằng chứng trích dẫn); D-02: Lịch sử phiên chat (`chat_sessions`, `chat_messages`); D-03: Bộ lọc phạm vi truy xuất tùy chọn; D-04: Cảnh báo trực quan màu vàng khi thiếu dữ liệu hoặc mâu thuẫn; D-05: Kiểm tra quyền thời gian thực (Live Scope Recheck) với thông báo thu hồi quyền; D-06: Token budget & secret masking. |
| `02-UI-SPEC.md` | Hệ thống thang đo khoảng cách (bội số của 4), bảng 4 cỡ chữ, 2 độ đậm, bảng màu 60/30/10 với màu nhấn `#075b79`, màu cảnh báo `#b45309`, màu lỗi `#a22a28`. Định dạng tọa độ provenance (Trang, Dòng, Sheet/Hàng, JSON path). |
| `01-CONTEXT.md` | Khung điều hướng vai trò Admin/Kỹ thuật viên, cơ chế phiên đăng nhập và bảo mật dataset ACL. |
| `03-RESEARCH.md` | Hybrid retrieval (lexical exact identifier match + pgvector dense cosine search), trích dẫn đánh số `[1]`, `[2]`, phân trang tin nhắn và phản hồi streaming/tiến trình. |

---

## Phase Boundary

Contract bao gồm:
1. Màn hình Hỏi - Đáp (`/chat`) cho cả Quản trị viên và Kỹ thuật viên:
   - Danh sách phiên hỏi đáp (lịch sử chat) và nút tạo cuộc trò chuyện mới.
   - Khung hội thoại chính với hiển thị tin nhắn người dùng và câu trả lời của AI.
   - Thẻ trích dẫn nguồn đánh số dạng pill `[1]`, `[2]` trong nội dung trả lời.
   - Panel xem trước bằng chứng nguồn (Evidence Preview Panel) bên phải khi click vào thẻ trích dẫn, hiển thị đoạn trích nguyên bản, `logical_filename`, version `v{n}`, tên dataset và tọa độ định vị (Page, Line, Sheet/Row, JSON path).
   - Thanh bộ lọc phạm vi tùy chọn (Scope Filters: Dataset, hồ sơ nguồn, khoảng thời gian) ở đầu phiên chat.
   - Huy hiệu/banner cảnh báo trực quan màu vàng cho các trường hợp thiếu dữ liệu xác thực hoặc mâu thuẫn giữa các nguồn tài liệu (RAG-05).
   - Xử lý lỗi thu hồi quyền truy cập (Live Scope Recheck) khi click citation hoặc tải tin nhắn cũ.
2. Màn hình Cấu hình mô hình (`/configuration` tab Model Settings cho Admin):
   - Xem thông tin Embedding Model (tên model, dimension 1536, index version) và LLM Generation Model.
   - Trạng thái cấu hình API key/Provider.

Không bao gồm trong Phase 3:
- Phân tích chuyên sâu sự cố WMS/TMS và ticket IT (thuộc Phase 4).
- Tạo và xuất báo cáo sự cố định kỳ ra file PDF (thuộc Phase 5).
- Tự động gọi external tool / AI Agent / MCP thực hiện thao tác trên hệ thống logistics thực tế.
- Bộ quét nhận dạng quang học OCR cho tài liệu scan.

---

## Layout and Interaction Contract

### 1. Điều hướng và Phân quyền (Navigation & Roles)
- Thêm mục `Hỏi đáp tri thức` (`/chat`) vào thanh sidebar cho cả Quản trị viên và Kỹ thuật viên.
- Admin có thêm tab/mục quản lý cấu hình mô hình tại `/configuration`.
- Kỹ thuật viên chỉ truy xuất và xem trước trích dẫn từ các Dataset được gán quyền hợp lệ.

### 2. Quản lý Phiên hỏi đáp (Chat Session Sidebar / List)
- Đặt ở cột phụ bên trái khung chat (hoặc menu trượt trên mobile), rộng 260px:
  - Header: Nút CTA `Tạo cuộc trò chuyện mới` (Primary CTA).
  - Danh sách các phiên trò chuyện sắp xếp theo thời gian cập nhật gần nhất.
  - Mỗi mục hiển thị tiêu đề tóm tắt (tự sinh từ câu hỏi đầu tiên, tối đa 40 ký tự) và thời gian (ví dụ: `Hôm nay`, `Hôm qua`, `08/10/2026`).
  - Đánh dấu rõ phiên đang mở (`aria-current="true"`, viền trái accent `#075b79`).
  - Thao tác xóa phiên: Nút nhỏ `Xóa cuộc trò chuyện` (kèm xác nhận hủy an toàn).

### 3. Bố cục 2 Cột Hỏi - Đáp (Two-Column Layout)
- **Trên màn hình desktop (>900px):**
  - Cột chính (65% chiều rộng): Luồng hội thoại gồm thanh bộ lọc phạm vi ở trên, danh sách tin nhắn ở giữa, và hộp nhập câu hỏi neo ở đáy.
  - Cột phụ bên phải (35% chiều rộng, min 360px): Panel xem trước bằng chứng nguồn (Evidence Preview Panel). Mặc định đóng hoặc hiển thị placeholder gợi ý; tự động mở rộng khi người dùng bấm vào một thẻ trích dẫn `[1]`, `[2]`.
- **Trên màn hình nhỏ / tablet (<900px):**
  - Luồng hội thoại chiếm toàn màn hình (100%).
  - Evidence Preview Panel chuyển thành ngăn kéo trượt (drawer) hoặc modal nổi chiếm 90-100% chiều rộng với nút `Đóng xem trước` rõ ràng ở góc trên bên phải.

### 4. Luồng Hội thoại & Hiển thị Tin nhắn (Chat Stream & Bubbles)
- Tin nhắn Người dùng: Căn phải hoặc có nền `#e9f3f8`, viền `#d7e1e8`, nhãn `Bạn`.
- Tin nhắn AI (Hệ thống): Căn trái, nền `#ffffff`, viền `#d7e1e8`, nhãn `Trợ lý tri thức Logistics`.
- Thẻ trích dẫn (Citation Pills):
  - Định dạng: `[1]`, `[2]`, `[3]` đặt ngay sau câu khẳng định hoặc kết luận.
  - Trực quan: Nền nhạt `#e9f3f8`, chữ `#075b79`, viền `#8195a4`, bo tròn 4px, font-weight bold (700), kích thước 12px.
  - Tương tác: Hiển thị tooltip tiêu đề tệp khi rê chuột (`title="{logical_filename} · v{n}"`); khi nhấp chuột sẽ kích hoạt mở Evidence Preview Panel và highlight đoạn tương ứng. Focus ring rõ ràng (`:focus-visible`).
- Huy hiệu/Banner Cảnh báo Trực quan (Uncertainty & Conflict Indicators - RAG-05):
  - Khi câu trả lời phát hiện thiếu dữ liệu hoặc mâu thuẫn:
    - Hiển thị banner cảnh báo màu vàng ở đầu bong bóng tin nhắn:
      - Thiếu dữ liệu: `⚠ Cảnh báo: Thiếu dữ liệu xác thực cho một số nội dung.`
      - Mâu thuẫn: `⚠ Cảnh báo: Phát hiện mâu thuẫn giữa các nguồn tài liệu trích dẫn.`
    - Màu sắc banner: Nền `#fef3c7`, viền `#fcd34d`, chữ `#b45309`, cỡ chữ 12px, padding 8px 12px, bo góc 4px.

### 5. Thanh Bộ lọc Phạm vi Truy xuất (Scope Filter Bar)
- Vị trí: Đặt ở trên cùng của khung hội thoại, có nút thu gọn/mở rộng `Bộ lọc phạm vi (Tất cả)` / `Đóng bộ lọc`.
- Các trường lọc:
  - `Dataset`: Dropdown chọn một dataset cụ thể hoặc `Tất cả dataset được cấp quyền`.
  - `Loại tài liệu`: Dropdown chọn `Tất cả hồ sơ`, `Quy trình SOP`, `Nhật ký Log`, `Phiếu Ticket`, `Bảng vận hành`.
  - `Khoảng thời gian`: 2 ô nhập ngày `Từ ngày` và `Đến ngày`.
- Mặc định: Thu gọn; tìm kiếm trên toàn bộ dữ liệu người dùng có quyền.

### 6. Panel Xem trước Bằng chứng Nguồn (Evidence Preview Panel)
- Header:
  - Tiêu đề: `Bằng chứng trích dẫn [{số thứ tự}]`
  - Nút đóng: `Đóng xem trước` (hoặc biểu tượng `✕` có nhãn `aria-label="Đóng bảng trích dẫn"`).
- Metadata nguồn:
  - Tên tệp: `logical_filename` (cắt tỉa an toàn, xuống dòng nếu dài).
  - Phiên bản: Huy hiệu `v{n} · đang dùng` màu accent.
  - Dataset: Tên dataset chứa nguồn.
  - Tọa độ Provenance (Locator Badge):
    - PDF: `Trang: {page}` (hoặc `Mục: {section}`)
    - TXT / Log: `Dòng: {line_start} - {line_end}`
    - Excel / CSV: `Sheet: {sheet}, Hàng: {row}`
    - JSON / JSONL: `Đường dẫn JSON: {json_path}`
- Nội dung trích dẫn (Excerpt Content):
  - Khối chứa văn bản trích dẫn nguyên bản, có thanh cuộn dọc riêng biệt, font chữ rõ ràng, giữ nguyên ngắt dòng (`white-space: pre-wrap`), nền `#f8fafc`, viền `#e2e8f0`, padding 12px.
  - Tuyệt đối không hiển thị đường dẫn tệp nội bộ của server, bucket URL hay credential bí mật.

### 7. Kiểm tra Quyền Thời gian thực (Live Scope Recheck - D-05)
- Khi người dùng bấm vào một thẻ citation cũ hoặc mở lại lịch sử chat:
  - Backend thực hiện kiểm tra quyền tức thời đối với dataset của nguồn đó (`recheck_response`).
  - Nếu quyền đã bị thu hồi hoặc nguồn đã bị tombstone/xóa:
    - Panel trích dẫn không trả về văn bản trích dẫn và tọa độ chi tiết.
    - Hiển thị thông báo cảnh báo an toàn: `Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi. Liên hệ Quản trị viên để được cấp lại quyền.` với `role="alert"`, màu `#a22a28`.

### 8. Hộp Nhập Câu hỏi (Chat Input Area)
- Ô nhập: `textarea` co giãn tự động hoặc cố định chiều cao (tối thiểu 44px), viền `#8195a4`, placeholder: `Nhập câu hỏi bằng tiếng Việt về quy trình, log, ticket, sự cố...`
- Nút bấm: `Gửi câu hỏi` (Primary CTA, nền `#075b79`, chữ trắng).
  - Trạng thái vô hiệu hóa (disabled): Khi ô nhập chỉ có khoảng trắng hoặc khi đang chờ hệ thống trả lời.
- Trạng thái chờ xử lý:
  - Hiển thị dòng thông báo trạng thái `Đang truy xuất và tổng hợp câu trả lời...` với `role="status"`.

---

## Spacing Scale

Declared values (bội số của 4 theo chuẩn thiết kế):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Khoảng cách inline, thẻ citation pill, padding huy hiệu tọa độ |
| sm | 8px | Khoảng cách giữa các control nhỏ, padding nút, margin nhãn |
| md | 16px | Khoảng cách mặc định giữa các khối tin nhắn, padding ô nhập |
| lg | 24px | Padding card hội thoại, padding Evidence Preview Panel |
| xl | 32px | Khoảng cách tách biệt giữa các khu vực layout chính |
| 2xl | 48px | Khoảng đệm cho trạng thái rỗng (empty state) |
| 3xl | 64px | Khoảng cách cấp trang khi mở rộng |

Exceptions:
- Vùng nội dung chính desktop giữ `padding: 40px` và mobile giữ `padding: 16px` từ khung shell Phase 1.
- Mọi thành phần tương tác (nút bấm, ô nhập, thẻ trích dẫn) duy trì chiều cao chạm tối thiểu 44px (hoặc vùng bấm tối thiểu 44x44px cho mobile).

---

## Typography

Chỉ sử dụng 4 cỡ chữ và 2 độ đậm chuẩn theo hệ thống hiện hữu:

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16px | regular (400) | 1.5 |
| Label / metadata / citation | 12px | bold (700) | 1.5 |
| Section heading | 20px | bold (700) | 1.2 |
| Page heading | 28px | bold (700) | 1.2 |

Quy tắc font:
- Font chữ: `Arial, Helvetica, sans-serif` từ `globals.css`.
- Trọng số font: Chỉ sử dụng `400` (regular) cho văn bản nội dung tin nhắn và `700` (bold) cho tiêu đề, nhãn metadata, citation pills và nút bấm quan trọng.

---

## Color

Tỷ lệ thị giác 60/30/10:

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#f3f6f8` | Nền canvas, nền trang chat và vùng làm việc chính |
| Secondary (30%) | `#ffffff` | Khung card chat, bong bóng tin nhắn trợ lý, bề mặt Evidence Preview Panel, thanh nhập liệu |
| Accent (10%) | `#075b79` | Thẻ citation pill `[1]`, nút CTA `Gửi câu hỏi`, `Tạo cuộc trò chuyện mới`, viền phiên chat đang chọn, nhãn version `v{n}` |
| Destructive | `#a22a28` | Nút `Xóa cuộc trò chuyện`, thông báo lỗi từ chối quyền truy cập `role="alert"` |
| Warning (Semantic) | `#b45309` | Huy hiệu/banner cảnh báo thiếu dữ liệu hoặc mâu thuẫn nguồn (nền `#fef3c7`, viền `#fcd34d`) |

Accent reserved for:
- Nút CTA chính `Gửi câu hỏi`
- Nút `Tạo cuộc trò chuyện mới`
- Thẻ trích dẫn citation pills `[1]`, `[2]`
- Viền đánh dấu phiên chat hiện tại (`aria-current="true"`)
- Nhãn phiên bản active `v{n} · đang dùng`
- Vòng focus hỗ trợ bàn phím (`outline: 3px solid #dc8f21`)

Các nút phụ (Đóng xem trước, Hủy, Thu gọn bộ lọc) sử dụng viền xám `#8195a4` hoặc nền trong suốt, không dùng màu nhấn.

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | `Gửi câu hỏi` |
| New chat CTA | `Tạo cuộc trò chuyện mới` |
| Close preview | `Đóng xem trước` |
| Empty chat stream heading | `Bắt đầu tra cứu tri thức` |
| Empty chat stream body | `Nhập câu hỏi bằng tiếng Việt để tìm kiếm quy trình SOP, nhật ký log, ticket hoặc dữ liệu vận hành từ các Dataset được cấp quyền.` |
| Empty sessions heading | `Chưa có cuộc trò chuyện` |
| Empty sessions body | `Bấm nút Tạo cuộc trò chuyện mới để bắt đầu phiên hỏi đáp đầu tiên.` |
| Empty evidence preview heading | `Chưa chọn trích dẫn` |
| Empty evidence preview body | `Nhấp vào thẻ trích dẫn số [1], [2] trong câu trả lời của trợ lý để xem đoạn văn bản và tọa độ nguồn tương ứng.` |
| General query error | `Không thể hoàn thành truy xuất do lỗi kết nối hoặc vượt quá giới hạn. Kiểm tra kết nối mạng và thử gửi lại câu hỏi.` |
| Revoked access error | `Quyền truy cập nguồn dữ liệu đã thay đổi hoặc bị thu hồi. Liên hệ Quản trị viên để được cấp lại quyền vào Dataset tương ứng.` |
| Out of scope / no match | `Không tìm thấy bằng chứng liên quan trong các Dataset bạn được cấp quyền. Thử điều chỉnh từ khóa câu hỏi hoặc mở rộng bộ lọc phạm vi.` |
| Destructive confirmation | `Xóa cuộc trò chuyện “{tiêu đề}”? Toàn bộ tin nhắn và trích dẫn trong phiên này sẽ bị xóa và không thể khôi phục.` Nút: `Xóa cuộc trò chuyện` / `Giữ cuộc trò chuyện` |
| Uncertainty warning badge | `Thiếu dữ liệu xác thực cho một số nội dung.` |
| Contradiction warning badge | `Phát hiện mâu thuẫn giữa các nguồn tài liệu trích dẫn.` |

Nhãn trạng thái (Status labels):
- `Đang truy xuất và tổng hợp câu trả lời...`
- `Đang lưu phiên...`
- `Đang tải lịch sử...`
- `v{n} · đang dùng`
- `Phạm vi: Toàn bộ dataset được cấp quyền`

---

## UI Considerations

| Category | Element(s) | Status | Resolution / Reason |
|----------|------------|--------|---------------------|
| empty | Chat stream, session list, evidence panel | ✅ covered | Khởi tạo với heading/body rõ ràng theo bảng Copywriting Contract; hướng dẫn người dùng hành động tiếp theo. |
| loading | Gửi câu hỏi, tải phiên, mở preview | ✅ covered | Dùng `role="status"` thông báo tiếng Việt ("Đang truy xuất và tổng hợp..."), vô hiệu hóa nút gửi, giữ focus bàn phím. |
| error | Lỗi truy xuất, lỗi thu hồi quyền, lỗi API | ✅ covered | Hiển thị inline `role="alert"` màu `#a22a28` kèm giải pháp khắc phục cụ thể; không làm mất lịch sử hội thoại đã có. |
| populated | Chat stream có trích dẫn, panel có locator | ✅ covered | Trình bày rõ ràng bong bóng tin nhắn, citation pills `[1]`, `[2]`, panel hiển thị đầy đủ tên tệp, dataset, locator và văn bản trích dẫn. |
| partial | Thiếu dữ liệu, mâu thuẫn nguồn | ✅ covered | Không giấu nhẹm khi thiếu bằng chứng; hiển thị banner cảnh báo màu vàng `#b45309`/`#fef3c7` và giải thích cụ thể trong văn bản. |
| overflow | Đoạn trích dẫn dài, tin nhắn dài, danh sách phiên | ✅ covered | Container trích dẫn và danh sách phiên có thanh cuộn dọc độc lập (`overflow-y: auto`), không làm vỡ bố cục tổng thể. |
| zero-one-many | Số lượng trích dẫn (0, 1, nhiều) | ✅ covered | Khi không có trích dẫn (câu hỏi tổng quát/thiếu bằng chứng) không hiện pill; khi có 1 hoặc nhiều trích dẫn đánh số liên tục `[1]`, `[2]`. |
| long-text | Tên file dài, câu hỏi dài, JSON path phức tạp | ✅ covered | Tên file và JSON path dài tự động wrap hoặc xuống dòng hợp lý (`word-break: break-word`), không làm tràn ngang viewport. |

---

## Visual Hierarchy & Focal Points

1. **Điểm nhấn thị giác chính (Primary Focal Point):**
   - Khi vào trang mới: Hộp nhập câu hỏi (Chat Input Area) ở chân màn hình và nút CTA `Gửi câu hỏi`.
   - Khi đang đọc câu trả lời: Bong bóng phản hồi của trợ lý với các thẻ trích dẫn màu nổi `[1]`, `[2]` và banner cảnh báo màu vàng nếu có.
2. **Điểm nhấn thị giác phụ (Secondary Focal Point):**
   - Evidence Preview Panel bên phải: Khi người dùng nhấp vào thẻ trích dẫn, panel mở ra làm tiêu điểm kiểm tra tính xác thực.
3. **Thứ bậc điều hướng:**
   - Sidebar cố định bên trái (nhận biết vị trí workspace) → Thanh công cụ lọc phạm vi ở trên → Dòng hội thoại ở giữa → Panel bằng chứng bên phải.
4. **Trợ năng & Bàn phím (Accessibility / ARIA):**
   - Mọi nút bấm icon/rút gọn đều có text hoặc `aria-label` tương ứng (ví dụ: `aria-label="Đóng bảng trích dẫn"`).
   - Thẻ trích dẫn citation có `role="button"` và `aria-haspopup="dialog"`.
   - Trạng thái tải câu trả lời dùng `aria-live="polite"` và `role="status"`.
   - Thông báo lỗi dùng `role="alert"`.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|------------|-------------|
| shadcn official | none | not applicable — Tool: none; `components.json` không tồn tại |
| Third-party registries | none | not applicable — không sử dụng block hoặc registry bên ngoài |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-10-08
