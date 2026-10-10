from fnb.services.table_service import TableService


class TableController:
    def __init__(self, table_service: TableService) -> None:
        self._table_service = table_service

    def list_tables(self) -> list[dict]:
        return [table.to_dict() for table in self._table_service.list_tables()]
