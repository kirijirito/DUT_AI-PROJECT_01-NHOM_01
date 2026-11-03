"""Node của Linked List dùng bên trong Queue."""

from typing import Generic, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    """Một nút gồm dữ liệu và liên kết đến nút kế tiếp."""

    def __init__(self, data: T) -> None:
        self.data = data
        self.next: Node[T] | None = None
