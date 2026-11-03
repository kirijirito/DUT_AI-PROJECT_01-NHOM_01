"""Nghiệp vụ hàng đợi bếp dùng Queue Linked List tự cài đặt."""

from fnb.exceptions import InvalidStateError, NotFoundError
from fnb.models import ItemStatus, Order, OrderItem, OrderStatus
from fnb.queue import Queue
from fnb.repositories.order_repository import OrderRepository


QueueEntry = tuple[int, str, str]


class KitchenService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository
        self._queue: Queue[QueueEntry] = Queue()
        self._restore_queue()

    @property
    def queue(self) -> Queue[QueueEntry]:
        """Cho phép kiểm tra Queue OOP khi demo/test; UI không tự sửa Queue."""
        return self._queue

    def _restore_queue(self) -> None:
        """Dựng lại Linked List từ orders.json theo queue_seq tăng dần."""
        pending: list[QueueEntry] = []
        for order in self._order_repository.list_all():
            if order.status != OrderStatus.OPEN:
                continue
            for item in order.items:
                if item.status == ItemStatus.QUEUED:
                    pending.append((item.queue_seq, order.id, item.id))

        for entry in sorted(pending, key=lambda value: value[0]):
            self._queue.enqueue(entry)

    def enqueue_items(self, order_id: str, items: list[OrderItem]) -> None:
        """Đưa từng dòng món QUEUED vào cuối Queue sau khi đã lưu JSON."""
        for item in sorted(items, key=lambda value: value.queue_seq):
            if item.status == ItemStatus.QUEUED:
                self._queue.enqueue((item.queue_seq, order_id, item.id))

    def get_queue(self) -> list[dict]:
        result = []
        for queue_seq, order_id, item_id in self._queue:
            found = self._find_item(order_id, item_id)
            if found is None:
                continue
            order, item = found
            if order.status == OrderStatus.OPEN and item.status == ItemStatus.QUEUED:
                result.append(self._task_dict(queue_seq, order, item))
        return result

    def get_served_items(self) -> list[dict]:
        """Lấy danh sách món đã phục vụ để UI hiển thị riêng."""
        served: list[tuple[int, dict]] = []
        for order in self._order_repository.list_all():
            for item in order.items:
                if item.status == ItemStatus.SERVED:
                    served.append((item.queue_seq, self._task_dict(item.queue_seq, order, item)))
        served.sort(key=lambda pair: pair[0])
        return [row for _, row in served]

    def serve_next_item(self) -> dict:
        """Đánh dấu món đầu Queue đã SERVED, sau đó mới dequeue Node."""
        while not self._queue.is_empty():
            entry = self._queue.peek()
            assert entry is not None
            queue_seq, order_id, item_id = entry
            found = self._find_item(order_id, item_id)

            if found is None:
                # Node không còn bản ghi tương ứng: bỏ Node lỗi để Queue tiếp tục.
                self._queue.dequeue()
                continue

            order, item = found
            if order.status != OrderStatus.OPEN or item.status != ItemStatus.QUEUED:
                self._queue.dequeue()
                continue

            item.status = ItemStatus.SERVED
            # Phải ghi thành công xuống JSON trước khi tháo Node khỏi Queue.
            self._order_repository.upsert(order)
            self._queue.dequeue()
            return self._task_dict(queue_seq, order, item)

        raise InvalidStateError("Queue đang rỗng, không còn món chờ phục vụ.")

    def _find_item(self, order_id: str, item_id: str) -> tuple[Order, OrderItem] | None:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            return None
        for item in order.items:
            if item.id == item_id:
                return order, item
        return None

    @staticmethod
    def _task_dict(queue_seq: int, order: Order, item: OrderItem) -> dict:
        return {
            "queue_seq": queue_seq,
            "order_id": order.id,
            "order_item_id": item.id,
            "menu_item_id": item.menu_item_id,
            "name": item.name,
            "unit_price": item.unit_price,
            "quantity": item.quantity,
            "note": item.note,
            "status": item.status.value,
        }
