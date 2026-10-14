---
phase: 05-on-demand-incident-reports-and-pdf
plan: "02"
subsystem: weasyprint-pdf-generator-and-template
tags: [weasyprint, pdf, jinja2, vietnamese-fonts, paged-media, print-css, ssrf-protection, xss-protection]
requires: [05-01]
provides:
  - WeasyPrint 70.0 and Vietnamese font native libraries in backend Dockerfile and pyproject.toml
  - Print-ready multi-page Jinja2 HTML/CSS template (incident_report.html) with repeating table headers, page-break rules, and Trang X / Y counters
  - ReportPDFGenerator service with SSRF blocking and autoescaping in backend/app/modules/reports/pdf_generator.py
  - Unit tests in backend/tests/unit/test_pdf_generator.py verifying HTML escaping, SSRF blocking, and Vietnamese PDF magic bytes
affects: [05-03, 05-04]
tech-stack:
  added: [weasyprint==70.0, fonts-liberation, fonts-dejavu-core, libpango-1.0-0, libcairo2]
  patterns: [paged-media-css, offline-font-packaging, ssrf-hardened-fetcher, jinja2-autoescape]
key-files:
  created:
    - backend/app/modules/reports/templates/incident_report.html
    - backend/app/modules/reports/pdf_generator.py
    - backend/tests/unit/test_pdf_generator.py
  modified:
    - backend/Dockerfile
    - backend/pyproject.toml
key-decisions:
  - "Sử dụng WeasyPrint 70.0 cùng bộ font native tiếng Việt (Liberation Sans, DejaVu Sans) đóng gói cục bộ trong container Docker, triệt tiêu nguy cơ lỗi font tofu (D-07, D-08)."
  - "Áp dụng quy tắc CSS in ấn đa trang (@page) khổ A4 dọc, margins 20mm 15mm, thead { display: table-header-group; } lặp lại tiêu đề bảng khi sang trang và tr { page-break-inside: avoid; } chống cắt ngang dòng."
  - "Chân trang hiển thị số trang chuẩn xác định dạng 'Trang ' counter(page) ' / ' counter(pages) cùng thời điểm xuất và định danh báo cáo."
  - "Chặn toàn bộ URL fetcher ngoại bộ trong WeasyPrint (_blocked_url_fetcher) để ngăn ngừa SSRF và rò rỉ dữ liệu (T-05-03)."
requirements-completed: [REP-06]
actuals:
  tokens: 32000
  tasks: 3
  commits: 1
duration: 12min
completed: 2026-10-14
status: complete
---

# Phase 5 Plan 02: WeasyPrint Docker Integration & PDF Generator Engine Summary

**Tích hợp WeasyPrint 70.0 vào môi trường Docker cùng bộ font tiếng Việt native (`Liberation Sans`, `DejaVu Sans`), xây dựng mẫu in ấn Jinja2 HTML/CSS đa trang chuẩn in ấn và dịch vụ sinh file PDF tiếng Việt an toàn chống SSRF theo REP-06 và D-07, D-08.**

## Hoàn thành các nhiệm vụ

### 1. Dockerfile & Dependencies Setup for WeasyPrint 70.0 (Task 05-02-01)
- Cập nhật `backend/Dockerfile`: Cài đặt các gói native `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz0b`, `libcairo2`, `fonts-liberation`, `fonts-dejavu-core` và pip package `weasyprint==70.0`.
- Cập nhật `backend/pyproject.toml`: Bổ sung `"weasyprint==70.0"` vào danh sách dependencies.
- Build và cập nhật container image thành công, xác thực lệnh `python -c "import weasyprint; print(weasyprint.__version__)"` in ra đúng `70.0`.

### 2. Jinja2 Print-Ready HTML/CSS Template for Incident Reports (Task 05-02-02)
- Tạo `backend/app/modules/reports/templates/incident_report.html`:
  - Khổ giấy A4 dọc (`size: A4 portrait; margin: 20mm 15mm 20mm 15mm;`).
  - Tiêu đề bảng lặp lại tự động (`thead { display: table-header-group; }`) khi bảng dữ liệu kéo dài nhiều trang.
  - Chống xé dòng bảng (`tr { page-break-inside: avoid; }`).
  - Chân trang hiển thị số trang `"Trang " counter(page) " / " counter(pages)` cùng thông tin hệ thống và ngày giờ xuất bản.
  - Trình bày đầy đủ 5 khối thông tin: Thông tin chung, KPI Overview, Phân bổ theo hệ thống & mức ưu tiên, Danh mục lỗi lặp lại ($\ge 2$ lần), Nhận định AI & SOP, và Nguồn dữ liệu tham chiếu (Provenance).

### 3. WeasyPrint PDF Generator Service & Unit Tests (Task 05-02-03)
- Triển khai `ReportPDFGenerator` trong `backend/app/modules/reports/pdf_generator.py`:
  - Khởi tạo Jinja2 Environment với `autoescape=True` ngăn ngừa XSS/HTML Injection (T-05-04).
  - Định dạng thời gian theo múi giờ `Asia/Ho_Chi_Minh` (UTC+7) trên bản in.
  - Tích hợp `_blocked_url_fetcher` chặn mọi yêu cầu mạng ngoại vi nhằm triệt tiêu hoàn toàn nguy cơ SSRF (T-05-03).
- Tạo `backend/tests/unit/test_pdf_generator.py` với 3 bài kiểm thử đơn vị:
  - `test_render_html_escaping`: Kiểm tra tự động escape thẻ HTML độc hại.
  - `test_ssrf_blocked_url_fetcher`: Kiểm tra chặn URL ngoại vi và ném `PermissionError`.
  - `test_generate_pdf_magic_bytes_and_vietnamese`: Biên dịch PDF với tiếng Việt có dấu phức tạp, xác thực file PDF sinh ra hợp lệ và bắt đầu bằng `%PDF-1.`.
- Toàn bộ 10/10 tests đơn vị của cả Plan 01 và Plan 02 đều chạy thành công 100%.
