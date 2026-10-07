---
phase: "02"
slug: "dataset-ingestion-and-source-lifecycle"
status: approved
shadcn_initialized: false
preset: none
created: "2026-10-07"
reviewed_at: "2026-10-07"
---

# Phase 02 — UI Design Contract

> Hợp đồng trực quan và tương tác cho luồng nạp Dataset và quản lý vòng đời nguồn. Giao diện tiếng Việt, kế thừa khung workspace Phase 1 và CSS hiện có.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — dùng CSS và HTML hiện có |
| Preset | not applicable |
| Component library | none |
| Icon library | none — không thêm bộ icon |
| Font | Arial, Helvetica, sans-serif (globals.css) |

Giữ sidebar trái, vùng nội dung chính, bảng danh sách, card và panel bên phải. Bảng màu nền/trạng thái giữ các giá trị hiện hữu trong `frontend/src/app/globals.css`; không đưa thêm hệ thống token hoặc thư viện component. Dùng `button`, `input`, `select`, `table`, `dialog` native và các class `card`, `empty`, `muted`, `error` hiện có. `components.json` không tồn tại; contract này giữ nguyên lựa chọn giao diện thủ công đã có.

### Contract Basis

| Source | Decisions used |
|--------|----------------|
| `02-CONTEXT.md` | D-01–D-10: kết quả riêng theo file, profile chọn tường minh, version bất biến/active, job bền vững, retry, preview có locator, delete tombstone và kiểm tra quyền hiện tại. |
| `01-CONTEXT.md` | Sidebar trái; bảng trong vùng chính; panel tác vụ bên phải; giao diện tiếng Việt; Admin quản lý nguồn, Kỹ thuật viên chỉ xem nguồn thuộc Dataset được cấp. |
| `02-RESEARCH.md` | Preview profile trước xác nhận; lỗi theo row/record/field; parse bất đồng bộ; parsed preview; version active cũ tiếp tục dùng khi version mới chưa đạt; đề xuất five profile baseline. |
| Dataset workspace và `globals.css` | Màu, font, card/bảng, panel `dialog`, trạng thái tải/lỗi, role-based actions và responsive breakpoint 700px hiện có. |

## Phase Boundary

Contract chỉ bao gồm chọn Dataset và profile, chọn nhiều file, preview profile/sample, kết quả từng file, trạng thái/xử lý lỗi, parsed source preview/provenance, retry, reprocess và delete. Không thêm OCR, chat/RAG, embedding, AI/provider controls, ticket/incident analysis, reports, PDF export, scheduler hay thao tác thật trên WMS/TMS. PDF scan được báo lỗi rõ ràng.

## Layout and Interaction Contract

