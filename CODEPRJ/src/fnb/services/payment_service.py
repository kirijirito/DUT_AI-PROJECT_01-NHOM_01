"""Nghiệp vụ xem hóa đơn và xác nhận thanh toán."""

from fnb.exceptions import InvalidStateError, NotFoundError
from fnb.models import ItemStatus, Order, OrderStatus, now_iso
from fnb.repositories.order_repository import OrderRepository


class PaymentService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    def list_unpaid_orders(self) -> list[Order]:
        return [
            order
            for order in self._order_repository.list_all()
            if order.status == OrderStatus.OPEN
        ]

    def preview_bill(self, order_id: str) -> dict:
        """Tạo hóa đơn cho một Order; món trùng mã được gộp trong cùng hóa đơn."""
        order = self._get_order(order_id)
        grouped: dict[tuple[str, int], dict] = {}

        for item in order.items:
            key = (item.menu_item_id, item.unit_price)
            if key not in grouped:
                grouped[key] = {
                    "menu_item_id": item.menu_item_id,
                    "name": item.name,
                    "unit_price": item.unit_price,
                    "quantity": 0,
                    "notes": [],
                    "status": ItemStatus.SERVED.value,
                }

            line = grouped[key]
            line["quantity"] += item.quantity
            if item.note and item.note not in line["notes"]:
                line["notes"].append(item.note)
            if item.status != ItemStatus.SERVED:
                line["status"] = ItemStatus.QUEUED.value

        items = []
        for line in grouped.values():
            notes = "; ".join(line.pop("notes"))
            line["note"] = notes
            line["line_total"] = line["unit_price"] * line["quantity"]
            items.append(line)

        subtotal = order.subtotal
        total_due = order.total_paid if order.status == OrderStatus.PAID else subtotal
        return {
            "order_id": order.id,
            "status": order.status.value,
            "created_at": order.created_at,
            "paid_at": order.paid_at,
            "items": items,
            "total_before_discount": subtotal,
            "total_due": total_due,
            "can_pay": (
                order.status == OrderStatus.OPEN
                and bool(order.items)
                and all(item.status == ItemStatus.SERVED for item in order.items)
            ),
        }

    def checkout(self, order_id: str) -> Order:
        order = self._get_order(order_id)
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Đơn này đã thanh toán hoặc không còn mở.")
        if not order.items or any(item.status != ItemStatus.SERVED for item in order.items):
            raise InvalidStateError(
                "Chưa thể thanh toán: tất cả món trong đơn phải ở trạng thái SERVED."
            )

        order.status = OrderStatus.PAID
        order.paid_at = now_iso()
        order.total_paid = order.subtotal
        self._order_repository.upsert(order)
        return order

    def _get_order(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(str(order_id).strip())
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}.")
        return order
