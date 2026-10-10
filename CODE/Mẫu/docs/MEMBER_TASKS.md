# Phân công 5 thành viên: Input → Việc làm → Output

Nguyên tắc: mỗi người phải hiểu **mình nhận gì, chịu trách nhiệm gì, bàn giao gì và kiểm tra bằng cách nào**. Không chỉ nhận một danh sách file rồi code riêng.

## Thành viên 1 — Thanh Bình: nền tảng, Models, Schema, khởi tạo

**Bạn nhận:** yêu cầu nghiệp vụ đã chốt và `docs/API_CONTRACT.md`.

**Bạn làm:**
- Giữ cấu trúc thư mục và quy tắc tên chung.
- Định nghĩa Model/Enum trong `src/fnb/models.py`.
- Định nghĩa lỗi dùng chung trong `exceptions.py`.
- Viết `JsonStore` đọc/ghi JSON an toàn cơ bản.
- Chuẩn bị `data/menu.json`, `data/tables.json`, `data/orders.json`.
- Dựng `bootstrap.py` để lắp các lớp và tài liệu cách chạy.
- Review thay đổi ảnh hưởng đến Schema; không tự ý đổi tên trường giữa chừng.

**Bạn bàn giao:** lớp Model có `to_dict/from_dict`, file JSON mẫu đọc được, khởi động context được và test lưu/đọc cơ bản.

**Tiêu chí xong:** một người khác có thể tạo Model, chuyển nó thành dict, lưu JSON rồi đọc lại mà không cần hỏi bạn.

## Thành viên 2 — Repository: CRUD và Hash Map

**Bạn nhận:** Models, JsonStore, cấu trúc JSON đã chốt từ thành viên 1.

**Bạn làm:**
- `MenuRepository`, `TableRepository`, `OrderRepository`.
- Dùng dict `{id: object}` trong bộ nhớ để tra cứu theo ID trung bình O(1).
- Cung cấp `get_by_id`, `list_all`, `upsert`, `delete` theo contract.
- Mỗi lần thay đổi phải đồng bộ lại JSON.
- Viết test CRUD, ID không tồn tại, dữ liệu được giữ sau khi tạo Repository mới.

**Bạn không làm:** quy tắc bếp, tính tiền, cập nhật giao diện hay tự quyết định bàn có được đặt không.

**Bạn bàn giao:** Repository chạy độc lập và test được; giải thích rõ Hash Map nằm ở đâu.

## Thành viên 3 — Service/Controller: menu, đơn hàng, bếp

**Bạn nhận:** Models/Repository và contract; phối hợp với thành viên 4 về TableService.

**Bạn làm:**
- `MenuService`: lấy menu, tra món, từ chối món không còn bán.
- `OrderService`: validate input, tạo Order/OrderItem, snapshot tên và giá, xếp `queue_seq`.
- `KitchenService`: Queue FIFO dùng `deque`, khôi phục Queue khi app khởi động, đổi trạng thái món.
- `MenuController`, `OrderController`, `KitchenController`: chuyển lời gọi UI sang Service.
- Test: món đầu tiên được lấy trước; quantity không hợp lệ bị từ chối; trạng thái đổi đúng; Queue dựng lại sau restart.

**Bạn không làm:** tính thanh toán cuối cùng hoặc viết callback Gradio.

**Bạn bàn giao:** tạo đơn từ input mẫu được, món vào Queue theo thứ tự và trạng thái được lưu JSON.

## Thành viên 4 — Service/Controller: bàn, thanh toán, báo cáo

**Bạn nhận:** Models/Repository và contract; phối hợp với thành viên 3 về cách OrderService sử dụng TableService/KitchenService.

**Bạn làm:**
- `TableService`: xem bàn, kiểm tra bàn trống, gắn đơn vào bàn và giải phóng bàn đúng đơn.
- `PaymentService`: tính tổng từ snapshot `unit_price * quantity`; chỉ checkout khi món đã READY/SERVED; chống checkout lần hai.
- `ReportService`: tổng số đơn PAID và doanh thu theo ngày.
- `TableController`, `PaymentController`, `ReportController`.
- Test thanh toán khi còn QUEUED/PREPARING, thanh toán thành công, thanh toán trùng, bàn được giải phóng, báo cáo chỉ tính đơn PAID.

**Bạn không làm:** tự sửa UI hoặc tự xóa đơn đã PAID để “reset” dữ liệu.

**Bạn bàn giao:** luồng checkout và report chạy được qua Controller, có test thể hiện các quy tắc.

## Thành viên 5 — Frontend Gradio và tích hợp

**Bạn nhận:** Controller contract và một bản backend có thể import được. Trong lúc chờ, có thể làm prototype bằng dữ liệu giả nhưng phải thay bằng Controller trước khi merge cuối.

**Bạn làm:**
- Xây UI hiển thị menu/bàn/đơn và các nút thao tác.
- Callback chỉ đọc input, gọi Controller, hiển thị output/lỗi.
- Không import Repository để tự sửa JSON; không tự quản lý Queue trong UI.
- Tích hợp luồng tạo đơn → bếp → thanh toán.
- Kiểm thử thao tác người dùng thực tế và thông báo thành công/thất bại.

**Bạn bàn giao:** UI có thể demo luồng chính liên tục mà không cần chạy từng hàm thủ công.

## Trách nhiệm chung

- Mỗi người viết test cho phần mình.
- Mỗi PR mô tả thay đổi, cách test và ảnh hưởng contract.
- Không sửa trực tiếp nhánh `main`/`develop`; dùng feature branch và PR.
- Khi thay đổi Model/contract, phải thông báo cả nhóm trước khi merge.
