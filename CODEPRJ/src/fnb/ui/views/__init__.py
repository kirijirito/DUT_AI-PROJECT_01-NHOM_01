"""Các View giao diện người dùng thuần Gradio theo mô hình MVC/MVP."""

from fnb.ui.views.invoice_view import InvoiceViewComponents, build_invoice_view
from fnb.ui.views.order_view import OrderViewComponents, build_order_view
from fnb.ui.views.payment_view import PaymentViewComponents, build_payment_view
from fnb.ui.views.table_view import TableViewComponents, build_table_view

__all__ = [
    "InvoiceViewComponents",
    "OrderViewComponents",
    "PaymentViewComponents",
    "TableViewComponents",
    "build_invoice_view",
    "build_order_view",
    "build_payment_view",
    "build_table_view",
]
