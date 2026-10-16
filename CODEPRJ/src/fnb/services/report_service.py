"""Báo cáo doanh thu theo ngày thanh toán."""

from datetime import date

from fnb.exceptions import ValidationError
from fnb.models import OrderStatus
from fnb.repositories.order_repository import OrderRepository


class ReportService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    def daily_summary(self, day: str | None = None) -> dict:
        day_text = day or date.today().isoformat()
        try:
            parsed_day = date.fromisoformat(day_text)
            if parsed_day.isoformat() != day_text:
                raise ValueError("Ngày không theo định dạng YYYY-MM-DD.")
        except (TypeError, ValueError) as exc:
            raise ValidationError("Ngày phải có định dạng YYYY-MM-DD.") from exc

        paid_orders = [
            order
            for order in self._order_repository.list_all()
            if order.status == OrderStatus.PAID
            and order.paid_at is not None
            and order.paid_at[:10] == day_text
        ]
        return {
            "date": day_text,
            "paid_order_count": len(paid_orders),
            "revenue_vnd": sum(order.total_paid or 0 for order in paid_orders),
            "order_ids": [order.id for order in paid_orders],
        }
