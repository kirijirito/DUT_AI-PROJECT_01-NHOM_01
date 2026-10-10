from fnb.models import MenuItem
from fnb.repositories.menu_repository import MenuRepository
from fnb.storage.json_store import JsonStore


def test_menu_repository_looks_up_by_id(tmp_path):
    store = JsonStore(tmp_path / "menu.json")
    store.save_records(
        [
            {"id": "MI-T", "name": "Burger thử nghiệm", "price": 25000, "is_available": True}
        ]
    )
    repository = MenuRepository(store)

    assert repository.get_by_id("MI-T").name == "Burger thử nghiệm"
    assert repository.get_by_id("MI-NOT-FOUND") is None


def test_menu_repository_upsert_persists_to_json(tmp_path):
    store = JsonStore(tmp_path / "menu.json")
    repository = MenuRepository(store)
    repository.upsert(MenuItem(id="MI-T", name="Món thử", price=12000))

    # Tạo Repository mới mô phỏng việc đọc dữ liệu khi ứng dụng khởi động lại.
    reloaded_repository = MenuRepository(store)
    assert reloaded_repository.get_by_id("MI-T").price == 12000
