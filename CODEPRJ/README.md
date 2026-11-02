# Hệ thống Quản lý Đơn hàng F&B — Backend-first starter

Bộ khung học tập cho nhóm 5 sinh viên năm nhất. Phiên bản này bám theo SRS đã thống nhất: **dùng JSON và bỏ nghiệp vụ quản lý bàn ăn**.

## Công nghệ

- Python 3.11+
- `uv` quản lý môi trường/dependencies
- Gradio làm UI mỏng
- JSON lưu menu và đơn hàng
- `dict` làm Hash Map tra cứu món/đơn theo ID (trung bình O(1))
- `collections.deque` làm Queue FIFO cho các dòng món chờ bếp
- `pytest` và `ruff` để kiểm thử/lint

## Chạy dự án

```bash
uv sync
uv run pytest
uv run python -m fnb.main
```

Nếu chưa có `uv.lock`, chạy `uv lock` rồi commit file đó để tất cả thành viên đồng bộ dependencies.

## Cấu trúc

```text
fnb_order_system_starter/
├── data/
│   ├── menu.json
│   └── orders.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   ├── MEMBER_TASKS.md
│   ├── SRS_FNB_v1.0.3.md
│   ├── SRS_SCOPE_ADJUSTMENTS.md
│   └── GIT_UV_WORKFLOW.md
├── src/fnb/
│   ├── models.py
│   ├── exceptions.py
│   ├── storage/json_store.py
│   ├── repositories/
│   ├── services/
│   ├── controllers/
│   ├── ui/app.py
│   ├── bootstrap.py
│   └── main.py
└── tests/
```

## Quy tắc nghiệp vụ quan trọng

- `OrderService` kiểm tra mã món, trạng thái còn bán và số lượng nguyên dương.
- Tên và đơn giá được chụp vào `OrderItem` tại thời điểm đặt, để cập nhật menu không làm thay đổi hóa đơn cũ.
- Mỗi dòng món là một phần tử Queue; `quantity=2` vẫn là một task Queue với số lượng 2.
- Queue dùng `deque` và được dựng lại sau khởi động từ các dòng có trạng thái `QUEUED`, sắp xếp theo `queue_seq`.
- Chỉ được hủy đơn `OPEN` khi tất cả dòng món còn `QUEUED`; đơn hủy và đơn đã thanh toán vẫn nằm trong lịch sử.
- Chỉ được thanh toán khi tất cả món ở trạng thái `READY` hoặc `SERVED`; không cho thanh toán lần hai.
- Backend tự tính tiền từ snapshot giá; UI không gửi số tiền cuối cùng để backend tin dùng.
- Dữ liệu mẫu không ghi đè các file JSON đang tồn tại. JSON phù hợp cho project nhỏ một tiến trình, không phải cơ chế ghi đồng thời đa tiến trình.
- Không triển khai nghiệp vụ bàn; không có `table_id` trong `Order`.

## Đọc tài liệu theo thứ tự

1. `docs/ARCHITECTURE.md` — luồng giữa các lớp.
2. `docs/API_CONTRACT.md` — tên hàm và input/output.
3. `docs/MEMBER_TASKS.md` — vai trò và đầu ra từng thành viên.
4. `docs/SRS_FNB_v1.0.3.md` — bản SRS đã điều chỉnh, dùng làm căn cứ nghiệm thu.
5. `docs/GIT_UV_WORKFLOW.md` — branch, PR, commit và lệnh kiểm tra.
6. `docs/SRS_SCOPE_ADJUSTMENTS.md` — ghi chú đối chiếu với bản SRS trước đó.
