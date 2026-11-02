# Hợp đồng API nội bộ

Mục đích: tất cả thành viên dùng chung tên hàm, kiểu input/output và ý nghĩa trạng thái. Nếu thay đổi contract, cần cập nhật file này trong cùng PR.

## 1. Model chính

```python
MenuItem(id: str, name: str, price: int, category: str = "Khác", is_available: bool = True)

OrderItem(
    id: str,
    menu_item_id: str,
    name: str,                 # snapshot tên món lúc gọi
    unit_price: int,           # snapshot giá lúc gọi, VND
    quantity: int,             # số nguyên dương
    note: str = "",
    status: ItemStatus = ItemStatus.QUEUED,
    queue_seq: int = 0,
)

Order(
    id: str,
    items: list[OrderItem],
    status: OrderStatus = OrderStatus.OPEN,
    created_at: str = ...,
    paid_at: str | None = None,
    total_before_discount: int | None = None,
    discount_amount: int = 0,
    total_paid: int | None = None,
    payment_method: str | None = None,
    cancelled_at: str | None = None,
    cancel_reason: str = "",
)
```

Trạng thái đơn: `OPEN`, `PAID`, `CANCELLED`. Trạng thái dòng món: `QUEUED`, `PREPARING`, `READY`, `SERVED`, `CANCELLED`.

## 2. Repository contract

```python
# MenuRepository
get_by_id(menu_item_id: str) -> MenuItem | None
list_all() -> list[MenuItem]
upsert(item: MenuItem) -> None

# OrderRepository
get_by_id(order_id: str) -> Order | None
list_all() -> list[Order]
upsert(order: Order) -> None
delete(order_id: str) -> bool  # CRUD nền tảng; Service không xóa đơn PAID/CANCELLED
```

Tra cứu `get_by_id` dùng `dict` theo ID, trung bình O(1). `JsonStore` chỉ làm nhiệm vụ nạp/ghi file JSON.

## 3. Service contract

```python
# MenuService
list_menu(available_only: bool = True) -> list[MenuItem]
get_item(menu_item_id: str) -> MenuItem

# OrderService
create_order(lines: list[dict]) -> Order
add_items(order_id: str, lines: list[dict]) -> Order
get_order(order_id: str) -> Order
list_orders() -> list[Order]
cancel_order(order_id: str, reason: str = "") -> Order

# KitchenService
get_queue() -> list[dict]
start_next_item() -> dict
mark_item_ready(order_id: str, order_item_id: str) -> OrderItem
mark_item_served(order_id: str, order_item_id: str) -> OrderItem

# PaymentService
preview_bill(order_id: str, discount_amount: int | None = None) -> dict
checkout(order_id: str, payment_method: str = "CASH", discount_amount: int = 0) -> Order

# ReportService
daily_summary(day: str | None = None) -> dict
```

`lines` có dạng:

```json
[
  {"menu_item_id": "MI-001", "quantity": 2, "note": "Ít sốt"},
  {"menu_item_id": "MI-008", "quantity": 1, "note": ""}
]
```

UI không gửi giá để backend tin dùng. Backend lấy giá từ menu và lưu snapshot trong `OrderItem`.

## 4. Controller contract — giao tiếp với UI

```python
menu_controller.list_menu(available_only=True) -> list[dict]
menu_controller.get_item(menu_item_id) -> dict
order_controller.create_order(lines) -> dict
order_controller.add_items(order_id, lines) -> dict
order_controller.get_order(order_id) -> dict
order_controller.list_orders() -> list[dict]
order_controller.cancel_order(order_id, reason="") -> dict
kitchen_controller.get_queue() -> list[dict]
kitchen_controller.start_next_item() -> dict
kitchen_controller.mark_item_ready(order_id, item_id) -> dict
kitchen_controller.mark_item_served(order_id, item_id) -> dict
payment_controller.preview_bill(order_id, discount_amount=None) -> dict
payment_controller.checkout(order_id, payment_method="CASH", discount_amount=0) -> dict
report_controller.daily_summary(day=None) -> dict
```

## 5. Quy tắc dữ liệu và lỗi

- Tiền dùng số nguyên VND; không dùng float để tính tiền.
- Số lượng phải là số nguyên dương; giảm giá là số nguyên không âm và không vượt subtotal.
- Chỉ checkout đơn `OPEN` khi tất cả dòng món là `READY` hoặc `SERVED`.
- Chỉ hủy đơn `OPEN` khi tất cả dòng món còn `QUEUED`.
- Lỗi nghiệp vụ thuộc `FNBError`: `ValidationError`, `NotFoundError`, `InvalidStateError`, `StorageError`.
- Controller trả dict/list để UI hiển thị; lỗi nghiệp vụ được ném bằng exception và UI chuyển thành thông báo thân thiện.
