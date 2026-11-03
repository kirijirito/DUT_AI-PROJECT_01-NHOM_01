import pytest

from fnb.exceptions import InvalidStateError


def _serve_all(context, order):
    for _ in order["items"]:
        context.kitchen_controller.serve_next_item()


def test_cannot_pay_until_every_item_is_served(context):
    order = context.order_controller.create_order(
        [
            {"menu_item_id": "MI-001", "quantity": 2},
            {"menu_item_id": "MI-009", "quantity": 1},
        ]
    )

    preview = context.payment_controller.preview_bill(order["id"])
    assert preview["can_pay"] is False
    assert preview["total_due"] == 105_000

    with pytest.raises(InvalidStateError):
        context.payment_controller.checkout(order["id"])


def test_bill_groups_same_dish_and_payment_succeeds_after_all_served(context):
    order = context.order_controller.create_order(
        [
            {"menu_item_id": "MI-001", "quantity": 2, "note": "ít sốt"},
            {"menu_item_id": "MI-001", "quantity": 1, "note": "không hành"},
            {"menu_item_id": "MI-009", "quantity": 2},
        ]
    )

    # Hai dòng Burger khác ghi chú vẫn là hai Node để bếp không mất ghi chú.
    assert len(order["items"]) == 3
    _serve_all(context, order)

    preview = context.payment_controller.preview_bill(order["id"])
    assert preview["can_pay"] is True
    burger = next(item for item in preview["items"] if item["menu_item_id"] == "MI-001")
    assert burger["quantity"] == 3
    assert burger["line_total"] == 135_000
    assert "ít sốt" in burger["note"] and "không hành" in burger["note"]

    paid = context.payment_controller.checkout(order["id"])
    assert paid["status"] == "PAID"
    assert paid["total_paid"] == 165_000
    assert paid["paid_at"] is not None

    with pytest.raises(InvalidStateError):
        context.payment_controller.checkout(order["id"])

    receipt = context.payment_controller.preview_bill(order["id"])
    assert receipt["status"] == "PAID"
    assert receipt["total_due"] == 165_000
