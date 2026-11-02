# TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM

**Tên hệ thống:** Hệ thống Quản lý Đơn hàng F&B (Nhà hàng đơn giản)  
**Phiên bản:** 1.0.3 — phạm vi đã điều chỉnh: dùng JSON, không quản lý bàn  
**Ngày cập nhật:** 14/10/2026

## 1. Giới thiệu

### 1.1. Mục đích

Tài liệu thống nhất phạm vi, chức năng và tiêu chí nghiệm thu cho phiên bản đồ án F&B. Tài liệu này là căn cứ chung để chia việc, triển khai và kiểm thử.

### 1.2. Phạm vi

Hệ thống hỗ trợ xem thực đơn, tạo đơn và thêm món, xử lý hàng đợi bếp, cập nhật trạng thái món, xem hóa đơn, thanh toán mô phỏng, hủy đơn hợp lệ, báo cáo doanh thu ngày và khôi phục dữ liệu sau khi khởi động lại.

Phiên bản này **không triển khai quản lý bàn ăn**, đăng nhập/phân quyền, đặt bàn trước, tồn kho, nhiều chi nhánh, thanh toán trực tuyến thực tế hoặc đồng bộ nhiều máy.

### 1.3. Thuật ngữ

| Thuật ngữ | Ý nghĩa |
|---|---|
| SRS | Software Requirements Specification — đặc tả yêu cầu phần mềm |
| F&B | Food and Beverage — lĩnh vực ăn uống |
| Use case | Tình huống sử dụng nhằm đạt một mục tiêu cụ thể |
| Queue / FIFO | Hàng đợi; phần tử vào trước được xử lý trước |
| Hash Map | Cấu trúc ánh xạ khóa sang giá trị; trong Python dùng `dict` |
| Snapshot giá | Tên và giá món được lưu tại thời điểm đặt để hóa đơn cũ không đổi theo menu |
| JSON | Định dạng văn bản có cấu trúc dùng để lưu dữ liệu |

### 1.4. Tài liệu tham khảo

- `docs/ARCHITECTURE.md` — kiến trúc và luồng nghiệp vụ.
- `docs/API_CONTRACT.md` — chữ ký hàm giữa các lớp.
- `docs/MEMBER_TASKS.md` — phạm vi công việc của 5 thành viên.
- Perforce, *How to Write a Software Requirements Specification (SRS) Document*: https://www.perforce.com/blog/alm/how-write-software-requirements-specification-srs-document

### 1.5. Tổng quan kỹ thuật

Ứng dụng chạy trong một tiến trình Python; giao diện trình duyệt được xây dựng bằng Gradio. Dữ liệu lâu dài lưu trong file `data/menu.json` và `data/orders.json`. Source được chia thành UI, Controller, Service, Repository, Models và Storage. Mẫu dữ liệu chỉ được sao chép khi file đích chưa tồn tại; không ghi đè dữ liệu người dùng.

## 2. Yêu cầu chức năng

### 2.1. Tác nhân

| Tác nhân | Hoạt động chính |
|---|---|
| Nhân viên phục vụ | Xem thực đơn, tạo đơn/thêm món, xác nhận món đã phục vụ |
| Nhân viên bếp | Xem Queue, nhận món tiếp theo, xác nhận chế biến xong |
| Thu ngân | Xem hóa đơn và xác nhận thanh toán mô phỏng |
| Quản lý | Xem doanh thu ngày, hủy đơn hợp lệ |

Các tác nhân mô tả nhu cầu sử dụng, không phải cơ chế phân quyền tài khoản. Phiên bản đầu chưa có đăng nhập.

### 2.2. Danh sách chức năng

