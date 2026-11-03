# Software Requirement Specification — F&B Simple Order System

**Phiên bản:** 1.1.0  
**Phạm vi:** Project môn học, bản tối giản Backend-first.

## 1. Mục đích

Mô tả yêu cầu của ứng dụng đặt món F&B nhỏ, tập trung minh họa Hash Map, Queue FIFO tự cài đặt bằng OOP và kiến trúc phân lớp.

## 2. Phạm vi sản phẩm

Hệ thống có đúng ba nhóm chức năng chính:

1. Chọn món từ menu, chọn số lượng/ghi chú và tạo một đơn hàng.
2. Đưa từng dòng món vào Queue FIFO, xử lý theo thứ tự và chuyển từ `QUEUED` sang `SERVED`.
3. Xem hóa đơn và xác nhận thanh toán; chỉ được thanh toán khi tất cả món của đơn đã `SERVED`.

Không triển khai quản lý bàn, báo cáo doanh thu, hủy đơn, thêm món sau khi đã tạo đơn, quản lý kho, đăng nhập, phân quyền, nhiều chi nhánh hoặc thanh toán trực tuyến.

## 3. Tác nhân

- Nhân viên đặt món: xem menu, chọn món, tạo đơn.
- Nhân viên bếp: xem Queue và xác nhận món đầu hàng đợi đã phục vụ.
- Thu ngân: xem hóa đơn, xác nhận thanh toán và hiển thị bill.

Các vai trò chỉ là cách mô tả người dùng; phiên bản này không có đăng nhập hoặc phân quyền.

## 4. Yêu cầu chức năng

### UC01 — Xem menu và chọn món

- Đầu vào: yêu cầu hiển thị menu, mã món, số lượng nguyên dương, ghi chú.
- Xử lý: menu được tra cứu qua Hash Map `dict` trong Repository; chỉ món còn bán xuất hiện khi đặt.
- Kết quả: giỏ hàng tạm hiển thị tên, mã, số lượng, thành tiền và ghi chú.
- Ngoại lệ: mã món không tồn tại/không còn bán hoặc số lượng không hợp lệ phải có thông báo.

### UC02 — Tạo đơn và enqueue

- Đầu vào: danh sách dòng món trong giỏ.
- Xử lý: kiểm tra dữ liệu; gộp các dòng cùng mã món và cùng ghi chú; chụp tên/giá hiện tại; tạo một Order; gán `queue_seq`; lưu Order vào `orders.json`; enqueue mỗi dòng món một Node.
- Kết quả: một đơn `OPEN`, tất cả dòng món có trạng thái `QUEUED` và nằm cuối Queue.
- Quy tắc: quantity không tạo thêm Node; quantity=3 vẫn là một Node.

### UC03 — Xử lý Queue và phục vụ món

- Đầu vào: thao tác xác nhận món tiếp theo đã phục vụ.
- Xử lý: xem Node ở `front`; tìm OrderItem tương ứng; ghi trạng thái `SERVED` vào JSON; nếu lưu thành công thì dequeue Node.
- Kết quả: món đầu hàng đợi đã `SERVED`, Queue còn các món tiếp theo.
- Ngoại lệ: Queue rỗng thì thông báo không có món chờ. Nếu ghi JSON thất bại thì Node phải ở lại Queue.

### UC04 — Thanh toán và hiển thị hóa đơn

- Đầu vào: mã Order được chọn và thao tác xác nhận.
- Xử lý: lấy toàn bộ Order; gom món trùng mã trong cùng Order; tính thành tiền bằng đơn giá snapshot × số lượng; kiểm tra tất cả món đều `SERVED`; đổi Order sang `PAID`; lưu thời gian và tổng tiền.
- Kết quả: hiển thị hóa đơn trong UI với mã đơn, món, số lượng, đơn giá, thành tiền và tổng thanh toán.
- Ngoại lệ: còn món `QUEUED`, đơn không tồn tại hoặc đã `PAID` thì từ chối thanh toán.

## 5. Cấu trúc dữ liệu bắt buộc

### Hash Map

- `MenuRepository._items_by_id: dict[str, MenuItem]`.
- `OrderRepository._orders_by_id: dict[str, Order]`.
- Tra cứu theo mã trung bình O(1).

### Queue OOP

- `Node`: chứa dữ liệu và con trỏ `next`.
- `Queue`: quản lý `front`, `rear`, `size`.
- `enqueue`, `dequeue`, `peek`, `is_empty`, `size`.
- Queue được cài đặt bằng Linked List; không dùng `collections.deque` hoặc list làm cấu trúc hàng đợi.

### Lưu trữ và khôi phục

- `menu.json`: danh sách món.
- `orders.json`: danh sách Order, các OrderItem, trạng thái và `queue_seq`.
- Khi khởi động, lấy các item `QUEUED` trong đơn `OPEN`, sắp xếp theo `queue_seq` và dựng lại Linked List.
- Mỗi lần tạo đơn và phục vụ món đều ghi JSON ngay; không chờ sự kiện đóng ứng dụng.

## 6. Trạng thái

```text
Order: OPEN → PAID
Item:  QUEUED → SERVED
```

Không có trạng thái trung gian `PREPARING`/`READY` trong phiên bản này. Không cho phép chuyển ngược trạng thái.

## 7. Yêu cầu phi chức năng

- UI Gradio có ba tab đúng với ba nhóm chức năng.
- UI không đọc/ghi JSON trực tiếp, không tự cài Queue, không tự tính tiền cuối cùng.
- Backend có thể kiểm thử độc lập không cần Gradio.
- Lỗi nhập liệu, trạng thái và lỗi lưu JSON được thông báo rõ ràng.
- Ứng dụng chạy một tiến trình Python; không cam kết an toàn khi nhiều tiến trình cùng ghi JSON.
- Dữ liệu tiền dùng số nguyên VND.
