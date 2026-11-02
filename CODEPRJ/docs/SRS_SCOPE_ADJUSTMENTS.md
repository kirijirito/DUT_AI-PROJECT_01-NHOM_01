# Các điều chỉnh SRS để thống nhất với phạm vi đã chốt

Bản đặc tả đã biên tập đầy đủ trong gói này là [`SRS_FNB_v1.0.3.md`](SRS_FNB_v1.0.3.md). File hiện tại ghi lại các khác biệt quan trọng so với SRS mà nhóm gửi ban đầu.

Quyết định hiện tại của nhóm: **lưu bằng JSON** và **không triển khai nghiệp vụ quản lý bàn ăn**. Vì SRS được gửi trước đó vẫn chứa yêu cầu về bàn, bản SRS chính thức cần cập nhật để không mâu thuẫn với code.

## Cập nhật mục 1.2 — Phạm vi

Thay nội dung phạm vi bằng: Hệ thống hỗ trợ xem thực đơn, tạo đơn và thêm món, xử lý Queue bếp, cập nhật trạng thái món, xem hóa đơn, thanh toán mô phỏng, hủy đơn hợp lệ, báo cáo doanh thu ngày và khôi phục dữ liệu từ JSON. Không triển khai quản lý bàn, đăng nhập/phân quyền, đặt bàn trước, nhiều chi nhánh, tồn kho, thanh toán trực tuyến thực tế hoặc đồng bộ nhiều máy.

## Cập nhật mục 2.1 — Tác nhân

- Nhân viên phục vụ: xem thực đơn, tạo/thêm món vào đơn và xác nhận món đã phục vụ.
- Nhân viên bếp: xem hàng chờ, nhận món tiếp theo và xác nhận chế biến xong.
- Thu ngân: xem hóa đơn và xác nhận thanh toán mô phỏng.
- Quản lý: xem doanh thu ngày và hủy đơn hợp lệ.

Các vai trò chỉ mô tả nhu cầu nghiệp vụ; phiên bản đầu chưa triển khai đăng nhập hoặc phân quyền.

## Cập nhật mục 2.2 — Chức năng

Giữ UC01–UC06 và làm rõ UC05 có xem hóa đơn/biên nhận, UC06 lưu lý do hủy nếu có. Bổ sung báo cáo ngày và khôi phục dữ liệu vào danh sách chức năng hoặc yêu cầu phi chức năng cần nghiệm thu.

## Sửa đặc tả use case

- **UC02 Tạo đơn:** bỏ điều kiện trước “Bàn tồn tại và đang trống”. Đầu vào chỉ gồm danh sách mã món, số lượng nguyên dương và ghi chú tùy chọn. Kết quả là một đơn `OPEN`; các dòng món được lưu và thêm vào Queue.
- **UC03 Thêm món:** bổ sung các dòng mới vào một đơn `OPEN`; dòng mới có ID, snapshot tên/giá và sequence Queue mới. Từ chối nếu đơn đã `PAID`/`CANCELLED`.
- **UC05 Thanh toán:** bỏ bước “giải phóng bàn”. Sau xác nhận, lưu `PAID`, tổng tiền trước giảm giá, giảm giá, tổng tiền thực trả, phương thức và thời điểm; hiển thị biên nhận. Chỉ thanh toán khi mọi món `READY` hoặc `SERVED`.
- **UC06 Hủy đơn:** bỏ bước “giải phóng bàn”. Giữ lịch sử đơn hủy và loại các món của đơn khỏi Queue. Chỉ cho hủy khi đơn `OPEN` và mọi món còn `QUEUED`.
- **Quy tắc nghiệp vụ:** xóa các quy tắc phụ thuộc bàn; giữ snapshot giá, FIFO, giảm giá hợp lệ, giữ lịch sử thanh toán/hủy và khôi phục các món `QUEUED` theo `queue_seq`.

## Cập nhật mục 3.4 — Ràng buộc kỹ thuật

Giữ Python, Gradio, JSON, một tiến trình và phân lớp. Thư mục dữ liệu mẫu là `data/menu.json` và `data/orders.json`; dữ liệu mẫu chỉ được sao chép nếu file đích chưa tồn tại, không được ghi đè dữ liệu hiện có.
