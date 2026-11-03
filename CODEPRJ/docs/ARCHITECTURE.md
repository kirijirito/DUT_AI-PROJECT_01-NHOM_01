# Kiến trúc hệ thống F&B Simple Order

## 1. Phạm vi

Ứng dụng chỉ có ba nhóm chức năng: tạo đơn từ menu, xử lý Queue bếp FIFO và thanh toán/in hóa đơn. Không triển khai nghiệp vụ bàn, báo cáo, hủy đơn, quản lý kho, đăng nhập hoặc phân quyền.

## 2. Các lớp

```text
Gradio UI
   ↓
Controller
   ↓
Service
   ↓
Repository
   ↓
JsonStore → menu.json / orders.json

KitchenService → Queue (Linked List tự cài đặt)
```

- **UI:** nhận thao tác, gửi dữ liệu tới Controller và hiển thị kết quả. Không tự sửa JSON, không tự quản lý Queue, không tự quyết định điều kiện thanh toán.
- **Controller:** tiếp nhận lời gọi từ UI và gọi Service phù hợp.
- **Service:** kiểm tra và thực hiện quy tắc nghiệp vụ.
- **Repository:** dùng `dict` làm Hash Map tra cứu theo mã và đồng bộ với JSON.
- **JsonStore:** đọc/ghi JSON; không chứa nghiệp vụ.
- **Queue:** cấu trúc dữ liệu riêng bằng Node và Linked List, do `KitchenService` sở hữu.

## 3. Cấu trúc Queue OOP

`src/fnb/queue/node.py` định nghĩa `Node(data, next)`. `src/fnb/queue/queue.py` định nghĩa `Queue` với `front`, `rear`, `_size` và các phương thức:

- `enqueue(item)`: thêm cuối hàng đợi, O(1).
- `dequeue()`: lấy đầu hàng đợi, O(1).
- `peek()`: xem phần tử đầu, O(1).
- `is_empty()`, `size()`, `to_list()`.

Không dùng `collections.deque` hoặc Python `list` để cài đặt Queue. `to_list()` chỉ tạo bản sao phục vụ hiển thị/kiểm thử.

Một Node lưu khóa tham chiếu `(queue_seq, order_id, order_item_id)`, không sao chép toàn bộ Order vào Queue. Dữ liệu món đầy đủ nằm trong Order JSON.

## 4. Luồng tạo đơn

1. UI tạo giỏ tạm và gửi `{menu_item_id, quantity, note}` đến `OrderController`.
2. `OrderService` kiểm tra mã món, tình trạng còn bán và số lượng nguyên dương.
3. Các dòng có cùng mã món và cùng ghi chú được gộp số lượng.
4. Service chụp tên/giá hiện tại từ Menu, tạo `Order` và gán `queue_seq` tăng dần.
5. `OrderRepository` ghi Order vào `orders.json`.
6. `KitchenService` enqueue các Node theo đúng thứ tự. Một dòng món có `quantity=3` vẫn là một Node.

## 5. Luồng bếp và lưu/khôi phục Queue

- Queue chỉ chứa các dòng `QUEUED` của các đơn `OPEN`.
- Bếp chỉ được xử lý phần tử ở `front`, bảo đảm FIFO.
- `serve_next_item()` xem Node đầu, tải Order/OrderItem, đổi trạng thái sang `SERVED` và ghi JSON trước. Chỉ khi ghi thành công mới `dequeue()` Node.
- Nếu ghi JSON thất bại, Node vẫn ở đầu Queue, người dùng có thể thử lại.
- Khi khởi động, `KitchenService` đọc Orders từ Repository, lấy mọi dòng `QUEUED`, sắp xếp theo `queue_seq` và enqueue lại vào Linked List.
- `orders.json` là nguồn lưu lâu dài; Queue trong RAM vẫn là Linked List OOP thực sự. Không có file JSON nào đóng vai trò thay cho cấu trúc Queue.

## 6. Luồng thanh toán

1. Thu ngân chọn một đơn `OPEN` và xem hóa đơn.
2. `PaymentService` gom các món cùng mã trong cùng Order, cộng số lượng và tính thành tiền từ giá snapshot.
3. Nếu còn bất kỳ món nào `QUEUED`, Service từ chối thanh toán.
4. Khi tất cả món `SERVED`, Service đổi đơn sang `PAID`, lưu `paid_at` và `total_paid` vào JSON.
5. UI hiển thị hóa đơn đã thanh toán ngay trong tab Thanh toán & Hóa đơn.

## 7. Giới hạn

Ứng dụng chạy một tiến trình Python, lưu JSON cục bộ. Không cam kết an toàn khi nhiều tiến trình cùng ghi file. Thanh toán chỉ là xác nhận nội bộ, không tích hợp ngân hàng/cổng thanh toán.
