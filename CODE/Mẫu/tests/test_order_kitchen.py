import pytest

from fnb.bootstrap import build_context
from fnb.exceptions import InvalidStateError, ValidationError


def test_create_order_adds_lines_to_fifo_queue(context):
    first = context.order_controller.create_order(
        "TBL-01", [{"menu_item_id": "MI-001", "quantity": 2}]
    )
    second = context.order_controller.create_order(
        "TBL-02", [{"menu_item_id": "MI-008", "quantity": 1}]
    )
    queue = context.kitchen_controller.get_queue()
    assert queue[0]["order_id"] == first["id"]
    assert queue[1]["order_id"] == second["id"]
    assert queue[0]["quantity"] == 2


def test_non_positive_quantity_is_rejected(context):
    with pytest.raises(ValidationError):
        context.order_controller.create_order(
            "TBL-01", [{"menu_item_id": "MI-001", "quantity": 0}]
        )


def test_queue_rebuilds_from_json_after_restart(context, tmp_path):
    created = context.order_controller.create_order(
        "TBL-01", [{"menu_item_id": "MI-001", "quantity": 1}]
    )
    new_context = build_context(tmp_path / "data")
    queue = new_context.kitchen_controller.get_queue()
    assert len(queue) == 1
    assert queue[0]["order_id"] == created["id"]


def test_cannot_start_next_when_queue_is_empty(context):
    # Đặt món trước rồi lấy món, để sau đó Queue rỗng.
    context.order_controller.create_order(
        "TBL-01", [{"menu_item_id": "MI-001", "quantity": 1}]
    )
    context.kitchen_controller.start_next_item()
    with pytest.raises(InvalidStateError):
        context.kitchen_controller.start_next_item()
