# Phân công 5 thành viên — Backend-first, không quản lý bàn

Mỗi thành viên cần nêu được: **Input mình nhận → trách nhiệm của module → Output bàn giao → cách kiểm tra**. Không chỉ nhận file để code riêng.

## Thành viên 1 — Thanh Bình: Models, JSON, khởi tạo

**Input:** SRS đã chốt, `docs/API_CONTRACT.md`.

**Việc làm:**
- Giữ cấu trúc thư mục, quy tắc đặt tên và cấu trúc dữ liệu.
- Duy trì `MenuItem`, `Order`, `OrderItem`, enum trạng thái trong `src/fnb/models.py`.
- Duy trì `JsonStore` để đọc/ghi JSON; tạo mẫu `data/menu.json`, `data/orders.json`.
- Duy trì `bootstrap.py`, `exceptions.py`, README và lệnh chạy.
- Review mọi thay đổi ảnh hưởng đến schema; không để UI sửa trực tiếp JSON.

**Bàn giao:** Model chuyển qua lại dict được; file JSON mẫu hợp lệ; khởi tạo context không ghi đè dữ liệu có sẵn.

**Tự kiểm tra:** tạo Model → `to_dict()` → ghi JSON → khởi động Repository mới → nạp lại đúng dữ liệu.

## Thành viên 2 — Repository và Hash Map

**Input:** Model, JsonStore và schema do thành viên 1 chốt.

**Việc làm:**
- `MenuRepository` và `OrderRepository`.
- Lập chỉ mục bằng `dict` theo mã món/mã đơn; cung cấp `get_by_id`, `list_all`, `upsert`, và CRUD cơ bản nếu cần.
- Đồng bộ thay đổi với JSON và xử lý ID không tồn tại.
- Viết test tra cứu O(1) theo cách dùng dict, CRUD, và khởi động lại Repository.

**Không làm:** quy tắc hủy đơn, chuyển trạng thái bếp, tính giảm giá hay chỉnh UI.

**Bàn giao:** Repository test độc lập được; giải thích được Hash Map đang nằm ở đâu và vì sao tra cứu theo mã trung bình O(1).

## Thành viên 3 — Đơn hàng và bếp

**Input:** Models/Repository/API contract.

**Việc làm:**
- `MenuService`: danh sách món còn bán và tra cứu mã.
- `OrderService`: tạo đơn, thêm món, snapshot tên/giá, kiểm tra số lượng, hủy đơn hợp lệ.
- `KitchenService`: `deque` FIFO; xử lý `QUEUED → PREPARING → READY → SERVED`; khôi phục hàng đợi theo `queue_seq`.
- Controller cho Menu, Order và Kitchen.
- Test FIFO, thêm món vào cuối Queue, sai mã/số lượng, hủy không hợp lệ, khôi phục sau restart.

**Bàn giao:** Có thể tạo đơn từ input mẫu, xem Queue và xử lý trạng thái mà không cần Gradio.

## Thành viên 4 — Thanh toán và báo cáo

**Input:** Models/OrderRepository và API contract; thống nhất quy tắc trạng thái với thành viên 3.

**Việc làm:**
- `PaymentService.preview_bill()`: tạo hóa đơn xem trước từ giá snapshot.
- `PaymentService.checkout()`: kiểm tra trạng thái món; tính subtotal, giảm giá, tiền thanh toán; lưu phương thức, thời điểm, biên nhận; chặn thanh toán hai lần.
- `ReportService`: thống kê số đơn PAID và doanh thu theo ngày.
- Controller cho Payment và Report.
- Test còn món QUEUED/PREPARING, giảm giá sai, thanh toán thành công/lặp, báo cáo chỉ tính đơn PAID.

**Bàn giao:** Hóa đơn/biên nhận và báo cáo chạy qua Controller với các tình huống lỗi được kiểm tra.

## Thành viên 5 — Frontend Gradio và tích hợp

**Input:** Controller contract và Backend có thể import được.

**Việc làm:**
- Dựng màn hình menu, tạo/thêm đơn, hàng đợi bếp, thanh toán và báo cáo.
- Callback chỉ đọc input, gọi Controller, hiển thị kết quả/thông báo.
- Không tự tính tổng tiền, quản lý Queue hoặc sửa file JSON trong UI.
- Thực hiện demo từ tạo đơn đến thanh toán.

**Bàn giao:** Người dùng chạy một luồng liền mạch từ UI; các lỗi nghiệp vụ được hiển thị dễ hiểu.

## Trách nhiệm chung

- Mỗi người viết test cho phần mình.
- Nhánh riêng → PR về `develop` → review → merge; không push trực tiếp lên `main`/`develop`.
- Mọi thay đổi schema/API phải được báo nhóm và cập nhật `docs/API_CONTRACT.md`.
- Trong project này không triển khai nghiệp vụ bàn ăn; không tạo `TableService`, `TableRepository` hoặc `table_id` trong đơn.
