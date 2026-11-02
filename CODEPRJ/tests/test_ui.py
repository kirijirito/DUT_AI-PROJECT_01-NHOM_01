"""Kiểm thử tầng Giao diện Người dùng (UI) và Presenter (3 Queues, Giỏ hàng, Thanh toán)."""

import gradio as gr

from fnb.ui.app import create_app
from fnb.ui.presenter import FnbPresenter, format_vnd


def test_create_app_initializes_blocks(context):
    app = create_app(context)
    assert isinstance(app, gr.Blocks)
    assert app.title == "F&B Order Management System"


def test_format_vnd():
    assert format_vnd(45000) == "45.000 ₫"
    assert format_vnd(0) == "0 ₫"
    assert format_vnd(None) == "0 ₫"
    assert format_vnd("abc") == "0 ₫"


def test_cart_operations(context):
    presenter = FnbPresenter(context)
    cart, rows, summary, msg = presenter.add_item_to_cart("MI-001", 2, "ít sốt", None)
    assert len(cart) == 1
    assert cart[0]["quantity"] == 2
    assert "Burger Phô mai Gà" in rows[0][0]

    # Điều chỉnh số lượng tăng
    cart, rows, summary, msg = presenter.adjust_cart_item(cart, 0, 1)
    assert cart[0]["quantity"] == 3

    # Giảm số lượng
    cart, rows, summary, msg = presenter.adjust_cart_item(cart, 0, -1)
    assert cart[0]["quantity"] == 2

    # Xóa giỏ
    cart, rows, summary, msg = presenter.clear_cart()
    assert len(cart) == 0


def test_order_creation_and_waiting_queue(context):
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 2, "Ghi chú 1", None)

    # Tạo đơn hàng -> các món tự động vào Queue 1: Đang Đợi
    cart, rows, summary, msg = presenter.submit_order(cart)
    assert len(cart) == 0
    assert "ORD-" in msg

    waiting_data = presenter.get_waiting_queue_data()
    assert len(waiting_data) >= 1
    assert waiting_data[0][2] == "Burger Phô mai Gà"
    assert waiting_data[0][3] == "2"


def test_3_queues_transitions(context):
    """Kiểm tra luồng luân chuyển món qua đúng 3 Hàng đợi:
    Queue Đang Đợi -> Queue Đang Nấu -> Queue Chờ Phục Vụ -> Đã Phục Vụ.
    """
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 1, "", None)
    presenter.submit_order(cart)

    # 1. Ban đầu món nằm trong Queue Đang Đợi
    assert len(presenter.get_waiting_queue_data()) == 1
    assert len(presenter.get_cooking_queue_data()) == 0
    assert len(presenter.get_serving_queue_data()) == 0

    # 2. Bắt đầu nấu -> chuyển sang Queue Đang Nấu
    msg, waiting, cooking = presenter.start_next_kitchen_item()
    assert "bắt đầu nấu" in msg
    assert len(waiting) == 0
    assert len(cooking) == 1

    # 3. Nấu xong -> chuyển sang Queue Chờ Phục Vụ
    msg, cooking, serving = presenter.finish_next_kitchen_item()
    assert "đã nấu xong" in msg
    assert len(cooking) == 0
    assert len(serving) == 1

    # 4. Phục vụ khách -> hoàn thành phục vụ
    msg, serving = presenter.serve_next_kitchen_item()
    assert "Đã phục vụ" in msg
    assert len(serving) == 0


def test_advance_kitchen_item_by_id(context):
    """Kiểm tra cập nhật trạng thái món theo mã ID cụ thể."""
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-002", 1, "", None)
    presenter.submit_order(cart)

    # Chuyển sang đang nấu bằng start_next
    presenter.start_next_kitchen_item()
    cooking_data = presenter.get_cooking_queue_data()
    order_id = cooking_data[0][1]
    item_id = cooking_data[0][5]

    # Cập nhật bằng ID sang READY (Chờ phục vụ)
    msg, _, _, serving = presenter.advance_kitchen_item(order_id, item_id, "READY")
    assert "READY" in msg or "nấu xong" in msg
    assert len(serving) == 1

    # Cập nhật bằng ID sang SERVED (Đã phục vụ)
    msg, _, _, serving = presenter.advance_kitchen_item(order_id, item_id, "SERVED")
    assert "SERVED" in msg or "phục vụ" in msg
    assert len(serving) == 0


def test_payment_and_receipt(context):
    """Kiểm tra quy trình thanh toán đơn giản và in hóa đơn."""
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 2, "", None)
    presenter.submit_order(cart)

    # Lấy danh sách đơn mở
    choices = presenter.get_open_orders_choices()
    assert len(choices) >= 1
    order_id = choices[0][1]

    # Phục vụ món trước khi thanh toán
    presenter.start_next_kitchen_item()
    presenter.finish_next_kitchen_item()
    presenter.serve_next_kitchen_item()

    # Xem trước hóa đơn với giảm giá 5.000đ
    rows, due_md, msg = presenter.load_bill_for_payment(order_id, discount=5000)
    assert len(rows) == 1
    assert "85.000 ₫" in due_md

    # Thực hiện thanh toán
    msg, receipt, choices = presenter.execute_checkout(
        order_id, "💵 TIỀN MẶT (CASH)", discount=5000
    )
    assert "Thanh toán thành công" in msg
    assert "HÓA ĐƠN BÁN HÀNG" in receipt
    assert "85.000 ₫" in receipt


def test_hash_map_lookup_and_report(context):
    """Kiểm tra tra cứu tức thời O(1) theo mã đơn và báo cáo tổng quan."""
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 1, "", None)
    presenter.submit_order(cart)

    choices = presenter.get_open_orders_choices()
    order_id = choices[0][1]

    # Tra cứu O(1)
    result_md = presenter.lookup_order_hash(order_id)
    assert order_id in result_md
    assert "Burger Phô mai Gà" in result_md

    # Thống kê tổng quan
    summary_md, history = presenter.get_summary_report()
    assert "BÁO CÁO TỔNG QUAN" in summary_md
