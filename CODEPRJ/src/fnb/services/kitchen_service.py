"""Quản lý Quy trình Bếp & Phục vụ bằng 3 Hàng đợi (Queues) FIFO:

1. waiting_queue: Queue Đang Đợi (món mới đặt, chờ bếp nhận)
2. cooking_queue: Queue Đang Nấu (bếp đang chế biến)
3. serving_queue: Queue Đang Chờ Phục Vụ (nấu xong, chờ bưng ra cho khách)
"""

from fnb.exceptions import InvalidStateError, NotFoundError
from fnb.models import ItemStatus, Order, OrderItem, OrderStatus
from fnb.repositories.order_repository import OrderRepository
from fnb.simple_queue import SimpleQueue


class KitchenService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

        # 3 Hàng đợi FIFO theo đúng quy trình nhà hàng
        self.waiting_queue = SimpleQueue("Queue Đang Đợi")
        self.cooking_queue = SimpleQueue("Queue Đang Nấu")
        self.serving_queue = SimpleQueue("Queue Chờ Phục Vụ")

        self._rebuild_queues()

    def _rebuild_queues(self) -> None:
        """Khôi phục lại 3 hàng đợi từ các đơn hàng OPEN trong cơ sở dữ liệu."""
        pending_waiting: list[tuple[int, str, str]] = []
        pending_cooking: list[tuple[int, str, str]] = []
        pending_serving: list[tuple[int, str, str]] = []

        for order in self._order_repository.list_all():
            if order.status != OrderStatus.OPEN:
                continue
            for item in order.items:
                if item.status == ItemStatus.QUEUED:
                    pending_waiting.append((item.queue_seq, order.id, item.id))
                elif item.status == ItemStatus.PREPARING:
                    pending_cooking.append((item.queue_seq, order.id, item.id))
                elif item.status == ItemStatus.READY:
                    pending_serving.append((item.queue_seq, order.id, item.id))

        # Sắp xếp theo thứ tự đặt món (queue_seq) và nạp vào 3 hàng đợi
        pending_waiting.sort(key=lambda entry: entry[0])
        for entry in pending_waiting:
            self.waiting_queue.enqueue(entry)

        pending_cooking.sort(key=lambda entry: entry[0])
        for entry in pending_cooking:
            self.cooking_queue.enqueue(entry)

        pending_serving.sort(key=lambda entry: entry[0])
        for entry in pending_serving:
            self.serving_queue.enqueue(entry)

    def enqueue_items(self, order_id: str, items: list[OrderItem]) -> None:
        """Thêm các món mới tạo (QUEUED) vào Queue Đang Đợi."""
        for item in sorted(items, key=lambda row: row.queue_seq):
            if item.status == ItemStatus.QUEUED:
                self.waiting_queue.enqueue((item.queue_seq, order_id, item.id))

    # =========================================================================
    # LẤY THÔNG TIN 3 HÀNG ĐỢI ĐỂ HIỂN THỊ
    # =========================================================================
    def get_waiting_queue(self) -> list[dict]:
        """Lấy danh sách các món trong Queue 1: Đang Đợi."""
        return self._format_queue_list(self.waiting_queue)

    def get_cooking_queue(self) -> list[dict]:
        """Lấy danh sách các món trong Queue 2: Đang Nấu."""
        return self._format_queue_list(self.cooking_queue)

    def get_serving_queue(self) -> list[dict]:
        """Lấy danh sách các món trong Queue 3: Đang Chờ Phục Vụ."""
        return self._format_queue_list(self.serving_queue)

    def get_queue(self) -> list[dict]:
        """Tương thích ngược: trả về danh sách Queue Đang Đợi."""
        return self.get_waiting_queue()

    # =========================================================================
    # CHUYỂN TIẾP TRẠNG THÁI GIỮA 3 HÀNG ĐỢI (FIFO & THEO MÃ)
    # =========================================================================
    def start_next_item(self) -> dict:
        """Lấy món đầu tiên từ Queue Đang Đợi -> Chuyển sang Queue Đang Nấu (FIFO)."""
        while not self.waiting_queue.is_empty():
            queue_seq, order_id, item_id = self.waiting_queue.dequeue()
            found = self._find_item(order_id, item_id)
            if found is None:
                continue
            order, item = found
            if order.status != OrderStatus.OPEN or item.status != ItemStatus.QUEUED:
                continue

            # Đổi trạng thái sang PREPARING (Đang nấu)
            item.status = ItemStatus.PREPARING
            self._order_repository.upsert(order)

            # Đưa vào Queue Đang Nấu
            self.cooking_queue.enqueue((queue_seq, order_id, item_id))
            return self._task_dict(queue_seq, order, item)

        raise InvalidStateError("Queue Đang Đợi đang rỗng, không có món để bắt đầu nấu.")

    def finish_next_item(self) -> dict:
        """Lấy món đầu tiên từ Queue Đang Nấu -> Chuyển sang Queue Chờ Phục Vụ (FIFO)."""
        while not self.cooking_queue.is_empty():
            queue_seq, order_id, item_id = self.cooking_queue.dequeue()
            found = self._find_item(order_id, item_id)
            if found is None:
                continue
            order, item = found
            if order.status != OrderStatus.OPEN or item.status != ItemStatus.PREPARING:
                continue

            # Đổi trạng thái sang READY (Đã nấu xong - Chờ phục vụ)
            item.status = ItemStatus.READY
            self._order_repository.upsert(order)

            # Đưa vào Queue Chờ Phục Vụ
            self.serving_queue.enqueue((queue_seq, order_id, item_id))
            return self._task_dict(queue_seq, order, item)

        raise InvalidStateError("Queue Đang Nấu đang rỗng, không có món nào đang nấu.")

    def serve_next_item(self) -> dict:
        """Lấy món đầu tiên từ Queue Chờ Phục Vụ -> Chuyển sang ĐÃ PHỤC VỤ (FIFO)."""
        while not self.serving_queue.is_empty():
            queue_seq, order_id, item_id = self.serving_queue.dequeue()
            found = self._find_item(order_id, item_id)
            if found is None:
                continue
            order, item = found
            if order.status != OrderStatus.OPEN or item.status != ItemStatus.READY:
                continue

            # Đổi trạng thái sang SERVED (Đã phục vụ)
            item.status = ItemStatus.SERVED
            self._order_repository.upsert(order)
            return self._task_dict(queue_seq, order, item)

        raise InvalidStateError("Queue Chờ Phục Vụ đang rỗng, không có món nào chờ phục vụ.")

    def mark_item_ready(self, order_id: str, item_id: str) -> OrderItem:
        """Đánh dấu món theo mã cụ thể: từ Đang Nấu -> Chờ Phục Vụ."""
        order, item = self._require_item(order_id, item_id)
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Không thể sửa món của đơn đã đóng.")
        if item.status != ItemStatus.PREPARING:
            raise InvalidStateError("Chỉ món đang nấu (PREPARING) mới có thể chuyển sang READY.")

        item.status = ItemStatus.READY
        self._order_repository.upsert(order)

        # Xóa khỏi cooking_queue và thêm vào serving_queue
        self.cooking_queue.remove_if(lambda entry: entry[1] == order_id and entry[2] == item_id)
        self.serving_queue.enqueue((item.queue_seq, order_id, item.id))
        return item

    def mark_item_served(self, order_id: str, item_id: str) -> OrderItem:
        """Đánh dấu món theo mã cụ thể: từ Chờ Phục Vụ -> Đã Phục Vụ."""
        order, item = self._require_item(order_id, item_id)
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Không thể sửa món của đơn đã đóng.")
        if item.status != ItemStatus.READY:
            raise InvalidStateError("Chỉ món đã sẵn sàng (READY) mới có thể chuyển sang SERVED.")

        item.status = ItemStatus.SERVED
        self._order_repository.upsert(order)

        # Xóa khỏi serving_queue
        self.serving_queue.remove_if(lambda entry: entry[1] == order_id and entry[2] == item_id)
        return item

    def remove_order_from_queue(self, order_id: str) -> None:
        """Xóa toàn bộ món của một đơn hàng khỏi cả 3 hàng đợi (dùng khi hủy đơn)."""
        self.waiting_queue.remove_if(lambda entry: entry[1] == order_id)
        self.cooking_queue.remove_if(lambda entry: entry[1] == order_id)
        self.serving_queue.remove_if(lambda entry: entry[1] == order_id)

    # =========================================================================
    # HÀM BỔ TRỢ TÌM KIẾM VÀ ĐỊNH DẠNG
    # =========================================================================
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

    def _format_queue_list(self, queue: SimpleQueue) -> list[dict]:
        result: list[dict] = []
        for queue_seq, order_id, item_id in queue.to_list():
            found = self._find_item(order_id, item_id)
            if found is None:
                continue
            order, item = found
            if order.status == OrderStatus.OPEN:
                result.append(self._task_dict(queue_seq, order, item))
        return result

    @staticmethod
    def _task_dict(queue_seq: int, order: Order, item: OrderItem) -> dict:
        return {
            "queue_seq": queue_seq,
            "order_id": order.id,
            "order_item_id": item.id,
            "menu_item_id": item.menu_item_id,
            "name": item.name,
            "quantity": item.quantity,
            "note": item.note,
            "status": item.status.value,
        }
