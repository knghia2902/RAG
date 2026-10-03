# Phase 1: Local Workspace and Access Control - Discussion Log

> Audit trail only. Downstream planning uses 01-CONTEXT.md, not this log.

**Date:** 2026-10-03
**Phase:** 01-local-workspace-and-access-control
**Areas discussed:** Tài khoản và phiên đăng nhập; Quyền theo dataset; Giao diện quản trị; Khởi động và dữ liệu demo.

User selected all four areas. Each area contained four questions; all implementation choices were option 1. User chose to proceed after each area and authorized CONTEXT.md creation at the final gate. In the dataset area the user briefly selected more discussion, then immediately corrected to proceed; no additional decision was made in between.

## Tài khoản và phiên đăng nhập

### Thông tin nào dùng để đăng nhập?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Username + mật khẩu | Yes |
| 2 | Email + mật khẩu |  |
| 3 | Username hoặc email |  |

**User choice:** Username + mật khẩu (option 1).

### Khởi tạo Admin đầu tiên thế nào?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Lệnh khởi tạo | Yes |
| 2 | Cấu hình môi trường |  |
| 3 | Trang thiết lập lần đầu |  |

**User choice:** Lệnh khởi tạo, nhập username/mật khẩu; chạy lại không ghi đè tài khoản (option 1).

### Khi kỹ thuật viên quên mật khẩu xử lý thế nào?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Admin cấp mật khẩu tạm, bắt buộc đổi | Yes |
| 2 | Admin đặt mật khẩu mới, không bắt buộc đổi |  |

**User choice:** Admin cấp mật khẩu tạm, bắt buộc đổi ở lần đăng nhập tiếp theo (option 1).

### Phiên đăng nhập kéo dài thế nào?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 30 phút không hoạt động, tối đa 8 giờ | Yes |
| 2 | Giữ phiên 8 giờ |  |
| 3 | Giữ phiên 7 ngày |  |

**User choice:** Hết phiên sau 30 phút không hoạt động, tối đa 8 giờ; đăng xuất hoặc vô hiệu hóa tài khoản thu hồi phiên (option 1).

## Quyền theo dataset

### Đơn vị cấp quyền dữ liệu?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Theo dataset | Yes |
| 2 | Theo từng tài liệu |  |
| 3 | Theo nhóm hệ thống/phòng ban |  |

**User choice:** Theo dataset (option 1).

### Quyền mặc định của Kỹ thuật viên mới?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Chưa được truy cập dataset nào | Yes |
| 2 | Tự cấp một dataset chung |  |

**User choice:** Chưa được truy cập dataset nào; Admin cấp cụ thể; hiển thị hướng dẫn liên hệ Admin khi chưa có quyền (option 1).

### Báo cáo dùng A và B khi bị thu hồi quyền A?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Chặn toàn bộ báo cáo/PDF và thông báo | Yes |
| 2 | Ẩn khỏi danh sách và từ chối liên kết cũ |  |

**User choice:** Chặn toàn bộ báo cáo/PDF, thông báo quyền đã thay đổi; có thể tạo báo cáo mới từ B (option 1).

### Kỹ thuật viên được làm gì với dữ liệu?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Chỉ sử dụng, cho phép nhập/upload ticket phân tích | Yes |
| 2 | Được upload thêm tài liệu/log |  |

**User choice:** Chỉ sử dụng để tra cứu/phân tích/tạo báo cáo; Admin quản lý upload tài liệu/log, xóa và reindex. Kỹ thuật viên được nhập/upload ticket để phân tích trong dataset được cấp (option 1).

## Giao diện quản trị

### Bố cục giao diện quản trị?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Sidebar bên trái | Yes |
| 2 | Menu ngang |  |
| 3 | Thẻ chức năng |  |

**User choice:** Sidebar bên trái; bảng và biểu mẫu ở nội dung chính (option 1).

### Màn hình sau đăng nhập?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Theo vai trò | Yes |
| 2 | Cùng vào Dataset |  |

**User choice:** Theo vai trò: Admin vào Tài khoản; Kỹ thuật viên vào Dataset được cấp, chưa có quyền thì hướng dẫn liên hệ Admin (option 1).

### Ngôn ngữ giao diện?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Tiếng Việt | Yes |
| 2 | Tiếng Anh |  |
| 3 | Chuyển đổi Việt/Anh |  |

**User choice:** Tiếng Việt; giữ thuật ngữ kỹ thuật phù hợp (option 1).

### Tạo tài khoản/chỉnh quyền ở đâu?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Panel bên phải | Yes |
| 2 | Trang riêng |  |
| 3 | Hộp thoại |  |

**User choice:** Panel bên phải cạnh bảng; lưu xong cập nhật bảng (option 1).

## Khởi động và dữ liệu demo

### Phạm vi truy cập MVP?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Chỉ localhost | Yes |
| 2 | Cho phép mạng nội bộ |  |

**User choice:** Chỉ localhost trên máy chạy Docker (option 1).

### Chuẩn bị dữ liệu demo phase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Lệnh seed riêng | Yes |
| 2 | Tạo thủ công qua Web |  |

**User choice:** Lệnh seed riêng: tài khoản Kỹ thuật viên và dataset mẫu chưa có tài liệu, trường hợp có/chưa có quyền; nhập mật khẩu khi chạy; chạy lại không ghi đè (option 1).

### Chưa có OpenAI API key khi khởi động?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Quản trị vẫn chạy | Yes |
| 2 | Yêu cầu key để khởi động |  |

**User choice:** Quản trị vẫn hoạt động; hiển thị Chưa cấu hình AI; chức năng cần AI ở phase sau yêu cầu key (option 1).

### Cấu hình lần đầu ở đâu?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | File .env và hướng dẫn | Yes |
| 2 | Kết hợp .env và Web |  |

**User choice:** File .env và hướng dẫn chạy; Web chỉ hiển thị trạng thái, không giá trị secrets (option 1).

## Implementation Discretion

No explicit you-decide answer. Technical details not presented as product choices remain researcher/planner responsibility within locked decisions.

## Deferred Ideas

None newly introduced. Other roadmap phases and MVP exclusions remain unchanged.
