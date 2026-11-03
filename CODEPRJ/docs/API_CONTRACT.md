# Hợp đồng API nội bộ

Các thành viên giữ thống nhất tên hàm, input/output và quy tắc trạng thái. Thay đổi contract phải cập nhật tài liệu trong cùng PR.

## 1. Model

```python
MenuItem(id, name, price, category, is_available)

OrderItem(
    id, menu_item_id, name, unit_price, quantity,
    note="", status=ItemStatus.QUEUED, queue_seq=0
)

Order(id, items, status=OrderStatus.OPEN, created_at, paid_at=None, total_paid=None)
```

Trạng thái Order: `OPEN`, `PAID`. Trạng thái món: `QUEUED`, `SERVED`.

## 2. Queue OOP

```python
class Node:
    data
    next

class Queue:
    front
    rear
    enqueue(item) -> None
    dequeue() -> item | None
    peek() -> item | None
    is_empty() -> bool
    size() -> int
    to_list() -> list
```

Queue là Linked List tự cài đặt; không sử dụng `deque` hoặc list để thực hiện enqueue/dequeue.

## 3. Repository

```python
# MenuRepository
get_by_id(menu_item_id: str) -> MenuItem | None
list_all() -> list[MenuItem]

# OrderRepository
get_by_id(order_id: str) -> Order | None
list_all() -> list[Order]
upsert(order: Order) -> None
```

`get_by_id` tra cứu qua `dict` theo ID, trung bình O(1).

## 4. Service

```python
# MenuService
list_menu(available_only: bool = True) -> list[MenuItem]
get_item(menu_item_id: str) -> MenuItem

# OrderService
create_order(lines: list[dict]) -> Order
get_order(order_id: str) -> Order
list_orders() -> list[Order]

# KitchenService
get_queue() -> list[dict]
get_served_items() -> list[dict]
serve_next_item() -> dict

# PaymentService
list_unpaid_orders() -> list[Order]
preview_bill(order_id: str) -> dict
checkout(order_id: str) -> Order
```

Input tạo đơn:

```json
[
  {"menu_item_id": "MI-001", "quantity": 2, "note": "ít sốt"},
  {"menu_item_id": "MI-009", "quantity": 1, "note": ""}
]
```

## 5. Controller dùng từ UI

```python
menu_controller.list_menu(available_only=True) -> list[dict]
menu_controller.get_item(menu_item_id) -> dict
order_controller.create_order(lines) -> dict
order_controller.get_order(order_id) -> dict
order_controller.list_orders() -> list[dict]
kitchen_controller.get_queue() -> list[dict]
kitchen_controller.get_served_items() -> list[dict]
kitchen_controller.serve_next_item() -> dict
payment_controller.list_unpaid_orders() -> list[dict]
payment_controller.preview_bill(order_id) -> dict
payment_controller.checkout(order_id) -> dict
```

## 6. Quy tắc dữ liệu

- Giá lưu bằng số nguyên VND; không dùng float để tính tiền.
- Số lượng là số nguyên dương.
- Tên món và giá được chụp tại thời điểm tạo đơn.
- Món trùng mã và cùng ghi chú trong một lượt đặt được gộp số lượng.
- Mỗi dòng OrderItem là một phần tử Queue; quantity không nhân số Node.
- Queue global được sắp xếp theo `queue_seq`.
- Chỉ `serve_next_item()` được phép lấy phần tử đầu và chuyển món sang `SERVED`.
- Chỉ thanh toán đơn `OPEN` khi tất cả món đều `SERVED`; không thanh toán hai lần.
- UI không gửi giá để Backend tin dùng và không tự tính số tiền cần thu.
