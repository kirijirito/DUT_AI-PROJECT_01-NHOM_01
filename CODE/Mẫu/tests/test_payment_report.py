import pytest

from fnb.exceptions import InvalidStateError


def test_checkout_requires_items_to_be_ready(context):
    order = context.order_controller.create_order(
        "TBL-01", [{"menu_item_id": "MI-001", "quantity": 2}]
    )
    with pytest.raises(InvalidStateError):
        context.payment_controller.checkout(order["id"])


def test_checkout_after_ready_saves_paid_order_and_frees_table(context):
    order = context.order_controller.create_order(
        "TBL-01", [{"menu_item_id": "MI-001", "quantity": 2}]
    )
    started = context.kitchen_controller.start_next_item()
    context.kitchen_controller.mark_item_ready(order["id"], started["order_item_id"])
    paid = context.payment_controller.checkout(order["id"])

    assert paid["status"] == "PAID"
    assert paid["total_paid"] == 2 * 45000
    table = next(t for t in context.table_controller.list_tables() if t["id"] == "TBL-01")
    assert table["status"] == "AVAILABLE"
    assert table["current_order_id"] is None

    with pytest.raises(InvalidStateError):
        context.payment_controller.checkout(order["id"])


def test_daily_report_counts_paid_orders(context):
    order = context.order_controller.create_order(
        "TBL-01", [{"menu_item_id": "MI-001", "quantity": 1}]
    )
    started = context.kitchen_controller.start_next_item()
    context.kitchen_controller.mark_item_ready(order["id"], started["order_item_id"])
    context.payment_controller.checkout(order["id"])
    report = context.report_controller.daily_summary()
    assert report["paid_order_count"] == 1
    assert report["revenue_vnd"] == 45000