| Mã | Chức năng | Kết quả mong đợi |
|---|---|---|
| UC01 | Xem thực đơn / tra cứu món | Hiển thị món còn bán hoặc thông tin món theo mã |
| UC02 | Tạo đơn | Lưu một đơn `OPEN`, các dòng món được đưa vào Queue |
| UC03 | Thêm món | Bổ sung dòng món vào đơn `OPEN` và cuối Queue |
| UC04 | Cập nhật trạng thái món | Chuyển trạng thái theo đúng thứ tự quy định |
| UC05 | Xem hóa đơn / thanh toán | Lưu thanh toán hợp lệ và hiển thị biên nhận |
| UC06 | Hủy đơn | Giữ lịch sử hủy và loại món chờ của đơn khỏi Queue |
| UC07 | Báo cáo ngày | Tổng số đơn đã thanh toán và doanh thu theo ngày |
| UC08 | Khôi phục dữ liệu | Đọc JSON và dựng lại đúng Queue khi khởi động |

### 2.3. Đặc tả UC01 — Xem thực đơn / tra cứu món

- **Điều kiện trước:** `menu.json` đọc được và thực đơn đã được nạp.
- **Đầu vào:** yêu cầu danh sách món hoặc mã món.
- **Luồng chính:** hệ thống tra cứu bằng mã trong Hash Map và hiển thị mã, tên, nhóm, giá, tình trạng còn bán.
- **Ngoại lệ:** mã không tồn tại thì báo không tìm thấy; danh sách dùng để đặt món chỉ hiển thị món còn bán.
- **Kết quả:** dữ liệu được hiển thị, không tự thay đổi thực đơn.

### 2.4. Đặc tả UC02 — Tạo đơn

- **Điều kiện trước:** thực đơn đã được nạp.
- **Đầu vào:** ít nhất một dòng `{menu_item_id, quantity, note}`.
- **Luồng chính:**
  1. Kiểm tra danh sách không rỗng, mã món tồn tại và đang được bán.
  2. Kiểm tra `quantity` là số nguyên dương.
  3. Tạo mã đơn và mã cho từng dòng món; lưu tên và giá món tại thời điểm đặt.
  4. Lưu đơn với trạng thái `OPEN`; các dòng món bắt đầu ở `QUEUED`.
  5. Đưa mỗi dòng món vào cuối Queue với `queue_seq` tăng dần.
- **Ngoại lệ:** mã món sai, món không còn bán, số lượng không hợp lệ hoặc lỗi lưu dữ liệu thì từ chối và báo lỗi.
- **Kết quả:** đơn được lưu vào `orders.json`; Queue phản ánh các dòng món đang chờ.

### 2.5. Đặc tả UC03 — Thêm món

- **Điều kiện trước:** đơn tồn tại và có trạng thái `OPEN`.
- **Đầu vào:** mã đơn cùng danh sách món bổ sung.
- **Luồng chính:** kiểm tra đơn, mã món, tình trạng bán và số lượng; tạo dòng món mới kèm snapshot tên/giá; lưu đơn; thêm những dòng mới vào cuối Queue.
- **Ngoại lệ:** không tìm thấy đơn/món, món ngừng bán, số lượng sai hoặc đơn đã `PAID`/`CANCELLED` thì từ chối.
- **Kết quả:** đơn có các dòng món mới, thứ tự Queue hiện có được giữ nguyên.

### 2.6. Đặc tả UC04 — Cập nhật trạng thái món

- **Điều kiện trước:** dòng món tồn tại, thuộc đơn `OPEN` và trạng thái hiện tại phù hợp.
- **Đầu vào:** mã đơn, mã dòng món và thao tác đích.
- **Luồng chính:**
  1. Bếp chọn món đầu Queue; món chuyển `QUEUED` → `PREPARING`.
  2. Bếp xác nhận chế biến xong; món chuyển `PREPARING` → `READY`.
  3. Nhân viên phục vụ xác nhận đã đưa món ra; món chuyển `READY` → `SERVED`.
  4. Lưu trạng thái mới vào JSON.
- **Ngoại lệ:** không cho bỏ qua bước, chuyển ngược trạng thái hoặc cập nhật món của đơn đã đóng.
- **Kết quả:** trạng thái được lưu và còn nguyên sau khi khởi động lại.

### 2.7. Đặc tả UC05 — Xem hóa đơn / thanh toán