1. **Dataset context:** Thêm vùng Nguồn trong card chi tiết Dataset hiện có. Header thể hiện tên Dataset, số nguồn và nút `Tải tệp lên` cho Admin. Kỹ thuật viên chỉ thấy danh sách và `Xem đoạn trích`; không thấy nút quản trị nguồn.
2. **Upload panel:** Mở native `dialog` dạng panel phải theo pattern hiện có, rộng `min(460px, 100vw)`. Form đi theo thứ tự Dataset → profile → tệp → kiểm tra trước upload. Dùng nút `Hủy tải lên` trước khi gửi; khóa nút này khi đang gửi bytes. Giữ focus trong dialog, trả focus về nút mở sau khi đóng, gắn `aria-labelledby`/`aria-busy`; khi API đã tiếp nhận và trả job ID, có thể đóng panel trong lúc worker tiếp tục.
3. **Profile selection:** Bắt buộc chọn một profile đã công bố trước khi xác nhận; không suy đoán profile từ tên/đuôi file hay header. Hiển thị tên và version profile, format được hỗ trợ, trường bắt buộc/tùy chọn, hướng dẫn mapping/timezone do profile công bố và một mẫu nhỏ đã decode. Baseline tên hiển thị: Tài liệu chung, Log, Ticket, Incident, Bảng vận hành. Profile không khả dụng hoặc không khớp format phải giải thích trước bước xác nhận.
4. **File selection:** Cho chọn nhiều file trong một lần; chấp nhận PDF có text, DOCX, CSV, XLSX, TXT, JSON, JSONL và `.log`. Hiển thị tên, định dạng, kích thước và bỏ file khỏi batch trước xác nhận. Nêu giới hạn kích thước/batch từ cấu hình hệ thống khi đã được công bố; không tự đặt con số trong Web. Sau xác nhận, hiển thị kết quả độc lập từng file.
5. **Source list:** Dùng bảng nằm trong card và cuộn ngang trên màn nhỏ theo pattern `.card { overflow-x:auto }`/`table { min-width:640px }`. Các cột: Tên nguồn, Định dạng/Profile, Version đang dùng, Trạng thái lần xử lý gần nhất, Cập nhật, Thao tác. Có phân trang nếu API trả trang; không tải tràn danh sách. Tên dài được wrap tối đa hai dòng hoặc mở rộng trong chi tiết; không làm tràn bảng.
6. **Version lifecycle:** Mỗi hàng phân biệt rõ version active với lần import/reprocess mới nhất. Khi version mới đang queued/processing/failed, vẫn ghi version active đang dùng và cho phép preview version active. Chỉ khi toàn bộ validation/publish của version mới thành công mới chuyển nhãn active. Checksum trùng trong cùng Dataset hiện kết quả `Nội dung đã tồn tại — không tạo bản sao`, liên kết tới nguồn canonical; nếu tên gửi khác, giữ tên đó như alias trong chi tiết/lịch sử import.
7. **Source preview:** Mở panel phải hoặc dialog theo pattern Phase 1. Chỉ hiện đoạn nội dung đã parse của version active; header cho biết tên nguồn, `v{n} · đang dùng`, profile và locator đúng định dạng: trang/section, sheet/row, JSON record/path, hoặc log event/line. Cho xem thông tin canonical như ID, hệ thống, trạng thái/ưu tiên và timestamp khi profile trả về. Nội dung read-only, giữ xuống dòng và có vùng cuộn; không đưa file gốc, đường dẫn storage hay URL public vào UI.
8. **Errors and warnings:** Mỗi file lỗi có thể mở chi tiết gồm loại lỗi, vị trí row/record, trường và lý do có thể sửa. Lỗi format, file hỏng, PDF scan và lỗi schema bắt buộc hiển thị riêng, không dùng trạng thái thành công. Cảnh báo trường optional hiển thị nhưng không chặn khi profile cho phép. Không hiển thị stack trace, đường dẫn filesystem, nội dung bí mật hoặc chi tiết storage.
9. **Retry and reprocess:** `Thử lại` chỉ xuất hiện với Admin trên job failed; giữ nguyên source/version và trạng thái lỗi cũ cho tới khi attempt mới được ghi nhận. `Nạp lại nguồn` chạy lại cùng version, không tạo version mới; giữ preview active cũ trong thời gian chạy và nếu thất bại. Trạng thái job không mất sau reload/restart. Không cho thao tác tạo bản sao canonical.
10. **Delete:** Admin chọn `Xóa nguồn` sẽ thấy xác nhận cho biết tên nguồn, hệ quả không còn được liệt kê/xem/dùng trong lần truy xuất mới và hành động không thể hoàn tác. Hộp xác nhận có nút `Xóa nguồn` và nút giữ an toàn `Giữ nguồn`. Chỉ gửi delete sau khi xác nhận; sau khi thành công bỏ nguồn khỏi danh sách ngay. Khi lỗi API, giữ hàng và hiển thị lỗi để thử lại. Backend vẫn là nơi quyết định ACL, active status và tombstone.
11. **Authorization:** Preview yêu cầu quyền Dataset hiện tại và version active mỗi lần mở/đọc; ẩn điều khiển Admin chỉ là affordance. Nếu quyền bị thu hồi hoặc nguồn bị xóa trong lúc panel đang mở, xóa nội dung khỏi panel và báo `Quyền truy cập đã thay đổi hoặc nguồn không còn khả dụng.` Không trả nội dung/metadata của Dataset ngoài quyền.

## Spacing Scale

