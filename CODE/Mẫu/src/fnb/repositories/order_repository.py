"""CRUD cho đơn; danh sách đơn được lập chỉ mục theo order ID."""

from fnb.models import Order
from fnb.storage.json_store import JsonStore


class OrderRepository:
    def __init__(self, store: JsonStore) -> None:
        self._store = store
        self._orders_by_id: dict[str, Order] = {
            row["id"]: Order.from_dict(row) for row in store.load_records()
        }

    def get_by_id(self, order_id: str) -> Order | None:
        return self._orders_by_id.get(order_id)

    def list_all(self) -> list[Order]:
        return list(self._orders_by_id.values())

    def upsert(self, order: Order) -> None:
        self._orders_by_id[order.id] = order
        self._persist()

    def delete(self, order_id: str) -> bool:
        """Chỉ phục vụ CRUD cơ bản; nghiệp vụ không nên xóa đơn đã thanh toán."""
        if order_id not in self._orders_by_id:
            return False
        del self._orders_by_id[order_id]
        self._persist()
        return True

    def _persist(self) -> None:
        self._store.save_records([order.to_dict() for order in self._orders_by_id.values()])
