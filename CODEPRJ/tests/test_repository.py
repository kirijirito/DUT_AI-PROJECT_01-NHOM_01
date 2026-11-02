import json

import pytest

from fnb.models import MenuItem
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


def test_menu_repository_upsert_persists_to_json(tmp_path):
    store = JsonStore(tmp_path / "menu.json")
    repository = MenuRepository(store)
    repository.upsert(MenuItem(id="MI-T", name="Món thử", price=12_000))

    reloaded_repository = MenuRepository(store)
    assert reloaded_repository.get_by_id("MI-T").price == 12_000
    saved = json.loads((tmp_path / "menu.json").read_text(encoding="utf-8"))
    assert saved[0]["category"] == "Khác"


def test_sample_data_does_not_include_tables(context):
    # Kiểm tra context khởi tạo không tạo file quản lý bàn.
    from fnb.bootstrap import DEFAULT_DATA_DIR

    assert not (DEFAULT_DATA_DIR / "tables.json").exists()


def test_failed_json_write_does_not_commit_repository_cache(tmp_path):
    from fnb.exceptions import StorageError

    store = JsonStore(tmp_path / "menu.json")
    repository = MenuRepository(store)

    def fail_write(_records):
        raise StorageError("simulated disk error")

    store.save_records = fail_write
    with pytest.raises(StorageError):
        repository.upsert(MenuItem(id="MI-FAIL", name="Món lỗi", price=10_000))

    assert repository.get_by_id("MI-FAIL") is None
