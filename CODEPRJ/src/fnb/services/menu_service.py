"""Nghiệp vụ tra cứu thực đơn."""

from fnb.exceptions import NotFoundError
from fnb.models import MenuItem
from fnb.repositories.menu_repository import MenuRepository


class MenuService:
    def __init__(self, menu_repository: MenuRepository) -> None:
        self._menu_repository = menu_repository

    def list_menu(self, available_only: bool = True) -> list[MenuItem]:
        items = self._menu_repository.list_all()
        return [item for item in items if item.is_available] if available_only else items

    def get_item(self, menu_item_id: str) -> MenuItem:
        item = self._menu_repository.get_by_id(menu_item_id)
        if item is None:
            raise NotFoundError(f"Không tìm thấy món có mã {menu_item_id}.")
        return item
