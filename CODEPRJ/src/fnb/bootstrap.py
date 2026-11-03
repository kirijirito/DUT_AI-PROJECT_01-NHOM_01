"""Khởi tạo và kết nối các lớp của ứng dụng."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from fnb.controllers.kitchen_controller import KitchenController
from fnb.controllers.menu_controller import MenuController
from fnb.controllers.order_controller import OrderController
from fnb.controllers.payment_controller import PaymentController
from fnb.repositories.menu_repository import MenuRepository
from fnb.repositories.order_repository import OrderRepository
from fnb.services.kitchen_service import KitchenService
from fnb.services.menu_service import MenuService
from fnb.services.order_service import OrderService
from fnb.services.payment_service import PaymentService
from fnb.storage.json_store import JsonStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DATA_FILES = ("menu.json", "orders.json")


@dataclass
class AppContext:
    menu_controller: MenuController
    order_controller: OrderController
    kitchen_controller: KitchenController
    payment_controller: PaymentController


def _ensure_data_files(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename in DATA_FILES:
        target = data_dir / filename
        source = DEFAULT_DATA_DIR / filename
        if not target.exists():
            if source.exists():
                shutil.copyfile(source, target)
            else:
                target.write_text("[]\n", encoding="utf-8")


def build_context(data_dir: str | Path | None = None) -> AppContext:
    """Nạp dữ liệu, khôi phục Queue rồi kết nối Controller."""
    chosen_data_dir = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    _ensure_data_files(chosen_data_dir)

    menu_repository = MenuRepository(JsonStore(chosen_data_dir / "menu.json"))
    order_repository = OrderRepository(JsonStore(chosen_data_dir / "orders.json"))

    menu_service = MenuService(menu_repository)
    kitchen_service = KitchenService(order_repository)
    order_service = OrderService(order_repository, menu_service, kitchen_service)
    payment_service = PaymentService(order_repository)

    return AppContext(
        menu_controller=MenuController(menu_service),
        order_controller=OrderController(order_service),
        kitchen_controller=KitchenController(kitchen_service),
        payment_controller=PaymentController(payment_service),
    )
