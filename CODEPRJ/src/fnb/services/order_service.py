"""Nghiệp vụ tạo, bổ sung và hủy đơn hàng."""

from uuid import uuid4

from fnb.exceptions import InvalidStateError, NotFoundError, ValidationError
from fnb.models import ItemStatus, MenuItem, Order, OrderItem, OrderStatus, now_iso
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
        """Tạo đơn OPEN, lưu trước rồi đưa từng dòng món vào cuối Queue."""
        validated = self._validate_lines(lines)
        next_seq = self._next_queue_seq()
        items = self._build_order_items(validated, next_seq)
        order = Order(id=f"ORD-{uuid4().hex[:10].upper()}", items=items)
        self._order_repository.upsert(order)
        self._kitchen_service.enqueue_items(order.id, items)
        return order

    def add_items(self, order_id: str, lines: list[dict]) -> Order:
        """Thêm dòng món mới vào đơn OPEN và cuối Queue, không sửa giá dòng cũ."""
        order = self.get_order(order_id)
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Chỉ có thể thêm món vào đơn OPEN.")

        validated = self._validate_lines(lines)
        new_items = self._build_order_items(validated, self._next_queue_seq())
        order.items.extend(new_items)
        self._order_repository.upsert(order)
        self._kitchen_service.enqueue_items(order.id, new_items)
        return order

    def get_order(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}.")
        return order

    def list_orders(self) -> list[Order]:
        return self._order_repository.list_all()

    def cancel_order(self, order_id: str, reason: str = "") -> Order:
        order = self.get_order(order_id)
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Chỉ đơn OPEN mới có thể hủy.")
        if not order.items or any(item.status != ItemStatus.QUEUED for item in order.items):
            raise InvalidStateError("Chỉ được hủy khi tất cả món vẫn đang QUEUED.")

        for item in order.items:
            item.status = ItemStatus.CANCELLED
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = now_iso()
        order.cancel_reason = str(reason).strip()
        self._order_repository.upsert(order)
        self._kitchen_service.remove_order_from_queue(order.id)
        return order

    def _validate_lines(self, lines: list[dict]) -> list[tuple[MenuItem, int, str]]:
        if not isinstance(lines, list) or not lines:
            raise ValidationError("Đơn hàng phải có ít nhất một dòng món.")

        validated: list[tuple[MenuItem, int, str]] = []
        for index, line in enumerate(lines, start=1):
            if not isinstance(line, dict):
                raise ValidationError(f"Dòng món số {index} phải là object.")

            menu_item_id = str(line.get("menu_item_id", "")).strip()
            if not menu_item_id:
                raise ValidationError(f"Dòng món số {index} thiếu menu_item_id.")

            quantity = line.get("quantity")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                raise ValidationError(
                    f"Số lượng ở dòng {index} phải là số nguyên dương."
                )

            menu_item = self._menu_service.get_item(menu_item_id)
            if not menu_item.is_available:
                raise ValidationError(f"Món {menu_item.name} hiện không được bán.")
            validated.append((menu_item, quantity, str(line.get("note", "")).strip()))

        return validated

    @staticmethod
    def _build_order_items(
        validated: list[tuple[MenuItem, int, str]], start_seq: int
    ) -> list[OrderItem]:
        return [
            OrderItem(
                id=f"OI-{uuid4().hex[:10].upper()}",
                menu_item_id=menu_item.id,
                name=menu_item.name,
                unit_price=menu_item.price,
                quantity=quantity,
                note=note,
                status=ItemStatus.QUEUED,
                queue_seq=start_seq + offset,
            )
            for offset, (menu_item, quantity, note) in enumerate(validated)
        ]

    def _next_queue_seq(self) -> int:
        all_sequences = [
            item.queue_seq
            for order in self._order_repository.list_all()
            for item in order.items
        ]
        return max(all_sequences, default=0) + 1
