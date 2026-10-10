"""Mô hình dữ liệu: định nghĩa hình dạng dữ liệu, không xử lý nghiệp vụ nhà hàng."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class TableStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"


class OrderStatus(StrEnum):
    OPEN = "OPEN"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class ItemStatus(StrEnum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"


def now_iso() -> str:
    """Tạo timestamp dạng ISO có timezone."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class MenuItem:
    id: str
    name: str
    price: int
    is_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "is_available": self.is_available,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MenuItem":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            price=int(data["price"]),
            is_available=bool(data.get("is_available", True)),
        )


@dataclass
class RestaurantTable:
    id: str
    name: str
    status: TableStatus = TableStatus.AVAILABLE
    current_order_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "current_order_id": self.current_order_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RestaurantTable":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            status=TableStatus(data.get("status", TableStatus.AVAILABLE.value)),
            current_order_id=data.get("current_order_id"),
        )


@dataclass
class OrderItem:
    id: str
    menu_item_id: str
    name: str
    unit_price: int
    quantity: int
    note: str = ""
    status: ItemStatus = ItemStatus.QUEUED
    queue_seq: int = 0

    @property
    def line_total(self) -> int:
        return self.unit_price * self.quantity

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "name": self.name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "note": self.note,
            "status": self.status.value,
            "queue_seq": self.queue_seq,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrderItem":
        return cls(
            id=str(data["id"]),
            menu_item_id=str(data["menu_item_id"]),
            name=str(data["name"]),
            unit_price=int(data["unit_price"]),
            quantity=int(data["quantity"]),
            note=str(data.get("note", "")),
            status=ItemStatus(data.get("status", ItemStatus.QUEUED.value)),
            queue_seq=int(data.get("queue_seq", 0)),
        )


@dataclass
class Order:
    id: str
    table_id: str
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN
    created_at: str = field(default_factory=now_iso)
    paid_at: str | None = None
    total_paid: int | None = None

    @property
    def subtotal(self) -> int:
        return sum(item.line_total for item in self.items if item.status != ItemStatus.CANCELLED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "table_id": self.table_id,
            "items": [item.to_dict() for item in self.items],
            "status": self.status.value,
            "created_at": self.created_at,
            "paid_at": self.paid_at,
            "total_paid": self.total_paid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Order":
        return cls(
            id=str(data["id"]),
            table_id=str(data["table_id"]),
            items=[OrderItem.from_dict(item) for item in data.get("items", [])],
            status=OrderStatus(data.get("status", OrderStatus.OPEN.value)),
            created_at=str(data.get("created_at", now_iso())),
            paid_at=data.get("paid_at"),
            total_paid=(int(data["total_paid"]) if data.get("total_paid") is not None else None),
        )
