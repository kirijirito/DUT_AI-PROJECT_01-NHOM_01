import gradio as gr

from fnb.ui.app import create_app
from fnb.ui.presenter import FnbPresenter, format_vnd


def test_create_app_initializes_three_main_tabs(context):
    app = create_app(context)
    assert isinstance(app, gr.Blocks)
    assert app.title == "F&B Simple Order System"


def test_format_vnd():
    assert format_vnd(45_000) == "45.000 đ"
    assert format_vnd(0) == "0 đ"
    assert format_vnd(None) == "0 đ"


def test_cart_groups_same_menu_item_and_note(context):
    presenter = FnbPresenter(context)
    cart, rows, summary, message = presenter.add_item_to_cart(
        "MI-001", 2, "ít sốt", None
    )
    cart, rows, summary, message = presenter.add_item_to_cart(
        "MI-001", 3, "ít sốt", cart
    )
    assert len(cart) == 1
    assert cart[0]["quantity"] == 5
    assert rows[0][3] == "5"


def test_submit_order_updates_queue_and_payment_choices(context):
    presenter = FnbPresenter(context)
    cart, _, _, _ = presenter.add_item_to_cart("MI-001", 2, "", None)
    cart, cart_rows, summary, message, queue_rows, choices = presenter.submit_order(cart)

    assert cart == []
    assert cart_rows == []
    assert "Đã tạo đơn" in message
    assert len(queue_rows) == 1
    assert len(choices) == 1


def test_ui_presenter_receipt_groups_items(context):
    presenter = FnbPresenter(context)
    order = context.order_controller.create_order(
        [
            {"menu_item_id": "MI-001", "quantity": 1},
            {"menu_item_id": "MI-001", "quantity": 2},
        ]
    )
    context.kitchen_controller.serve_next_item()
    bill = context.payment_controller.preview_bill(order["id"])
    receipt = presenter.build_receipt(bill)
    assert "Burger Phô mai Gà" in receipt
    assert "3" in receipt
