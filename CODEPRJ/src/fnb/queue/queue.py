"""Cài đặt Queue FIFO bằng Linked List, không dùng deque hoặc list làm Queue."""

from typing import Generic, Iterator, TypeVar

from fnb.queue.node import Node

T = TypeVar("T")


class Queue(Generic[T]):
    """Hàng đợi FIFO với Front, Rear và Size."""

    def __init__(self) -> None:
        self.front: Node[T] | None = None
        self.rear: Node[T] | None = None
        self._size = 0

    def enqueue(self, item: T) -> None:
        """Thêm một phần tử vào cuối hàng đợi. Độ phức tạp O(1)."""
        new_node = Node(item)

        if self.is_empty():
            self.front = new_node
            self.rear = new_node
        else:
            assert self.rear is not None
            self.rear.next = new_node
            self.rear = new_node

        self._size += 1

    def dequeue(self) -> T | None:
        """Lấy phần tử ở đầu hàng đợi. Độ phức tạp O(1)."""
        if self.is_empty():
            return None

        assert self.front is not None
        removed_data = self.front.data
        self.front = self.front.next
        self._size -= 1

        if self.front is None:
            self.rear = None

        return removed_data

    def peek(self) -> T | None:
        """Xem phần tử đầu tiên nhưng không xóa nó."""
        return self.front.data if self.front is not None else None

    def is_empty(self) -> bool:
        return self.front is None

    def size(self) -> int:
        return self._size

    def clear(self) -> None:
        """Xóa các liên kết trong Queue."""
        self.front = None
        self.rear = None
        self._size = 0

    def to_list(self) -> list[T]:
        """Tạo bản sao dạng list để hiển thị hoặc kiểm tra; không thay Queue."""
        result: list[T] = []
        current = self.front
        while current is not None:
            result.append(current.data)
            current = current.next
        return result

    def __iter__(self) -> Iterator[T]:
        current = self.front
        while current is not None:
            yield current.data
            current = current.next

    def __len__(self) -> int:
        return self._size
