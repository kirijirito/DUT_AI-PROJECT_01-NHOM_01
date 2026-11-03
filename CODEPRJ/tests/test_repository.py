import json

from fnb.repositories.menu_repository import MenuRepository
from fnb.storage.json_store import JsonStore


def test_menu_repository_looks_up_by_id(tmp_path):
    store = JsonStore(tmp_path / "menu.json")
    store.save_records(
        [
            {
                "id": "MI-T",
                "name": "Burger thử nghiệm",
                "category": "Món ăn",
                "price": 25_000,
                "is_available": True,
            }
        ]
    )
    repository = MenuRepository(store)
    assert repository.get_by_id("MI-T").name == "Burger thử nghiệm"
    assert repository.get_by_id("MI-NOT-FOUND") is None
    assert repository.list_all()[0].price == 25_000


def test_orders_json_is_initialized_as_empty_list(tmp_path):
    from fnb.bootstrap import build_context

    data_dir = tmp_path / "data"
    build_context(data_dir)
    saved = json.loads((data_dir / "orders.json").read_text(encoding="utf-8"))
    assert saved == []