- **Điều kiện trước:** đơn ở trạng thái `OPEN`; mọi dòng món đã `READY` hoặc `SERVED`.
- **Đầu vào:** mã đơn, phương thức thanh toán mô phỏng và mức giảm giá nguyên VND.
- **Luồng chính:**
  1. Tính hóa đơn từ tên, giá snapshot và số lượng đã lưu.
  2. Tính `subtotal = Σ(unit_price × quantity)`.
  3. Kiểm tra giảm giá là số nguyên không âm và không vượt subtotal.
  4. Khi xác nhận, lưu `total_before_discount`, `discount_amount`, `total_paid`, `payment_method`, `paid_at` và trạng thái `PAID`.
  5. Hiển thị biên nhận từ dữ liệu đã lưu.
- **Ngoại lệ:** từ chối nếu còn món `QUEUED`/`PREPARING`, giảm giá sai, không tìm thấy đơn hoặc đơn đã thanh toán/hủy.
- **Kết quả:** thanh toán được ghi nhận một lần; đơn vẫn được giữ trong lịch sử.
- **Giới hạn:** phương thức thanh toán chỉ để mô phỏng, không kết nối cổng thanh toán thật.

### 2.8. Đặc tả UC06 — Hủy đơn

- **Điều kiện trước:** đơn `OPEN`, có ít nhất một dòng món và tất cả dòng món vẫn `QUEUED`.
- **Đầu vào:** mã đơn và lý do hủy tùy chọn.
- **Luồng chính:** kiểm tra điều kiện hủy; chuyển đơn sang `CANCELLED`, chuyển các dòng món sang `CANCELLED`, lưu thời điểm/lý do hủy và loại các dòng món của đơn khỏi Queue.
- **Ngoại lệ:** từ chối nếu có món đã chuyển sang `PREPARING`, `READY` hoặc `SERVED`, hoặc đơn đã đóng.
- **Kết quả:** đơn hủy vẫn còn trong lịch sử; không còn món của đơn trong Queue.

### 2.9. Đặc tả UC07 — Báo cáo doanh thu ngày

- **Đầu vào:** ngày theo định dạng `YYYY-MM-DD`; bỏ trống thì dùng ngày hiện tại.
- **Luồng chính:** lọc các đơn `PAID` có ngày `paid_at` trùng ngày yêu cầu; đếm số đơn và cộng `total_paid`.
- **Ngoại lệ:** ngày sai định dạng thì thông báo lỗi.
- **Kết quả:** ngày báo cáo, số đơn đã thanh toán, doanh thu VND và danh sách mã đơn được hiển thị.

### 2.10. Đặc tả UC08 — Khôi phục dữ liệu

- **Điều kiện trước:** các file JSON hiện có đọc được.
- **Luồng chính:** nạp thực đơn và đơn; dựng Hash Map theo mã; tìm dòng món của đơn `OPEN` có trạng thái `QUEUED`; sắp xếp theo `queue_seq`; dựng lại `deque`.
- **Quy tắc:** món `PREPARING` vẫn giữ trạng thái đã lưu nhưng không tự đưa lại vào Queue; đơn `PAID`/`CANCELLED` không tạo task chờ.
- **Ngoại lệ:** JSON lỗi hoặc cấu trúc không hợp lệ thì báo lỗi đọc dữ liệu, không âm thầm thay bằng dữ liệu trống.

### 2.11. Quy tắc nghiệp vụ

- Số lượng là số nguyên dương. Giá và tiền dùng số nguyên VND, không âm.
- Tên và giá món lưu trong từng dòng đơn tại thời điểm đặt; cập nhật menu không làm đổi hóa đơn cũ.
- Một dòng món có số lượng `n` là **một mục Queue**, không tách thành `n` mục.
- Trạng thái món: `QUEUED → PREPARING → READY → SERVED`.
- Trạng thái đơn: `OPEN → PAID` hoặc `OPEN → CANCELLED` khi thỏa điều kiện hủy.
- Chỉ thanh toán đơn `OPEN` khi mọi món `READY` hoặc `SERVED`.
- `total_paid = total_before_discount − discount_amount`; giảm giá không âm và không vượt subtotal.
- Không thanh toán lại; không xóa vật lý đơn đã `PAID` hoặc `CANCELLED`.
- Chỉ hủy khi tất cả dòng món còn `QUEUED`.
- Khôi phục chỉ đưa dòng món `QUEUED` thuộc đơn `OPEN` vào Queue theo `queue_seq`.

