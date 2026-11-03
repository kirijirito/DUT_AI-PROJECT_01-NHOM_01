import json

from fnb.bootstrap import build_context
from fnb.models import ItemStatus


def test_create_order_groups_same_item_and_enqueues_one_node_per_line(context):
    order = context.order_controller.create_order(
        [
            {"menu_item_id": "MI-001", "quantity": 2, "note": "ít sốt"},
            {"menu_item_id": "MI-001", "quantity": 3, "note": "ít sốt"},
            {"menu_item_id": "MI-009", "quantity": 1, "note": ""},
        ]
    )

    assert len(order["items"]) == 2
    assert order["items"][0]["quantity"] == 5
    assert order["items"][0]["status"] == ItemStatus.QUEUED.value
    queue = context.kitchen_controller.get_queue()
    assert len(queue) == 2
    assert [item["name"] for item in queue] == ["Burger Phô mai Gà", "Pepsi"]


def test_queue_is_served_in_fifo_order_and_only_two_item_states(context):
    first = context.order_controller.create_order(
        [{"menu_item_id": "MI-001", "quantity": 2}]
    )
    second = context.order_controller.create_order(
        [{"menu_item_id": "MI-009", "quantity": 1}]
    )

    queue_before = context.kitchen_controller.get_queue()
    assert [row["order_id"] for row in queue_before] == [first["id"], second["id"]]

    served = context.kitchen_controller.serve_next_item()
    assert served["order_id"] == first["id"]
    assert served["status"] == "SERVED"
    assert [row["order_id"] for row in context.kitchen_controller.get_queue()] == [second["id"]]

    statuses = {
        item["status"]
        for order in context.order_controller.list_orders()
        for item in order["items"]
    }
    assert statuses <= {"QUEUED", "SERVED"}


def test_queue_is_persisted_and_restored_after_restarting_context(tmp_path):
    data_dir = tmp_path / "data"
    first_context = build_context(data_dir)
    created = first_context.order_controller.create_order(
        [
            {"menu_item_id": "MI-001", "quantity": 2},
            {"menu_item_id": "MI-009", "quantity": 1},
        ]
    )

    stored = json.loads((data_dir / "orders.json").read_text(encoding="utf-8"))
    assert all(item["status"] == "QUEUED" for item in stored[0]["items"])
    assert [item["queue_seq"] for item in stored[0]["items"]] == [1, 2]

    restarted_context = build_context(data_dir)
    restored = restarted_context.kitchen_controller.get_queue()
    assert [item["order_item_id"] for item in restored] == [
        item["id"] for item in created["items"]
    ]

    restarted_context.kitchen_controller.serve_next_item()
    after_serve = json.loads((data_dir / "orders.json").read_text(encoding="utf-8"))
    assert after_serve[0]["items"][0]["status"] == "SERVED"
    assert after_serve[0]["items"][1]["status"] == "QUEUED"

    restarted_again = build_context(data_dir)
    assert [item["order_item_id"] for item in restarted_again.kitchen_controller.get_queue()] == [
        created["items"][1]["id"]
    ]


def test_serving_empty_queue_returns_business_error(context):
    import pytest
    from fnb.exceptions import InvalidStateError

    with pytest.raises(InvalidStateError):
        context.kitchen_controller.serve_next_item()


def test_queue_keeps_front_node_when_json_save_fails(context):
    from fnb.exceptions import StorageError

    context.order_controller.create_order(
        [{"menu_item_id": "MI-001", "quantity": 1}]
    )
    kitchen_service = context.kitchen_controller._kitchen_service
    order_repository = kitchen_service._order_repository
    original_upsert = order_repository.upsert
    first_entry = kitchen_service.queue.peek()

    def fail_save(_order):
        raise StorageError("simulated JSON write error")

    order_repository.upsert = fail_save
    try:
        import pytest

        with pytest.raises(StorageError):
            context.kitchen_controller.serve_next_item()
        assert kitchen_service.queue.peek() == first_entry
        assert kitchen_service.queue.size() == 1
    finally:
        order_repository.upsert = original_upsert

    served = context.kitchen_controller.serve_next_item()
    assert served["status"] == "SERVED"
    assert kitchen_service.queue.is_empty()
