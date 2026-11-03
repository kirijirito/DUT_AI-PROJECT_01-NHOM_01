"""Nghiệp vụ tạo và tra cứu đơn hàng."""

from collections import OrderedDict
from uuid import uuid4

from fnb.exceptions import NotFoundError, ValidationError
from fnb.models import ItemStatus, MenuItem, Order, OrderItem
from fnb.repositories.order_repository import OrderRepository
from fnb.services.kitchen_service import KitchenService
from fnb.services.menu_service import MenuService


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        menu_service: MenuService,
        kitchen_service: KitchenService,
    ) -> None:
        self._order_repository = order_repository
        self._menu_service = menu_service
        self._kitchen_service = kitchen_service

    def create_order(self, lines: list[dict]) -> Order:
        """Tạo một đơn cho một lượt đặt; món trùng mã/ghi chú được gộp số lượng."""
        validated = self._validate_and_group_lines(lines)
        next_sequence = self._next_queue_sequence()
        order_items = [
            OrderItem(
                id=f"OI-{uuid4().hex[:10].upper()}",
                menu_item_id=menu_item.id,
                name=menu_item.name,
                unit_price=menu_item.price,
                quantity=quantity,
                note=note,
                status=ItemStatus.QUEUED,
                queue_seq=next_sequence + offset,
            )
            for offset, (menu_item, quantity, note) in enumerate(validated)
        ]

        order = Order(id=f"ORD-{uuid4().hex[:10].upper()}", items=order_items)

        # Lưu đơn/queue_seq vào JSON trước. Nếu ứng dụng dừng đột ngột,
        # KitchenService sẽ dựng lại Queue từ các dòng QUEUED khi khởi động.
        self._order_repository.upsert(order)
        self._kitchen_service.enqueue_items(order.id, order.items)
        return order

    def get_order(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(str(order_id).strip())
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}.")
        return order

    def list_orders(self) -> list[Order]:
        return self._order_repository.list_all()

    def _validate_and_group_lines(
        self, lines: list[dict]
    ) -> list[tuple[MenuItem, int, str]]:
        if not isinstance(lines, list) or not lines:
            raise ValidationError("Giỏ hàng phải có ít nhất một món.")

        grouped: OrderedDict[tuple[str, str], tuple[MenuItem, int, str]] = OrderedDict()
        for index, line in enumerate(lines, start=1):
            if not isinstance(line, dict):
                raise ValidationError(f"Dòng món số {index} không hợp lệ.")

            menu_item_id = str(line.get("menu_item_id", "")).strip()
            if not menu_item_id:
                raise ValidationError(f"Dòng món số {index} thiếu mã món.")

            quantity = line.get("quantity")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                raise ValidationError(f"Số lượng dòng {index} phải là số nguyên dương.")

            note = str(line.get("note", "")).strip()
            menu_item = self._menu_service.get_item(menu_item_id)
            if not menu_item.is_available:
                raise ValidationError(f"Món {menu_item.name} hiện không còn bán.")

            key = (menu_item.id, note)
            if key in grouped:
                old_item, old_quantity, old_note = grouped[key]
                grouped[key] = (old_item, old_quantity + quantity, old_note)
            else:
                grouped[key] = (menu_item, quantity, note)

        return list(grouped.values())

    def _next_queue_sequence(self) -> int:
        sequences = [
            item.queue_seq
            for order in self._order_repository.list_all()
            for item in order.items
        ]
        return max(sequences, default=0) + 1
