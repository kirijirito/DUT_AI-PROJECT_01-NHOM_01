"""Kiểm thử tầng UI View và Presenter (MVC/MVP) cho hệ thống F&B."""

from datetime import date

import gradio as gr

from fnb.ui.app import create_app
from fnb.ui.presenter import FnbPresenter, format_vnd
from fnb.ui.views import (
    build_invoice_view,
    build_order_view,
    build_payment_view,
    build_table_view,
)


def test_create_app_initializes_blocks(context):
    app = create_app(context)
    assert isinstance(app, gr.Blocks)
    assert app.title == "F&B Order Management System"


def test_format_vnd():
    assert format_vnd(45000) == "45.000 ₫"
    assert format_vnd(0) == "0 ₫"
    assert format_vnd(None) == "0 ₫"
    assert format_vnd("abc") == "0 ₫"


def test_views_initialization(context):
    presenter = FnbPresenter(context)
    with gr.Blocks():
        order_view = build_order_view(presenter)
        assert order_view.cart_table is not None

        table_view = build_table_view(presenter)
        assert len(table_view.table_buttons) == 12

        payment_view = build_payment_view(presenter)
        assert payment_view.bill_items_table is not None

        invoice_view = build_invoice_view(presenter)
        assert invoice_view.invoices_table is not None


def test_cart_operations(context):
    presenter = FnbPresenter(context)
    cart, rows, summary, msg = presenter.add_item_to_cart("MI-001", 2, "ít sốt", None)
    assert len(cart) == 1
    assert cart[0]["quantity"] == 2
    assert "ít sốt" in rows[0][0]

    # Điều chỉnh số lượng tăng
    cart, rows, summary, msg = presenter.adjust_cart_item(cart, 0, 1)
    assert cart[0]["quantity"] == 3

    # Giảm số lượng
    cart, rows, summary, msg = presenter.adjust_cart_item(cart, 0, -1)
    assert cart[0]["quantity"] == 2

    # Xóa giỏ
    cart, rows, summary, msg = presenter.clear_cart()
    assert len(cart) == 0


def test_order_submission_and_table_mapping(context):
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 2, "Ghi chú 1", None)
    cart, rows, summary, msg = presenter.submit_order(cart, "T-01")

    assert len(cart) == 0
    assert "T-01" in msg or "Bàn 01" in msg

    table = presenter.table_manager.get_table("T-01")
    assert table is not None
    assert table.order_id is not None

    status = presenter.table_manager.get_table_status(table, context)
    assert "Có khách" in status or "Chờ bếp" in status

    # Kiểm tra chi tiết bàn
    details = presenter.get_table_details_markdown("T-01")
    assert "Bàn 01" in details
    assert table.order_id in details


def test_table_transfer_and_merge(context):
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 1, "", None)
    presenter.submit_order(cart, "T-01")

    # Chuyển bàn T-01 sang T-02
    msg, table_data = presenter.transfer_table("T-01", "T-02")
    assert "Đã chuyển" in msg
    assert presenter.table_manager.get_table("T-01").order_id is None
    assert presenter.table_manager.get_table("T-02").order_id is not None

    # Tạo đơn khác cho T-03
    cart2, _, _, _ = presenter.add_item_to_cart("MI-002", 1, "", None)
    presenter.submit_order(cart2, "T-03")

    # Gộp bàn T-03 vào T-02
    merge_msg, _ = presenter.merge_tables("T-03", "T-02")
    assert "Đã gộp" in merge_msg
    assert presenter.table_manager.get_table("T-03").order_id is None


def test_kitchen_queue_flow(context):
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 1, "", None)
    presenter.submit_order(cart, "T-04")

    queue_data = presenter.get_kitchen_queue_data()
    assert len(queue_data) >= 1

    row = queue_data[0]
    order_id = row[1]
    item_id = row[7]

    msg, queue_data = presenter.start_next_kitchen_item()
    assert "chế biến" in msg

    msg, _ = presenter.advance_kitchen_item(order_id, item_id, "READY")
    assert "READY" in msg

    msg, _ = presenter.advance_kitchen_item(order_id, item_id, "SERVED")
    assert "SERVED" in msg


def test_payment_and_invoice_history(context):
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 2, "", None)
    presenter.submit_order(cart, "T-05")

    order_id = presenter.table_manager.get_table("T-05").order_id
    assert order_id is not None

    # Phục vụ hết món tại bàn trước khi thanh toán
    presenter.mark_all_served_for_table("T-05")

    # Load bill preview
    rows, due_md, msg = presenter.load_bill_for_payment(order_id)
    assert len(rows) == 1
    assert "TỔNG CẦN THANH TOÁN" in due_md

    # Checkout
    checkout_msg, receipt, choices = presenter.execute_checkout(
        order_id, "💵 TIỀN MẶT (CASH)"
    )
    assert "Thanh toán thành công" in checkout_msg
    assert "HÓA ĐƠN BÁN HÀNG" in receipt

    # Bàn T-05 phải được giải phóng
    assert presenter.table_manager.get_table("T-05").order_id is None

    # Kiểm tra hóa đơn trong lịch sử
    today_iso = date.today().isoformat()
    hist_rows, stats_md = presenter.get_invoice_history(today_iso)
    assert len(hist_rows) >= 1
    assert any(r[0] == order_id for r in hist_rows)

    preview = presenter.get_invoice_preview(order_id)
    assert order_id in preview