**Ví dụ tính tiền:** 2 phần món giá 55.000 VND và 1 đồ uống giá 18.000 VND có subtotal 128.000 VND. Giảm giá 8.000 VND thì tiền thanh toán là 120.000 VND.

## 3. Yêu cầu phi chức năng

### 3.1. Giao diện và trải nghiệm

- **NFR01:** các khu vực thực đơn, đơn hàng, bếp/Queue, thanh toán và báo cáo phải có nhãn rõ ràng.
- **NFR02:** thao tác thành công và lỗi nhập liệu phải có thông báo dễ hiểu; không hiển thị traceback/chi tiết lỗi lập trình.
- **Kiểm tra:** thử mã món sai, số lượng 0, hủy đơn có món đang chế biến và thanh toán khi còn món chờ; hệ thống cần giải thích vì sao từ chối.

### 3.2. Lưu trữ và hiệu năng

- **NFR03:** dữ liệu đã lưu thành công phải còn sau khi đóng/mở ứng dụng; lỗi đọc/ghi phải được báo.
- **NFR04:** tra cứu món theo mã dùng Hash Map (`dict`); Queue hỗ trợ FIFO.
- **NFR05:** khi khởi động, khôi phục đúng thứ tự các dòng món đang chờ và không đưa dòng `PREPARING` quay lại Queue.
- **Giới hạn:** chưa đặt ngưỡng thời gian phản hồi hay số người dùng đồng thời; JSON chỉ dành cho một tiến trình ghi tại một thời điểm.

### 3.3. Kiểm tra dữ liệu và bảo mật

- **NFR06:** hệ thống kiểm tra mã, số lượng, giảm giá và trạng thái trước khi sửa dữ liệu; tổng tiền được backend tính từ giá đã lưu.
- **NFR07:** lỗi ngoài dự kiến được giữ đủ thông tin ở nơi chạy ứng dụng để chẩn đoán; UI chỉ hiển thị thông báo chung.
- **Giới hạn:** phiên bản đầu chưa có đăng nhập/phân quyền.

### 3.4. Ràng buộc kỹ thuật

- **NFR08:** sử dụng Python, Gradio, JSON và `uv` theo cấu hình dự án.
- **NFR09:** tách UI, Controller, Service, Repository, Models và Storage; UI không tự sửa JSON hoặc tự tính số tiền thanh toán.
- **NFR10:** dữ liệu mẫu chỉ được sao chép khi file đích chưa tồn tại; không ghi đè dữ liệu hiện có.
- Không tích hợp SQL, kho hàng, nhiều chi nhánh, thanh toán trực tuyến thật hoặc quản lý bàn ăn trong phiên bản này.

## 4. Điều kiện nghiệm thu MVP

- Có thể xem danh sách món còn bán và tra cứu món theo mã.
- Tạo đơn và thêm món có validate, snapshot giá và lưu JSON.
- Chứng minh Queue FIFO bằng `deque` và Hash Map tra cứu menu bằng `dict`.
- Chuyển trạng thái món đúng luồng, không bỏ qua bước.
- Chỉ hủy đơn hợp lệ; đơn hủy vẫn được giữ và không còn task trong Queue.
- Hóa đơn tính đúng subtotal, giảm giá, tổng thanh toán; chặn thanh toán lần hai.
- Báo cáo ngày chỉ tính đơn `PAID`.
- Khởi động lại ứng dụng vẫn giữ dữ liệu và khôi phục đúng Queue.
- Chạy test tự động và khởi động Gradio từ lệnh đã nêu trong README.
