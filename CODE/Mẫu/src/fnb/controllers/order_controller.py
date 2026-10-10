from fnb.services.order_service import OrderService


class OrderController:
    def __init__(self, order_service: OrderService) -> None:
        self._order_service = order_service

    def create_order(self, table_id: str, lines: list[dict]) -> dict:
        return self._order_service.create_order(table_id, lines).to_dict()

    def get_order(self, order_id: str) -> dict:
        return self._order_service.get_order(order_id).to_dict()

    def cancel_order(self, order_id: str) -> dict:
        return self._order_service.cancel_order(order_id).to_dict()
