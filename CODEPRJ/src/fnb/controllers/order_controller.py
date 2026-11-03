from fnb.services.order_service import OrderService


class OrderController:
    def __init__(self, order_service: OrderService) -> None:
        self._order_service = order_service

    def create_order(self, lines: list[dict]) -> dict:
        return self._order_service.create_order(lines).to_dict()

    def get_order(self, order_id: str) -> dict:
        return self._order_service.get_order(order_id).to_dict()

    def list_orders(self) -> list[dict]:
        return [order.to_dict() for order in self._order_service.list_orders()]
