from fnb.services.kitchen_service import KitchenService


class KitchenController:
    def __init__(self, kitchen_service: KitchenService) -> None:
        self._kitchen_service = kitchen_service

    def get_queue(self) -> list[dict]:
        return self._kitchen_service.get_queue()

    def get_served_items(self) -> list[dict]:
        return self._kitchen_service.get_served_items()

    def serve_next_item(self) -> dict:
        return self._kitchen_service.serve_next_item()
