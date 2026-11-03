# Phân công 5 thành viên — Phiên bản tối giản Backend-first

Mỗi người phải hiểu: Input nhận từ đâu → mình xử lý gì → Output bàn giao cho ai → kiểm tra bằng cách nào.

## Thành viên 1 — Thanh Bình: Models, JSON, khởi tạo

**Phạm vi:** `models.py`, `storage/json_store.py`, `bootstrap.py`, `data/`.

- Định nghĩa `MenuItem`, `Order`, `OrderItem`, hai enum trạng thái.
- Đảm bảo menu và đơn hàng đọc/ghi JSON.
- Duy trì `queue_seq` để khôi phục đúng FIFO.
- Kết nối Repository, Service và Controller trong `bootstrap.py`.
- Không viết logic Queue trong JSON Store; không quản lý bàn/báo cáo.

**Bàn giao:** Model serialize/deserialize được; `build_context()` khởi tạo được và Queue tự khôi phục qua `KitchenService`.

## Thành viên 2 — Repository và Hash Map

**Phạm vi:** `repositories/menu_repository.py`, `repositories/order_repository.py`.

- Dùng `dict` lập chỉ mục theo mã món/mã đơn.
- Cung cấp `get_by_id`, `list_all`, `upsert`.
- Lưu JSON trước khi cập nhật cache để tránh cache lệch khi ghi file lỗi.
- Viết test tra cứu, lưu và nạp lại dữ liệu.

**Bàn giao:** Menu/Order tra cứu theo mã trung bình O(1); giải thích được Hash Map nằm ở Repository.

## Thành viên 3 — Queue OOP và nghiệp vụ bếp

**Phạm vi:** `queue/node.py`, `queue/queue.py`, `services/kitchen_service.py`, `controllers/kitchen_controller.py`.

- Tự cài Node và Queue bằng Linked List; quản lý front, rear, size.
- Cài `enqueue`, `dequeue`, `peek`, `is_empty`, `size`.
- Khôi phục các món QUEUED theo `queue_seq` khi khởi động.
- Chỉ phục vụ Node đầu Queue; lưu trạng thái SERVED xuống JSON trước khi dequeue.
- Viết test FIFO, rỗng, một phần tử, nhiều phần tử, khôi phục sau restart.

**Bàn giao:** Có thể demo Linked List Queue độc lập và xử lý món từ QUEUED sang SERVED.

## Thành viên 4 — Tạo đơn và thanh toán

**Phạm vi:** `services/order_service.py`, `services/menu_service.py`, `services/payment_service.py` và Controllers liên quan.

- Tạo một Order từ giỏ món; kiểm tra mã món và số lượng.
- Gộp dòng trùng mã món/cùng ghi chú; chụp tên và giá tại thời điểm đặt.
- Gửi từng dòng món đến KitchenService theo queue_seq.
- Xem hóa đơn, gộp cùng món và tính tiền.
- Chỉ checkout khi mọi dòng đã SERVED; lưu PAID, paid_at, total_paid.
- Viết test dữ liệu sai, gộp số lượng, thanh toán sớm và thanh toán lặp.

**Bàn giao:** Tạo đơn → Queue → thanh toán được qua Controller, không cần UI.

## Thành viên 5 — Frontend Gradio và tích hợp

**Phạm vi:** `ui/app.py`, `ui/presenter.py`, `ui/views/`.

- Dựng ba tab: Đặt món, Queue bếp, Thanh toán & Hóa đơn.
- Tab Đặt món: menu table, chọn mã món, số lượng, ghi chú, giỏ hàng, tạo đơn.
- Tab Bếp: hiển thị Queue và món SERVED; chỉ có nút phục vụ phần tử đầu.
- Tab Thanh toán: chọn Order, xem hóa đơn, xác nhận và hiển thị bill.
- Callback chỉ gọi Controller; không sửa JSON, không tự thao tác Linked List.

**Bàn giao:** Demo liền mạch từ chọn món đến in bill; UI hiển thị lỗi Backend thân thiện.

## Việc chung

- Cả nhóm đọc `API_CONTRACT.md` trước khi code song song.
- Mọi thay đổi trạng thái/field phải trao đổi với người phụ trách Models và cập nhật contract.
- Mỗi thành viên viết test cho phần mình.
- Dùng Feature branch → PR → review → merge vào `develop`.
