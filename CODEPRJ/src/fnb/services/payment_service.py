"""Nghiệp vụ xem hóa đơn và thanh toán mô phỏng."""

from fnb.exceptions import InvalidStateError, NotFoundError, ValidationError
from fnb.models import ItemStatus, Order, OrderStatus, now_iso
from fnb.repositories.order_repository import OrderRepository


class PaymentService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    def preview_bill(self, order_id: str, discount_amount: int | None = None) -> dict:
        """Tính hóa đơn xem trước hoặc trả lại đúng biên nhận đã thanh toán."""
        order = self._get_order(order_id)
        if order.status == OrderStatus.CANCELLED:
            raise InvalidStateError(
                "Không thể xem hóa đơn thanh toán của đơn đã hủy."
            )

        if order.status == OrderStatus.PAID:
            subtotal = order.total_before_discount
            if subtotal is None:
                subtotal = order.subtotal
            discount = order.discount_amount
            total_due = order.total_paid if order.total_paid is not None else subtotal - discount
        else:
            subtotal = order.subtotal
            discount = 0 if discount_amount is None else discount_amount
            self._validate_discount(discount, subtotal)
            total_due = subtotal - discount

        return {
            "order_id": order.id,
            "status": order.status.value,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                    "line_total": item.line_total,
                    "status": item.status.value,
                }
                for item in order.items
                if item.status != ItemStatus.CANCELLED
            ],
            "total_before_discount": subtotal,
            "discount_amount": discount,
            "total_due": total_due,
            "payment_method": order.payment_method,
            "paid_at": order.paid_at,
        }

    def checkout(
        self,
        order_id: str,
        payment_method: str = "CASH",
        discount_amount: int = 0,
    ) -> Order:
        order = self._get_order(order_id)
        if order.status != OrderStatus.OPEN:
            raise InvalidStateError("Đơn không còn OPEN; không thể thanh toán lần nữa.")

        allowed_statuses = {ItemStatus.READY, ItemStatus.SERVED}
        if not order.items or any(item.status not in allowed_statuses for item in order.items):
            raise InvalidStateError(
                "Chưa thể thanh toán: tất cả món phải READY hoặc SERVED."
            )

        method = str(payment_method).strip().upper()
        if not method:
            raise ValidationError("Phải chọn phương thức thanh toán.")
        self._validate_discount(discount_amount, order.subtotal)

        order.total_before_discount = order.subtotal
        order.discount_amount = discount_amount
        order.total_paid = order.subtotal - discount_amount
        order.payment_method = method
        order.paid_at = now_iso()
        order.status = OrderStatus.PAID
        self._order_repository.upsert(order)
        return order

    def _get_order(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}.")
        return order

    @staticmethod
    def _validate_discount(discount_amount: int, subtotal: int) -> None:
        if (
            isinstance(discount_amount, bool)
            or not isinstance(discount_amount, int)
            or discount_amount < 0
        ):
            raise ValidationError("Giảm giá phải là số nguyên VND không âm.")
        if discount_amount > subtotal:
            raise ValidationError(
                "Giảm giá không được vượt tổng tiền trước giảm giá."
            )
