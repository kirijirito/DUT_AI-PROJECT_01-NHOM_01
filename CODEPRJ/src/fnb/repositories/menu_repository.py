"""CRUD thực đơn; dict lập chỉ mục theo mã món (tra cứu trung bình O(1))."""

from fnb.models import MenuItem
from fnb.storage.json_store import JsonStore


class MenuRepository:
    def __init__(self, store: JsonStore) -> None:
        self._store = store
        self._items_by_id: dict[str, MenuItem] = {
            row["id"]: MenuItem.from_dict(row) for row in store.load_records()
        }

    def get_by_id(self, item_id: str) -> MenuItem | None:
        item = self._items_by_id.get(item_id)
        return MenuItem.from_dict(item.to_dict()) if item is not None else None

    def list_all(self) -> list[MenuItem]:
        return [MenuItem.from_dict(item.to_dict()) for item in self._items_by_id.values()]

    def upsert(self, item: MenuItem) -> None:
        candidate = self._items_by_id.copy()
        candidate[item.id] = item
        self._persist(candidate)
        self._items_by_id = candidate

    def delete(self, item_id: str) -> bool:
        if item_id not in self._items_by_id:
            return False
        candidate = self._items_by_id.copy()
        del candidate[item_id]
        self._persist(candidate)
        self._items_by_id = candidate
        return True

    def _persist(self, items_by_id: dict[str, MenuItem] | None = None) -> None:
        source = items_by_id if items_by_id is not None else self._items_by_id
        self._store.save_records([item.to_dict() for item in source.values()])
