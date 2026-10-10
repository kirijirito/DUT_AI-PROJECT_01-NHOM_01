"""Nghiệp vụ tạo và hủy đơn hàng."""

from uuid import uuid4

from fnb.exceptions import InvalidStateError, NotFoundError, ValidationError
from fnb.models import ItemStatus, MenuItem, Order, OrderItem, OrderStatus
from fnb.repositories.order_repository import OrderRepository
from fnb.services.kitchen_service import KitchenService
from fnb.services.menu_service import MenuService
from fnb.services.table_service import TableService


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        menu_service: MenuService,
        table_service: TableService,
        kitchen_service: KitchenService,
    ) -> None:
        self._order_repository = order_repository
        self._menu_service = menu_service
        self._table_service = table_service
        self._kitchen_service = kitchen_service

    def create_order(self, table_id: str, lines: list[dict]) -> Order:
        if not isinstance(lines, list) or not lines:
            raise ValidationError("Đơn hàng phải có ít nhất một dòng món.")
        self._table_service.ensure_available(table_id)

        # Kiểm tra toàn bộ input trước khi ghi file để giảm lỗi dữ liệu dở dang.
        validated: list[tuple[MenuItem, int, str]] = []
        for index, line in enumerate(lines, start=1):
            if not isinstance(line, dict):
                raise ValidationError(f"Dòng món số {index} phải là object.")
            menu_item_id = str(line.get("menu_item_id", "")).strip()
            if not menu_item_id:
                raise ValidationError(f"Dòng món số {index} thiếu menu_item_id.")
            quantity = line.get("quantity")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                raise ValidationError(f"Số lượng ở dòng {index} phải là số nguyên dương.")
            menu_item = self._menu_service.get_item(menu_item_id)
            if not menu_item.is_available:
                raise ValidationError(f"Món {menu_item.name} hiện không được bán.")
            note = str(line.get("note", "")).strip()
            validated.append((menu_item, quantity, note))

        next_seq = self._next_queue_seq()
        order_items: list[OrderItem] = []
        for offset, (menu_item, quantity, note) in enumerate(validated):
            order_items.append(
                OrderItem(
                    id=f"OI-{uuid4().hex[:10].upper()}",
                    menu_item_id=menu_item.id,
                    name=menu_item.name,
                    unit_price=menu_item.price,
                    quantity=quantity,
                    note=note,
                    status=ItemStatus.QUEUED,
                    queue_seq=next_seq + offset,
                )
            )

        order = Order(
            id=f"ORD-{uuid4().hex[:10].upper()}",
            table_id=table_id,
            items=order_items,
        )
        self._order_repository.upsert(order)
        self._table_service.occupy(table_id, order.id)
        self._kitchen_service.enqueue_order(order)
        return order

    def get_order(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}.")
        return order

    def list_orders(self) -> list[Order]:
        return self._order_repository.list_all()

    def cancel_order(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Chỉ đơn OPEN mới có thể hủy.")
        if any(item.status != ItemStatus.QUEUED for item in order.items):
            raise InvalidStateError("Chỉ được hủy khi tất cả món vẫn đang QUEUED.")
        for item in order.items:
            item.status = ItemStatus.CANCELLED
        order.status = OrderStatus.CANCELLED
        self._order_repository.upsert(order)
        self._kitchen_service.remove_order_from_queue(order.id)
        self._table_service.release(order.table_id, order.id)
        return order

    def _next_queue_seq(self) -> int:
        all_sequences = [
            item.queue_seq
            for order in self._order_repository.list_all()
            for item in order.items
        ]
        return max(all_sequences, default=0) + 1