Declared values (multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Khoảng icon và nhãn sát nhau |
| sm | 8px | Khoảng nội tuyến và giữa control nhỏ |
| md | 16px | Khoảng cách mặc định giữa control/row |
| lg | 24px | Padding card và nhóm form |
| xl | 32px | Tách nhóm nội dung chính |
| 2xl | 48px | Khoảng trống trạng thái rỗng |
| 3xl | 64px | Khoảng cách cấp trang khi cần |

Exceptions: giữ padding 40px của vùng chính desktop và 16px mobile do shell Phase 1; control tương tác có chiều cao tối thiểu 44px để chạm/bấm dễ dàng.

## Typography

Chỉ dùng bốn cỡ chữ sau cho giao diện nguồn; không thêm cỡ 13/14/21px cho bảng, trạng thái hay nhãn.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16px | regular (400) | 1.5 |
| Label / metadata | 12px | bold (700) | 1.5 |
| Section heading | 20px | bold (700) | 1.2 |
| Page heading | 28px | bold (700) | 1.2 |

Font weights: chỉ regular (400) và bold (700). Giữ font Arial, Helvetica, sans-serif hiện có.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#f3f6f8` | Nền workspace và vùng nội dung |
| Secondary (30%) | `#ffffff` | Card, bảng, form và panel preview |
| Accent (10%) | `#075b79` | CTA tải tệp; hồ sơ được chọn; nhãn version active; locator mở preview; thao tác `Thử lại` và `Nạp lại nguồn` |
| Destructive | `#a22a28` | Trạng thái lỗi và thao tác `Xóa nguồn` |

Accent reserved for: `Tải tệp lên`, `Xác nhận tải lên`, viền/nền profile đang chọn, dấu `Đang dùng` của version active, liên kết locator/`Xem đoạn trích`, `Thử lại`, `Nạp lại nguồn`. Các nút đóng/hủy không được trình bày như CTA chính. Nền sidebar hiện có `#16394b` và màu chữ `#172b3a` giữ nguyên; muted text dùng `#587080`/`#527080`; border dùng `#d7e1e8`/`#e0e8ed`; focus ring giữ `#dc8f21`.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | `Tải tệp lên` |
| Confirm upload | `Xác nhận tải lên` |
| Cancel upload | `Hủy tải lên` |
| Empty state heading | `Chưa có nguồn dữ liệu` |
| Empty state body | `Tải tệp đầu tiên lên để bắt đầu quản lý dữ liệu trong Dataset này.` |
| Error state | `Không thể xử lý tệp này. Mở chi tiết để xem dòng/trường và nguyên nhân; sửa tệp rồi tải lại, hoặc chọn Thử lại nếu đây là lỗi tạm thời.` |
| Destructive confirmation | `Xóa nguồn “{tên nguồn}”? Nguồn sẽ không còn hiển thị hoặc được dùng trong lần truy xuất mới. Việc xóa không thể hoàn tác.` Buttons: `Xóa nguồn` / `Giữ nguồn` |

Status labels: `Đang chờ xử lý`, `Đang xử lý`, `Sẵn sàng`, `Thất bại`, `Đang dùng`, `Có cảnh báo`. Tên hành động ngắn: `Xem đoạn trích`, `Thử lại`, `Nạp lại nguồn`, `Xóa nguồn`, `Hủy tải lên`, `Giữ nguồn`, `Đóng`. Không báo `Sẵn sàng` cho tới khi toàn bộ bước bắt buộc hoàn tất.

## UI Considerations

Applicable state considerations resolved: 8 covered, 0 backstop, 0 unresolved.

| Category | Element(s) | Status | Resolution / Reason |
|----------|------------|--------|---------------------|
| empty | Source list, upload form | ✅ covered | Khi Dataset chưa có nguồn, hiện heading/body trong Copywriting Contract và CTA `Tải tệp lên`; form bắt đầu ở trạng thái chưa chọn profile/tệp, không giả định dữ liệu đã tải. |
| loading | Source list, profile selector, source preview | ✅ covered | Dùng `role="status"` với thông báo tiếng Việt; khóa nút liên quan khi tải dữ liệu/gửi file, còn parser job tiếp tục hiển thị trạng thái bền vững theo từng file. |
| error | Upload form, source list, preview | ✅ covered | Inline `role="alert"`, chẩn đoán theo file/row/record/field và đường xử lý; không lộ stack/path; dùng copy lỗi đã quy định ở trên. |
| populated | Source list, source preview | ✅ covered | Bảng cho thấy nguồn/version/profile/status; preview có excerpt và locator cụ thể theo format. |
| partial | Batch result, source row | ✅ covered | Mỗi file có kết quả riêng; warning optional không chặn; candidate version lỗi không thay version active cũ; không công bố một phần version là `Sẵn sàng`. |
| overflow | Source list, preview content | ✅ covered | Bảng cuộn ngang trong card trên màn nhỏ; excerpt wrap theo dòng trong vùng cuộn; tên/file/error dài không đẩy bố cục vượt viewport. |
| zero-one-many | Source list, batch result | ✅ covered | Giữ cùng header bảng khi có một nguồn; khi không có nguồn dùng empty state; số lượng file/nguồn và trạng thái được hiển thị theo từng hàng, kể cả batch hỗn hợp. |
| long-text | Filename, error detail, profile schema, preview excerpt | ✅ covered | Tên dài wrap/mở rộng; lỗi và schema đọc được đầy đủ trong chi tiết; preview giữ xuống dòng và cuộn dọc, không clip nội dung hoặc biến nội dung thành một dòng dài. |

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|------------|-------------|
| shadcn official | none | not applicable — Tool: none; `components.json` không có |
| Third-party registries | none | not applicable — không khai báo registry/block |

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: FLAG
- [ ] Dimension 2 Visuals: FLAG
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS
- [x] Dimension 7 Inventory Provenance: PASS — Tool: none; component inventory được lược bỏ theo template.

**Approval:** approved 2026-10-07
