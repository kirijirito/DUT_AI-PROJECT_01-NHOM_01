"""Nghiệp vụ về trạng thái và liên kết bàn với đơn hiện tại."""

from fnb.exceptions import ConflictError, InvalidStateError, NotFoundError
from fnb.models import RestaurantTable, TableStatus
from fnb.repositories.table_repository import TableRepository


class TableService:
    def __init__(self, table_repository: TableRepository) -> None:
        self._table_repository = table_repository

    def list_tables(self) -> list[RestaurantTable]:
        return self._table_repository.list_all()

    def get_table(self, table_id: str) -> RestaurantTable:
        table = self._table_repository.get_by_id(table_id)
        if table is None:
            raise NotFoundError(f"Không tìm thấy bàn {table_id}.")
        return table

    def ensure_available(self, table_id: str) -> RestaurantTable:
        table = self.get_table(table_id)
        if table.status != TableStatus.AVAILABLE or table.current_order_id is not None:
            raise ConflictError(f"{table.name} đang có đơn hàng.")
        return table

    def occupy(self, table_id: str, order_id: str) -> RestaurantTable:
        table = self.ensure_available(table_id)
        table.status = TableStatus.OCCUPIED
        table.current_order_id = order_id
        self._table_repository.upsert(table)
        return table

    def release(self, table_id: str, order_id: str) -> RestaurantTable:
        table = self.get_table(table_id)
        if table.current_order_id != order_id:
            raise InvalidStateError(
                f"Không thể giải phóng bàn {table_id}: bàn không liên kết với đơn {order_id}."
            )
        table.status = TableStatus.AVAILABLE
        table.current_order_id = None
        self._table_repository.upsert(table)
        return table
