"""CRUD đơn hàng; dict lập chỉ mục theo mã đơn (tra cứu trung bình O(1))."""

from fnb.models import Order
from fnb.storage.json_store import JsonStore


class OrderRepository:
    def __init__(self, store: JsonStore) -> None:
        self._store = store
        self._orders_by_id: dict[str, Order] = {
            row["id"]: Order.from_dict(row) for row in store.load_records()
        }

    def get_by_id(self, order_id: str) -> Order | None:
        order = self._orders_by_id.get(order_id)
        return Order.from_dict(order.to_dict()) if order is not None else None

    def list_all(self) -> list[Order]:
        return [Order.from_dict(order.to_dict()) for order in self._orders_by_id.values()]

    def upsert(self, order: Order) -> None:
        candidate = self._orders_by_id.copy()
        candidate[order.id] = order
        self._persist(candidate)
        self._orders_by_id = candidate

    def delete(self, order_id: str) -> bool:
        """CRUD cấp Repository; Service không cho xóa đơn PAID/CANCELLED."""
        if order_id not in self._orders_by_id:
            return False
        candidate = self._orders_by_id.copy()
        del candidate[order_id]
        self._persist(candidate)
        self._orders_by_id = candidate
        return True

    def _persist(self, orders_by_id: dict[str, Order] | None = None) -> None:
        source = orders_by_id if orders_by_id is not None else self._orders_by_id
        self._store.save_records([order.to_dict() for order in source.values()])
