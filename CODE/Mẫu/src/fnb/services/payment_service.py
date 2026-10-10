"""Nghiệp vụ thanh toán mô phỏng; không kết nối cổng thanh toán thật."""

from fnb.exceptions import InvalidStateError, NotFoundError
from fnb.models import ItemStatus, Order, OrderStatus, now_iso
from fnb.repositories.order_repository import OrderRepository
from fnb.services.table_service import TableService


class PaymentService:
    def __init__(self, order_repository: OrderRepository, table_service: TableService) -> None:
        self._order_repository = order_repository
        self._table_service = table_service

    def checkout(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}.")
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Đơn này không còn ở trạng thái OPEN; không thể checkout lại.")
        allowed_statuses = {ItemStatus.READY, ItemStatus.SERVED}
        if any(item.status not in allowed_statuses for item in order.items):
            raise InvalidStateError("Chưa thể thanh toán: vẫn còn món chưa READY hoặc SERVED.")

        order.total_paid = sum(item.line_total for item in order.items)
        order.paid_at = now_iso()
        order.status = OrderStatus.PAID
        self._order_repository.upsert(order)
        self._table_service.release(order.table_id, order.id)
        return order
