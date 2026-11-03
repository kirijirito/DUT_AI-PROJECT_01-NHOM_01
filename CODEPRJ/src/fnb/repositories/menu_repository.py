"""Repository chỉ đọc menu; dict là Hash Map tra cứu theo mã món."""

from fnb.models import MenuItem
from fnb.storage.json_store import JsonStore


class MenuRepository:
    def __init__(self, store: JsonStore) -> None:
        self._items_by_id: dict[str, MenuItem] = {
            row["id"]: MenuItem.from_dict(row) for row in store.load_records()
        }

    def get_by_id(self, item_id: str) -> MenuItem | None:
        item = self._items_by_id.get(item_id)
        return MenuItem.from_dict(item.to_dict()) if item is not None else None

    def list_all(self) -> list[MenuItem]:
        return [MenuItem.from_dict(item.to_dict()) for item in self._items_by_id.values()]
