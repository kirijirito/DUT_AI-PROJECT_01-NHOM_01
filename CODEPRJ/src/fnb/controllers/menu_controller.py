from fnb.services.menu_service import MenuService


class MenuController:
    def __init__(self, menu_service: MenuService) -> None:
        self._menu_service = menu_service

    def list_menu(self, available_only: bool = True) -> list[dict]:
        return [item.to_dict() for item in self._menu_service.list_menu(available_only)]

    def get_item(self, menu_item_id: str) -> dict:
        return self._menu_service.get_item(menu_item_id).to_dict()
