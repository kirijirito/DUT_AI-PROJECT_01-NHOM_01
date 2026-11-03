"""Repository đơn hàng; dict dùng làm Hash Map tra cứu theo mã đơn."""

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
        """Ghi JSON trước, sau đó mới cập nhật Hash Map trong bộ nhớ."""
        candidate = self._orders_by_id.copy()
        candidate[order.id] = Order.from_dict(order.to_dict())
        self._store.save_records([item.to_dict() for item in candidate.values()])
        self._orders_by_id = candidate
