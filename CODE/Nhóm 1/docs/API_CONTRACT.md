# Hợp đồng API nội bộ (các hàm Python)

Mục đích của file này là để các bạn chia việc mà không phải đoán tên hàm hoặc định dạng dữ liệu. Nếu muốn đổi hợp đồng, hãy bàn trong nhóm và cập nhật file này trong cùng PR.

## 1. Model chính

### MenuItem

```python
MenuItem(id: str, name: str, price: int, is_available: bool = True)
```

`price` là số nguyên VND, tránh số thực cho tiền.

### RestaurantTable

```python
RestaurantTable(
    id: str,
    name: str,
    status: TableStatus = TableStatus.AVAILABLE,
    current_order_id: str | None = None,
)
```

### OrderItem

```python
OrderItem(
    id: str,
    menu_item_id: str,
    name: str,                 # snapshot tên món
    unit_price: int,           # snapshot giá lúc gọi món
    quantity: int,
    note: str = "",
    status: ItemStatus = ItemStatus.QUEUED,
    queue_seq: int = 0,
)
```

### Order

```python
Order(
    id: str,
    table_id: str,
    items: list[OrderItem],
    status: OrderStatus = OrderStatus.OPEN,
    created_at: str = ...,
    paid_at: str | None = None,
    total_paid: int | None = None,
)
```

## 2. Repository contract

Các Repository cung cấp cách gọi tương tự:

```python
get_by_id(item_id: str) -> Model | None
list_all() -> list[Model]
upsert(item: Model) -> None
delete(item_id: str) -> bool
```

Không tìm thấy mã: `get_by_id()` trả `None`; Service quyết định có báo `NotFoundError` hay không. Repository không nên quyết định luật như “bàn đang bận thì không được đặt món”.

## 3. Service contract

```python
# MenuService
list_menu() -> list[MenuItem]
get_item(menu_item_id: str) -> MenuItem

# OrderService
create_order(table_id: str, lines: list[dict]) -> Order
get_order(order_id: str) -> Order
list_orders() -> list[Order]
cancel_order(order_id: str) -> Order

# KitchenService
get_queue() -> list[dict]
start_next_item() -> dict
mark_item_ready(order_id: str, order_item_id: str) -> OrderItem
mark_item_served(order_id: str, order_item_id: str) -> OrderItem

# TableService
list_tables() -> list[RestaurantTable]
get_table(table_id: str) -> RestaurantTable

# PaymentService
checkout(order_id: str) -> Order

# ReportService
daily_summary(day: str | None = None) -> dict
```

`lines` ví dụ:

```json
[
  {"menu_item_id": "MI-001", "quantity": 2, "note": "Ít hành"},
  {"menu_item_id": "MI-008", "quantity": 1, "note": ""}
]
```

UI không gửi `unit_price`/`total_paid` để backend tin dùng. Backend tự lấy giá đã lưu trong menu.

## 4. Controller contract (giao tiếp với UI)

```python
menu_controller.list_menu() -> list[dict]
table_controller.list_tables() -> list[dict]
order_controller.create_order(table_id: str, lines: list[dict]) -> dict
order_controller.get_order(order_id: str) -> dict
kitchen_controller.get_queue() -> list[dict]
kitchen_controller.start_next_item() -> dict
kitchen_controller.mark_item_ready(order_id: str, item_id: str) -> dict
kitchen_controller.mark_item_served(order_id: str, item_id: str) -> dict
payment_controller.checkout(order_id: str) -> dict
report_controller.daily_summary(day: str | None = None) -> dict
```

Controller trả dict/list để UI dễ hiển thị. Service làm việc với Model. Lỗi nghiệp vụ được thể hiện bằng exception thuộc `FNBError`; UI có thể bắt lỗi để hiện thông báo thân thiện.

## 5. Các lỗi thống nhất

- `ValidationError`: input sai, ví dụ số lượng <= 0.
- `NotFoundError`: không có mã bàn/món/đơn.
- `ConflictError`: bàn đang được sử dụng hoặc xung đột dữ liệu.
- `InvalidStateError`: chuyển trạng thái không hợp lệ hoặc thanh toán đơn đã thanh toán.
- `StorageError`: JSON hỏng hoặc không đọc/ghi được.
