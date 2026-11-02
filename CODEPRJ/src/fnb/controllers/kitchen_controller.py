from fnb.services.kitchen_service import KitchenService


class KitchenController:
    """Controller điều phối giữa UI và KitchenService (quản lý 3 Queues)."""

    def __init__(self, kitchen_service: KitchenService) -> None:
        self._kitchen_service = kitchen_service

    def get_queue(self) -> list[dict]:
        """Tương thích ngược: lấy Queue Đang Đợi."""
        return self._kitchen_service.get_queue()

    def get_waiting_queue(self) -> list[dict]:
        """Lấy danh sách Queue 1: Đang Đợi."""
        return self._kitchen_service.get_waiting_queue()

    def get_cooking_queue(self) -> list[dict]:
        """Lấy danh sách Queue 2: Đang Nấu."""
        return self._kitchen_service.get_cooking_queue()

    def get_serving_queue(self) -> list[dict]:
        """Lấy danh sách Queue 3: Đang Chờ Phục Vụ."""
        return self._kitchen_service.get_serving_queue()

    def start_next_item(self) -> dict:
        """Bắt đầu nấu món tiếp theo (FIFO): Chờ -> Đang Nấu."""
        return self._kitchen_service.start_next_item()

    def finish_next_item(self) -> dict:
        """Nấu xong món tiếp theo (FIFO): Đang Nấu -> Chờ Phục Vụ."""
        return self._kitchen_service.finish_next_item()

    def serve_next_item(self) -> dict:
        """Phục vụ món tiếp theo (FIFO): Chờ Phục Vụ -> Đã Phục Vụ."""
        return self._kitchen_service.serve_next_item()

    def mark_item_ready(self, order_id: str, item_id: str) -> dict:
        """Đánh dấu món theo mã cụ thể: Đang Nấu -> Chờ Phục Vụ."""
        return self._kitchen_service.mark_item_ready(order_id, item_id).to_dict()

    def mark_item_served(self, order_id: str, item_id: str) -> dict:
        """Đánh dấu món theo mã cụ thể: Chờ Phục Vụ -> Đã Phục Vụ."""
        return self._kitchen_service.mark_item_served(order_id, item_id).to_dict()
