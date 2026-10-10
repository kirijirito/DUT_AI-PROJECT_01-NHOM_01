"""Nghiệp vụ tra cứu menu."""

from fnb.exceptions import NotFoundError
from fnb.models import MenuItem
from fnb.repositories.menu_repository import MenuRepository


class MenuService:
    def __init__(self, menu_repository: MenuRepository) -> None:
        self._menu_repository = menu_repository

    def list_menu(self) -> list[MenuItem]:
        return self._menu_repository.list_all()

    def get_item(self, menu_item_id: str) -> MenuItem:
        item = self._menu_repository.get_by_id(menu_item_id)
        if item is None:
            raise NotFoundError(f"Không tìm thấy món có mã {menu_item_id}.")
        return item
