# Kiến trúc hệ thống — phiên bản theo phạm vi đã chốt

## 1. Phạm vi

Ứng dụng quản lý thực đơn, đơn hàng, hàng đợi bếp, trạng thái món, thanh toán, hủy đơn hợp lệ, báo cáo doanh thu ngày và khôi phục dữ liệu. **Không triển khai nghiệp vụ quản lý bàn ăn** trong phiên bản này.

Dữ liệu lưu lâu dài bằng file JSON theo SRS. Chạy trong một tiến trình Python; không cam kết an toàn cho nhiều tiến trình đồng thời ghi chung file.

## 2. Sơ đồ lớp

```text
Người dùng
   ↓
UI / Gradio (src/fnb/ui)
   ↓
Controller (src/fnb/controllers)
   ↓
Service (src/fnb/services)
   ├── MenuService: xem thực đơn / tra mã món
   ├── OrderService: tạo, thêm, hủy đơn
   ├── KitchenService: Queue FIFO và trạng thái món
   ├── PaymentService: hóa đơn, giảm giá, thanh toán
   └── ReportService: báo cáo doanh thu ngày
   ↓
Repository (src/fnb/repositories)
   ├── MenuRepository: dict theo mã món
   └── OrderRepository: dict theo mã đơn
   ↓
JsonStore (src/fnb/storage)
   ↓
JSON files (data/menu.json, data/orders.json)

Models định nghĩa cấu trúc dữ liệu dùng chung.
```

## 3. Trách nhiệm từng lớp

- **UI:** nhận input và hiển thị kết quả/lỗi. Không tự tính tiền, xử lý Queue hoặc đọc/ghi JSON.
- **Controller:** làm cổng giữa UI và Service; nhận tham số, gọi Service, chuyển kết quả Model thành dict/list.
- **Service:** chứa quy tắc nghiệp vụ. `OrderService` xác thực và điều phối tạo/thêm/hủy đơn; `KitchenService` xử lý FIFO và trạng thái món; `PaymentService` tính hóa đơn và kiểm tra điều kiện thanh toán.
- **Repository:** giữ Hash Map trong bộ nhớ, cung cấp CRUD, đồng bộ dữ liệu với JsonStore.
- **Models:** định nghĩa `MenuItem`, `Order`, `OrderItem` và các trạng thái hợp lệ.
- **JsonStore:** chỉ đọc/ghi danh sách bản ghi JSON, không hiểu quy tắc nghiệp vụ nhà hàng.

## 4. Luồng tạo đơn

1. UI gửi danh sách dòng món `{menu_item_id, quantity, note}` đến `OrderController`.
2. Controller gọi `OrderService.create_order(lines)`.
3. Service kiểm tra danh sách không rỗng; mã món tồn tại và còn bán; số lượng là số nguyên dương.
4. Service tạo `Order` và các `OrderItem`; tên/giá món được chụp tại thời điểm đặt.
5. `OrderRepository` lưu đơn vào `orders.json`.
6. `KitchenService` thêm từng dòng món có trạng thái `QUEUED` vào cuối `deque` theo `queue_seq`.
7. Controller trả kết quả cho UI.

## 5. Queue và Hash Map

- **Hash Map:** `MenuRepository._items_by_id` và `OrderRepository._orders_by_id` dùng `dict` với mã làm khóa. Tra cứu trung bình O(1).
- **Queue:** `KitchenService._queue` là `collections.deque`; `append()` thêm cuối, `popleft()` nhận món đầu.
- **Đơn vị Queue:** một dòng món trong đơn là một task Queue. `quantity=2` vẫn là một task có số lượng 2, đúng quy tắc SRS.
- **Khôi phục:** Queue không lưu độc lập trong file. Khi khởi động, hệ thống nạp `orders.json`, lấy các dòng thuộc đơn `OPEN` còn `QUEUED`, sắp xếp theo `queue_seq` rồi dựng lại `deque`.
- **Món đang chế biến:** `PREPARING` vẫn được lưu trong JSON, nhưng không quay lại Queue khi khởi động; người dùng có thể tìm đơn/món và tiếp tục cập nhật trạng thái.

## 6. Trạng thái hợp lệ

```text
Order: OPEN → PAID
             ↘ CANCELLED (chỉ khi mọi dòng món vẫn QUEUED)

OrderItem: QUEUED → PREPARING → READY → SERVED
     QUEUED → CANCELLED (khi hủy đơn hợp lệ)
```

Không cho bỏ qua bước hoặc chuyển ngược trạng thái. Không thanh toán lần hai. Đơn `PAID` và `CANCELLED` được giữ lại trong lịch sử.

## 7. Phạm vi ngoài MVP

Quản lý bàn, đăng nhập/phân quyền, đặt bàn trước, nhiều chi nhánh, tồn kho, thanh toán trực tuyến thực tế, SQL, nhiều tiến trình cùng ghi JSON và hoàn tiền không thuộc phiên bản hiện tại.
