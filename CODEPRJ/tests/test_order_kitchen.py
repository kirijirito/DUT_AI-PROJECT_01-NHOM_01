import pytest

from fnb.bootstrap import build_context
from fnb.exceptions import InvalidStateError, NotFoundError, ValidationError
from fnb.models import ItemStatus, OrderStatus


def test_create_order_adds_each_line_to_fifo_queue(context):
    first = context.order_controller.create_order([{"menu_item_id": "MI-001", "quantity": 2}])
    second = context.order_controller.create_order([{"menu_item_id": "MI-008", "quantity": 1}])

    queue = context.kitchen_controller.get_queue()
    assert [task["order_id"] for task in queue] == [first["id"], second["id"]]
    assert queue[0]["quantity"] == 2  # quantity=2 vẫn là một Queue task
    assert "table_id" not in first


def test_invalid_quantity_is_rejected(context):
    with pytest.raises(ValidationError):
        context.order_controller.create_order([{"menu_item_id": "MI-001", "quantity": 0}])


def test_unknown_menu_id_is_rejected(context):
    with pytest.raises(NotFoundError):
        context.order_controller.create_order([{"menu_item_id": "MI-NOT-FOUND", "quantity": 1}])


def test_add_items_appends_to_queue_and_snapshots_price(context):
    order = context.order_controller.create_order([{"menu_item_id": "MI-001", "quantity": 1}])
    original_price = order["items"][0]["unit_price"]

    updated = context.order_controller.add_items(
        order["id"], [{"menu_item_id": "MI-008", "quantity": 2, "note": "Giòn"}]
    )

    queue = context.kitchen_controller.get_queue()
    assert len(updated["items"]) == 2
    assert [task["menu_item_id"] for task in queue] == ["MI-001", "MI-008"]
    assert updated["items"][0]["unit_price"] == original_price
    assert updated["items"][1]["quantity"] == 2


def test_queue_rebuilds_from_json_after_restart_and_only_restores_queued(context, tmp_path):
    order = context.order_controller.create_order(
        [
            {"menu_item_id": "MI-001", "quantity": 1},
            {"menu_item_id": "MI-008", "quantity": 1},
        ]
    )
    started = context.kitchen_controller.start_next_item()
    assert started["status"] == ItemStatus.PREPARING.value

    new_context = build_context(tmp_path / "data")
    queue = new_context.kitchen_controller.get_queue()
    assert len(queue) == 1
    assert queue[0]["order_item_id"] == order["items"][1]["id"]
    reloaded = new_context.order_controller.get_order(order["id"])
    assert reloaded["items"][0]["status"] == ItemStatus.PREPARING.value


def test_cancel_order_only_when_all_items_queued_and_removes_queue(context):
    order = context.order_controller.create_order([{"menu_item_id": "MI-001", "quantity": 1}])
    cancelled = context.order_controller.cancel_order(order["id"], "Khách đổi ý")

    assert cancelled["status"] == OrderStatus.CANCELLED.value
    assert cancelled["cancel_reason"] == "Khách đổi ý"
    assert context.kitchen_controller.get_queue() == []


def test_cannot_cancel_order_after_preparation_started(context):
    order = context.order_controller.create_order([{"menu_item_id": "MI-001", "quantity": 1}])
    context.kitchen_controller.start_next_item()
    with pytest.raises(InvalidStateError):
        context.order_controller.cancel_order(order["id"])


def test_cannot_add_items_to_cancelled_order(context):
    order = context.order_controller.create_order([{"menu_item_id": "MI-001", "quantity": 1}])
    context.order_controller.cancel_order(order["id"])
    with pytest.raises(InvalidStateError):
        context.order_controller.add_items(order["id"], [{"menu_item_id": "MI-008", "quantity": 1}])


def test_simple_queue_fifo_operations():
    from fnb.simple_queue import SimpleQueue

    q = SimpleQueue("TestQueue")
    assert q.is_empty()
    assert q.size() == 0

    q.enqueue("Món A")
    q.enqueue("Món B")
    q.enqueue("Món C")

    assert q.size() == 3
    assert q.peek() == "Món A"
    assert q.dequeue() == "Món A"
    assert q.dequeue() == "Món B"
    assert q.dequeue() == "Món C"
    assert q.dequeue() is None
    assert q.is_empty()


def test_kitchen_three_queues_progression(context):
    """Kiểm tra dữ liệu vào là đơn hàng, ra 3 Queues: Chờ -> Đang nấu -> Chờ phục vụ."""
    order = context.order_controller.create_order([{"menu_item_id": "MI-001", "quantity": 1}])

    # 1. Món mới tạo nằm trong Queue Đang Đợi
    waiting = context.kitchen_controller.get_waiting_queue()
    cooking = context.kitchen_controller.get_cooking_queue()
    serving = context.kitchen_controller.get_serving_queue()

    assert len(waiting) == 1
    assert len(cooking) == 0
    assert len(serving) == 0
    assert waiting[0]["order_id"] == order["id"]

    # 2. Bắt đầu nấu -> chuyển sang Queue Đang Nấu
    started = context.kitchen_controller.start_next_item()
    assert started["status"] == ItemStatus.PREPARING.value

    assert len(context.kitchen_controller.get_waiting_queue()) == 0
    assert len(context.kitchen_controller.get_cooking_queue()) == 1
    assert len(context.kitchen_controller.get_serving_queue()) == 0

    # 3. Nấu xong -> chuyển sang Queue Chờ Phục Vụ
    finished = context.kitchen_controller.finish_next_item()
    assert finished["status"] == ItemStatus.READY.value

    assert len(context.kitchen_controller.get_waiting_queue()) == 0
    assert len(context.kitchen_controller.get_cooking_queue()) == 0
    assert len(context.kitchen_controller.get_serving_queue()) == 1

    # 4. Phục vụ -> chuyển sang SERVED
    served = context.kitchen_controller.serve_next_item()
    assert served["status"] == ItemStatus.SERVED.value

    assert len(context.kitchen_controller.get_waiting_queue()) == 0
    assert len(context.kitchen_controller.get_cooking_queue()) == 0
    assert len(context.kitchen_controller.get_serving_queue()) == 0
