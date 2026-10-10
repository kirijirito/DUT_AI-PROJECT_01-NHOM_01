"""CRUD cho bàn; dict giúp tra cứu theo mã bàn trung bình O(1)."""

from fnb.models import RestaurantTable
from fnb.storage.json_store import JsonStore


class TableRepository:
    def __init__(self, store: JsonStore) -> None:
        self._store = store
        self._tables_by_id: dict[str, RestaurantTable] = {
            row["id"]: RestaurantTable.from_dict(row) for row in store.load_records()
        }

    def get_by_id(self, table_id: str) -> RestaurantTable | None:
        return self._tables_by_id.get(table_id)

    def list_all(self) -> list[RestaurantTable]:
        return list(self._tables_by_id.values())

    def upsert(self, table: RestaurantTable) -> None:
        self._tables_by_id[table.id] = table
        self._persist()

    def delete(self, table_id: str) -> bool:
        if table_id not in self._tables_by_id:
            return False
        del self._tables_by_id[table_id]
        self._persist()
        return True

    def _persist(self) -> None:
        self._store.save_records([table.to_dict() for table in self._tables_by_id.values()])
