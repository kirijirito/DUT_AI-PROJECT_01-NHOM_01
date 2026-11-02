"""Cấu trúc dữ liệu Hàng đợi (Queue) theo nguyên lý FIFO (First In, First Out).

Dành cho sinh viên học OOP và Cấu trúc dữ liệu & Giải thuật.
"""

from collections import deque
from collections.abc import Callable
from typing import Any


class SimpleQueue:
    """Lớp Hàng đợi FIFO đơn giản, trực quan.

    Các thao tác cơ bản:
      - enqueue: Thêm phần tử vào cuối hàng đợi (O(1))
      - dequeue: Lấy phần tử ở đầu hàng đợi ra (O(1))
      - peek: Xem phần tử ở đầu hàng đợi mà không xóa nó
      - is_empty: Kiểm tra hàng đợi có rỗng không
      - size: Trả về số lượng phần tử hiện tại
      - to_list: Chuyển toàn bộ phần tử trong hàng đợi thành list
    """

    def __init__(self, name: str = "Queue") -> None:
        self.name = name
        self._items: deque[Any] = deque()

    def enqueue(self, item: Any) -> None:
        """Đưa phần tử vào cuối hàng đợi (Push/Enqueue)."""
        self._items.append(item)

    def dequeue(self) -> Any | None:
        """Lấy phần tử đầu tiên ra khỏi hàng đợi (Pop/Dequeue theo FIFO)."""
        if self.is_empty():
            return None
        return self._items.popleft()

    def peek(self) -> Any | None:
        """Xem phần tử đầu tiên mà không xóa khỏi hàng đợi."""
        if self.is_empty():
            return None
        return self._items[0]

    def is_empty(self) -> bool:
        """Hàng đợi có rỗng không."""
        return len(self._items) == 0

    def size(self) -> int:
        """Số lượng phần tử hiện tại trong hàng đợi."""
        return len(self._items)

    def to_list(self) -> list[Any]:
        """Trả về danh sách các phần tử theo thứ tự FIFO (từ đầu đến cuối)."""
        return list(self._items)

    def remove_if(self, predicate: Callable[[Any], bool]) -> None:
        """Xóa các phần tử thỏa mãn điều kiện predicate (ví dụ khi hủy đơn hàng)."""
        self._items = deque(item for item in self._items if not predicate(item))

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"SimpleQueue(name='{self.name}', size={self.size()})"
