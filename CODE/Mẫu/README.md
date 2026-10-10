# Hệ thống Quản lý Đơn hàng / Bàn ăn F&B — Starter Backend-first

Đây là bộ khung học tập cho nhóm 5 sinh viên. Mục tiêu là làm rõ **ai chịu trách nhiệm gì**, dữ liệu đi qua các lớp như thế nào và cách kiểm thử trước khi hoàn thiện giao diện.

## 1. Công nghệ

- Python 3.11+
- `uv` để tạo môi trường và khóa phiên bản package
- Gradio cho giao diện demo mỏng
- File JSON để lưu dữ liệu
- `dict` làm Hash Map tra cứu theo ID (trung bình O(1))
- `collections.deque` làm Queue FIFO cho các dòng món chờ bếp
- `pytest` để kiểm thử; `ruff` để kiểm tra chất lượng code

## 2. Chạy dự án

Cài `uv` theo hướng dẫn của môn học/máy tính bạn đang dùng, sau đó chạy tại thư mục gốc:

```bash
uv sync
uv run pytest
uv run python -m fnb.main
```

Nếu lệnh chạy package chưa tìm thấy `fnb`, hãy dùng lệnh cài đặt ở chế độ editable hoặc kiểm tra cấu hình project:

```bash
uv sync
```

Ứng dụng Gradio chỉ là giao diện demo kỹ thuật ban đầu, không phải UI cuối cùng. Nó cho phép gọi một số thao tác backend bằng cách nhập dữ liệu JSON; thành viên FE có thể cải tiến sau khi hợp đồng Controller được nhóm duyệt.

## 3. Đọc tài liệu theo thứ tự

1. `docs/ARCHITECTURE.md` — hiểu luồng dữ liệu giữa các lớp.
2. `docs/API_CONTRACT.md` — biết hàm nào gọi hàm nào, input/output là gì.
3. `docs/MEMBER_TASKS.md` — trách nhiệm và đầu ra của từng thành viên.
4. `docs/GIT_UV_WORKFLOW.md` — cách làm việc với Git và uv.

## 4. Cấu trúc thư mục

```text
fnb_order_system_starter/
├── data/                     # JSON mẫu được version control
├── docs/                     # Sơ đồ, API contract, phân công
├── src/fnb/
│   ├── models.py              # Các kiểu dữ liệu và trạng thái
│   ├── exceptions.py          # Lỗi nghiệp vụ dùng chung
│   ├── storage/               # Đọc/ghi JSON
│   ├── repositories/          # CRUD và Hash Map
│   ├── services/              # Quy tắc nghiệp vụ và Queue bếp
│   ├── controllers/           # Cửa vào cho UI gọi
│   ├── ui/                    # Gradio, không đặt nghiệp vụ tại đây
│   ├── bootstrap.py           # Lắp ghép các thành phần
│   └── main.py                # Điểm khởi chạy
└── tests/                     # Test nghiệp vụ và dữ liệu
```

## 5. Quy tắc quan trọng

- **Không đặt nghiệp vụ trong `ui/app.py`.** UI chỉ lấy input, gọi Controller và hiển thị output.
- Giá thanh toán phải lấy từ Menu/Order đã xác thực ở backend, không tin giá do UI gửi lên.
- `menu.json`, `tables.json`, `orders.json` là nguồn dữ liệu bền vững.
- Queue trong RAM được dựng lại khi khởi động từ các `OrderItem` có trạng thái `QUEUED`, sắp theo `queue_seq`.
- Một phần tử Queue là **một dòng món trong đơn**; trường `quantity` cho biết số phần của dòng đó. Ví dụ 2 burger cùng ghi chú có thể là 1 Queue task với quantity=2.
- Đơn đã thanh toán được giữ trong `orders.json` để làm báo cáo; chỉ cập nhật trạng thái chứ không xóa.
- Bộ khung không tích hợp cổng thanh toán thật. `checkout()` chỉ mô phỏng xác nhận thanh toán.
- JSON phù hợp cho đồ án nhỏ/chạy một tiến trình. Không coi đây là giải pháp nhiều người ghi đồng thời như hệ thống production.

## 6. Tiêu chí MVP

- Tra cứu menu theo mã bằng dict.
- Tạo đơn hợp lệ và cập nhật trạng thái bàn.
- Món được đưa vào Queue FIFO và có thể chuyển trạng thái `QUEUED → PREPARING → READY → SERVED`.
- Chỉ thanh toán đơn hợp lệ; lưu đơn PAID và giải phóng bàn.
- Báo cáo doanh thu ngày từ các đơn PAID.
- Test các luồng chính; chạy được với `uv`; PR có review.
