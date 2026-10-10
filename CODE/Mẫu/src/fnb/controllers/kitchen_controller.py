from fnb.services.kitchen_service import KitchenService


class KitchenController:
    def __init__(self, kitchen_service: KitchenService) -> None:
        self._kitchen_service = kitchen_service

    def get_queue(self) -> list[dict]:
        return self._kitchen_service.get_queue()

    def start_next_item(self) -> dict:
        return self._kitchen_service.start_next_item()

    def mark_item_ready(self, order_id: str, item_id: str) -> dict:
        return self._kitchen_service.mark_item_ready(order_id, item_id).to_dict()

    def mark_item_served(self, order_id: str, item_id: str) -> dict:
        return self._kitchen_service.mark_item_served(order_id, item_id).to_dict()
