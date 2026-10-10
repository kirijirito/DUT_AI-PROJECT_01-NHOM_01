from fnb.services.menu_service import MenuService


class MenuController:
    def __init__(self, menu_service: MenuService) -> None:
        self._menu_service = menu_service

    def list_menu(self) -> list[dict]:
        return [item.to_dict() for item in self._menu_service.list_menu()]
