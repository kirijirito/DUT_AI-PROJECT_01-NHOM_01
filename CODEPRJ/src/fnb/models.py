"""Mô hình dữ liệu dùng chung; không chứa luồng nghiệp vụ nhà hàng."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


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
    """Timestamp ISO 8601 có thông tin múi giờ."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class MenuItem:
    id: str
    name: str
    price: int
    category: str = "Khác"
    is_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "is_available": self.is_available,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MenuItem":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            price=int(data["price"]),
            category=str(data.get("category", data.get("group", "Khác"))),
            is_available=bool(data.get("is_available", True)),
        )


@dataclass
class OrderItem:
    """Một dòng món trong đơn; quantity không làm tăng số phần tử Queue."""

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
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN
    created_at: str = field(default_factory=now_iso)
    paid_at: str | None = None
    total_before_discount: int | None = None
    discount_amount: int = 0
    total_paid: int | None = None
    payment_method: str | None = None
    cancelled_at: str | None = None
    cancel_reason: str = ""

    @property
    def subtotal(self) -> int:
        return sum(item.line_total for item in self.items if item.status != ItemStatus.CANCELLED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "items": [item.to_dict() for item in self.items],
            "status": self.status.value,
            "created_at": self.created_at,
            "paid_at": self.paid_at,
            "total_before_discount": self.total_before_discount,
            "discount_amount": self.discount_amount,
            "total_paid": self.total_paid,
            "payment_method": self.payment_method,
            "cancelled_at": self.cancelled_at,
            "cancel_reason": self.cancel_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Order":
        total_before_discount = data.get("total_before_discount")
        total_paid = data.get("total_paid")
        return cls(
            id=str(data["id"]),
            items=[OrderItem.from_dict(item) for item in data.get("items", [])],
            status=OrderStatus(data.get("status", OrderStatus.OPEN.value)),
            created_at=str(data.get("created_at", now_iso())),
            paid_at=data.get("paid_at"),
            total_before_discount=(
                int(total_before_discount) if total_before_discount is not None else None
            ),
            discount_amount=int(data.get("discount_amount", 0)),
            total_paid=int(total_paid) if total_paid is not None else None,
            payment_method=data.get("payment_method"),
            cancelled_at=data.get("cancelled_at"),
            cancel_reason=str(data.get("cancel_reason", "")),
        )
