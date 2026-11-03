# F&B Simple Order System

Project học tập cho nhóm 5 sinh viên năm nhất. Phiên bản này chỉ tập trung vào ba chức năng:

1. Chọn món và tạo một đơn hàng.
2. Đưa từng dòng món vào Queue FIFO, xử lý từ đầu hàng đợi và chuyển sang `SERVED`.
3. Thanh toán một đơn khi tất cả món trong đơn đã `SERVED`, sau đó hiển thị hóa đơn.

## Công nghệ

- Python 3.11+
- `uv` quản lý môi trường và dependencies.
- Gradio tạo giao diện web.
- JSON lưu menu và đơn hàng.
- `dict` trong Repository tra cứu món/đơn theo mã (trung bình O(1)).
- Queue FIFO tự cài đặt bằng OOP + Linked List (`Node`, `Queue`); không dùng `list` hoặc `collections.deque` làm hàng đợi.
- `pytest` kiểm thử.

## Chạy dự án

```bash
uv sync
uv run pytest
uv run python -m fnb.main
```

## Cấu trúc thư mục

```text
CODEPRJ/
├── data/
│   ├── menu.json
│   └── orders.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   ├── MEMBER_TASKS.md
│   ├── GIT_UV_WORKFLOW.md
│   └── SRS_FNB_v1.1.0.md
├── src/fnb/
│   ├── controllers/
│   ├── models.py
│   ├── queue/
│   │   ├── node.py
│   │   └── queue.py
│   ├── repositories/
│   ├── services/
│   ├── storage/
│   ├── ui/
│   ├── bootstrap.py
│   └── main.py
└── tests/
```

## Quy tắc nghiệp vụ

- Một lần nhấn “Tạo đơn” tạo một `Order`; toàn bộ món của cùng lượt đặt nằm trong đơn đó.
- Món trùng mã và cùng ghi chú được gộp số lượng thành một dòng. Mỗi dòng món là một Node Queue, `quantity=3` vẫn là một Node.
- Mỗi dòng món chỉ có hai trạng thái: `QUEUED` và `SERVED`.
- Bếp chỉ được xác nhận phục vụ Node ở đầu Queue. Sau khi JSON ghi trạng thái `SERVED` thành công, Node mới được lấy khỏi Queue.
- `orders.json` lưu nội dung đơn, trạng thái món và `queue_seq`. Khi khởi động, Queue Linked List được dựng lại từ các dòng `QUEUED` theo `queue_seq`.
- Mỗi lần tạo đơn hoặc phục vụ món, trạng thái liên quan được ghi xuống JSON ngay. Không cần phụ thuộc vào thao tác đóng ứng dụng để lưu Queue.
- Hóa đơn gom các món cùng mã trong một đơn và cộng số lượng. Ghi chú khác nhau được gom vào cùng dòng hóa đơn.
- Chỉ thanh toán khi tất cả món đã `SERVED`; Backend chặn thanh toán lặp.
- Không có quản lý bàn, báo cáo doanh thu, hủy đơn, thêm món sau khi tạo đơn, quản lý kho, đăng nhập hoặc phân quyền.

## Đọc tài liệu

1. `docs/ARCHITECTURE.md`
2. `docs/API_CONTRACT.md`
3. `docs/MEMBER_TASKS.md`
4. `docs/SRS_FNB_v1.1.0.md`
5. `docs/GIT_UV_WORKFLOW.md`
