"""CRUD cho menu; dict giúp tra cứu theo mã món trung bình O(1)."""

from fnb.models import MenuItem
from fnb.storage.json_store import JsonStore


class MenuRepository:
    def __init__(self, store: JsonStore) -> None:
        self._store = store
        self._items_by_id: dict[str, MenuItem] = {
            row["id"]: MenuItem.from_dict(row) for row in store.load_records()
        }

    def get_by_id(self, item_id: str) -> MenuItem | None:
        return self._items_by_id.get(item_id)

    def list_all(self) -> list[MenuItem]:
        return list(self._items_by_id.values())

    def upsert(self, item: MenuItem) -> None:
        self._items_by_id[item.id] = item
        self._persist()

    def delete(self, item_id: str) -> bool:
        if item_id not in self._items_by_id:
            return False
        del self._items_by_id[item_id]
        self._persist()
        return True

    def _persist(self) -> None:
        self._store.save_records([item.to_dict() for item in self._items_by_id.values()])
