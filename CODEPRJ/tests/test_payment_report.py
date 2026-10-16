import pytest

from fnb.exceptions import InvalidStateError, ValidationError
from fnb.models import OrderStatus


def _make_all_items_ready(context, order: dict) -> None:
    for item in order["items"]:
        started = context.kitchen_controller.start_next_item()
        assert started["order_item_id"] == item["id"]
        context.kitchen_controller.mark_item_ready(order["id"], item["id"])


def test_checkout_requires_every_item_ready_or_served(context):
    order = context.order_controller.create_order(
        [{"menu_item_id": "MI-001", "quantity": 2}]
    )
    with pytest.raises(InvalidStateError):
        context.payment_controller.checkout(order["id"])


def test_checkout_saves_receipt_discount_and_prevents_second_payment(context):
    order = context.order_controller.create_order(
        [
            {"menu_item_id": "MI-007", "quantity": 2},  # 55,000 x 2
            {"menu_item_id": "MI-012", "quantity": 1},  # 18,000
        ]
    )
    _make_all_items_ready(context, order)

    preview = context.payment_controller.preview_bill(order["id"], 8_000)
    assert preview["total_before_discount"] == 128_000
    assert preview["total_due"] == 120_000

    paid = context.payment_controller.checkout(
        order["id"], payment_method="CASH", discount_amount=8_000
    )
    assert paid["status"] == OrderStatus.PAID.value
    assert paid["total_before_discount"] == 128_000
    assert paid["discount_amount"] == 8_000
    assert paid["total_paid"] == 120_000
    assert paid["payment_method"] == "CASH"
    assert paid["paid_at"] is not None

    receipt = context.payment_controller.preview_bill(order["id"])
    assert receipt["total_due"] == 120_000
    with pytest.raises(InvalidStateError):
        context.payment_controller.checkout(order["id"])


def test_discount_must_be_valid(context):
    order = context.order_controller.create_order(
        [{"menu_item_id": "MI-001", "quantity": 1}]
    )
    with pytest.raises(ValidationError):
        context.payment_controller.preview_bill(order["id"], -1)
    with pytest.raises(ValidationError):
        context.payment_controller.preview_bill(order["id"], 50_000)


def test_daily_report_counts_only_paid_orders(context):
    paid_order = context.order_controller.create_order(
        [{"menu_item_id": "MI-001", "quantity": 1}]
    )
    _make_all_items_ready(context, paid_order)
    context.payment_controller.checkout(paid_order["id"])

    context.order_controller.create_order(
        [{"menu_item_id": "MI-002", "quantity": 1}]
    )  # đơn OPEN không được tính vào doanh thu

    report = context.report_controller.daily_summary()
    assert report["paid_order_count"] == 1
    assert report["revenue_vnd"] == 45_000
    assert report["order_ids"] == [paid_order["id"]]


def test_invalid_report_date_is_rejected(context):
    with pytest.raises(ValidationError):
        context.report_controller.daily_summary("14-10-2026")


def test_paid_receipt_keeps_original_discount_even_if_ui_passes_zero(context):
    order = context.order_controller.create_order(
        [{"menu_item_id": "MI-001", "quantity": 1}]
    )
    _make_all_items_ready(context, order)
    context.payment_controller.checkout(
        order["id"], payment_method="CARD", discount_amount=5_000
    )

    receipt = context.payment_controller.preview_bill(order["id"], 0)
    assert receipt["discount_amount"] == 5_000
    assert receipt["total_due"] == 40_000
    assert receipt["payment_method"] == "CARD"
