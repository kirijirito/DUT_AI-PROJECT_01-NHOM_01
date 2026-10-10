"""Quản lý Queue FIFO cho các dòng món đang chờ chế biến."""

from collections import deque

from fnb.exceptions import InvalidStateError, NotFoundError
from fnb.models import ItemStatus, Order, OrderItem, OrderStatus
from fnb.repositories.order_repository import OrderRepository


class KitchenService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository
        self._queue: deque[tuple[int, str, str]] = deque()
        self._rebuild_queue()

    def _rebuild_queue(self) -> None:
        """Khôi phục Queue từ các dòng QUEUED trong JSON, theo thứ tự queue_seq."""
        pending: list[tuple[int, str, str]] = []
        for order in self._order_repository.list_all():
            if order.status != OrderStatus.OPEN:
                continue
            for item in order.items:
                if item.status == ItemStatus.QUEUED:
                    pending.append((item.queue_seq, order.id, item.id))
        pending.sort(key=lambda entry: entry[0])
        self._queue = deque(pending)

    def enqueue_order(self, order: Order) -> None:
        """Đưa các dòng món của một đơn mới vào cuối Queue."""
        for item in sorted(order.items, key=lambda row: row.queue_seq):
            if item.status == ItemStatus.QUEUED:
                self._queue.append((item.queue_seq, order.id, item.id))

    def get_queue(self) -> list[dict]:
        """Trả Queue dưới dạng dict dễ hiển thị; không làm thay đổi hàng đợi."""
        result: list[dict] = []
        for queue_seq, order_id, item_id in self._queue:
            found = self._find_item(order_id, item_id)
            if found is None:
                continue
            order, item = found
            result.append(self._task_dict(queue_seq, order, item))
        return result

    def start_next_item(self) -> dict:
        """Lấy món đầu Queue, chuyển QUEUED sang PREPARING và lưu lại JSON."""
        while self._queue:
            queue_seq, order_id, item_id = self._queue.popleft()
            found = self._find_item(order_id, item_id)
            if found is None:
                continue
            order, item = found
            if order.status != OrderStatus.OPEN or item.status != ItemStatus.QUEUED:
                continue
            item.status = ItemStatus.PREPARING
            self._order_repository.upsert(order)
            return self._task_dict(queue_seq, order, item)
        raise InvalidStateError("Queue bếp đang rỗng, không có món để bắt đầu.")

    def mark_item_ready(self, order_id: str, item_id: str) -> OrderItem:
        order, item = self._require_item(order_id, item_id)
        if item.status != ItemStatus.PREPARING:
            raise InvalidStateError("Chỉ món đang PREPARING mới được chuyển sang READY.")
        item.status = ItemStatus.READY
        self._order_repository.upsert(order)
        return item

    def mark_item_served(self, order_id: str, item_id: str) -> OrderItem:
        order, item = self._require_item(order_id, item_id)
        if item.status != ItemStatus.READY:
            raise InvalidStateError("Chỉ món READY mới được chuyển sang SERVED.")
        item.status = ItemStatus.SERVED
        self._order_repository.upsert(order)
        return item

    def remove_order_from_queue(self, order_id: str) -> None:
        """Loại bỏ các task của đơn bị hủy khỏi Queue trong bộ nhớ."""
        self._queue = deque(entry for entry in self._queue if entry[1] != order_id)

    def _find_item(self, order_id: str, item_id: str) -> tuple[Order, OrderItem] | None:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            return None
        for item in order.items:
            if item.id == item_id:
                return order, item
        return None

    def _require_item(self, order_id: str, item_id: str) -> tuple[Order, OrderItem]:
        found = self._find_item(order_id, item_id)
        if found is None:
            raise NotFoundError(f"Không tìm thấy món {item_id} trong đơn {order_id}.")
        return found

    @staticmethod
    def _task_dict(queue_seq: int, order: Order, item: OrderItem) -> dict:
        return {
            "queue_seq": queue_seq,
            "order_id": order.id,
            "table_id": order.table_id,
            "order_item_id": item.id,
            "menu_item_id": item.menu_item_id,
            "name": item.name,
            "quantity": item.quantity,
            "note": item.note,
            "status": item.status.value,
        }
