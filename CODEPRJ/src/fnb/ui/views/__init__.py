"""Các View Gradio của ba chức năng chính."""

from fnb.ui.views.kitchen_view import KitchenViewComponents, build_kitchen_view
from fnb.ui.views.order_view import OrderViewComponents, build_order_view
from fnb.ui.views.payment_view import PaymentViewComponents, build_payment_view

__all__ = [
    "KitchenViewComponents",
    "OrderViewComponents",
    "PaymentViewComponents",
    "build_kitchen_view",
    "build_order_view",
    "build_payment_view",
]
