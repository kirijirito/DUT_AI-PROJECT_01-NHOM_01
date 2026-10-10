# Kiến trúc và luồng nghiệp vụ

## 1. Sơ đồ tầng

```text
Người dùng
   ↓ thao tác
UI / Gradio (src/fnb/ui)
   ↓ gọi hàm Python
Controller (src/fnb/controllers)
   ↓ gọi nghiệp vụ
Service (src/fnb/services)
   ├── kiểm tra quy tắc
   ├── dùng Queue deque ở KitchenService
   └── tra cứu/lưu qua Repository
              ↓
Repository (src/fnb/repositories)
   ├── dict theo ID để tra cứu trung bình O(1)
   └── gọi JsonStore
              ↓
JSON files (data/*.json)

Models định nghĩa hình dạng dữ liệu dùng giữa các lớp.
```

## 2. Trách nhiệm từng lớp

- **UI:** nhận thao tác và hiển thị kết quả/lỗi. Không tính tiền, không sửa JSON, không tự thay đổi Queue.
- **Controller:** là cửa vào dành cho UI. Chuyển dữ liệu UI sang lời gọi Service; chuyển Model thành dict đơn giản để UI hiển thị.
- **Service:** chứa quy tắc nghiệp vụ. Ví dụ `OrderService` kiểm tra món/bàn trước khi tạo đơn; `PaymentService` kiểm tra trạng thái trước khi checkout.
- **Repository:** cung cấp thao tác lưu/đọc CRUD; sở hữu Hash Map trong bộ nhớ và đồng bộ với file JSON.
- **Models:** quy định trường dữ liệu, enum trạng thái, cách chuyển từ/đến dict.
- **JsonStore:** chỉ chịu trách nhiệm đọc/ghi list JSON. Không biết nghiệp vụ nhà hàng.

## 3. Luồng “bấm Order”

1. UI gửi `table_id` và danh sách `{menu_item_id, quantity, note}` cho `OrderController`.
2. Controller gọi `OrderService.create_order(...)`.
3. Service kiểm tra bàn tồn tại/còn trống, mã món tồn tại/đang bán và số lượng hợp lệ.
4. Service tạo `Order` và `OrderItem`. Tên/giá được chụp vào `OrderItem` tại thời điểm gọi món.
5. `OrderRepository` lưu đơn vào `orders.json`; `TableService` gắn bàn với đơn.
6. `KitchenService` đưa các dòng món trạng thái QUEUED vào `deque` theo `queue_seq`.
7. Controller trả dữ liệu đơn cho UI hiển thị.

## 4. Queue và Hash Map

- **Hash Map:** `MenuRepository._items_by_id` và `TableRepository._tables_by_id` là dict khóa theo ID. `get_by_id()` dùng dict thay vì duyệt toàn bộ list.
- **Queue:** `KitchenService._queue` là `collections.deque`. `append()` thêm cuối hàng; `popleft()` lấy món đứng đầu.
- **Khôi phục sau restart:** Queue không được lưu thành một cấu trúc riêng trong JSON. Thay vào đó, `queue_seq` và `status` của từng dòng OrderItem được lưu. Khi khởi động, KitchenService tìm các dòng đang QUEUED và dựng lại Queue theo `queue_seq` tăng dần.
- **Khi bắt đầu chế biến:** dòng món chuyển sang PREPARING và được lưu JSON. Dòng món không còn nằm trong hàng chờ QUEUED; nó vẫn tồn tại trong đơn để bếp tiếp tục cập nhật.

## 5. Trạng thái đề xuất

```text
Order: OPEN → PAID
             ↘ CANCELLED (nếu được phép hủy)

OrderItem: QUEUED → PREPARING → READY → SERVED
     QUEUED → CANCELLED (khi hủy đơn hợp lệ)

Table: AVAILABLE ↔ OCCUPIED
```

Không cho `PAID` chuyển ngược thành `OPEN`. Không cho thanh toán lần hai. MVP chỉ cho hủy khi tất cả dòng món còn QUEUED; nhóm có thể bỏ chức năng hủy nếu thiếu thời gian nhưng cần ghi rõ phạm vi.

## 6. Phạm vi cố ý chưa làm

Đăng nhập/phân quyền, nhiều chi nhánh, database SQL, thanh toán thật, nhiều tiến trình cùng ghi JSON, hoàn tiền và quản lý kho nằm ngoài MVP. Làm ít nhưng đúng và test được.
