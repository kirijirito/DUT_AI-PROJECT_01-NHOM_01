"""Composition root: khởi tạo và nối Repository, Service, Controller."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from fnb.controllers.kitchen_controller import KitchenController
from fnb.controllers.menu_controller import MenuController
from fnb.controllers.order_controller import OrderController
from fnb.controllers.payment_controller import PaymentController
from fnb.controllers.report_controller import ReportController
from fnb.repositories.menu_repository import MenuRepository
from fnb.repositories.order_repository import OrderRepository
from fnb.services.kitchen_service import KitchenService
from fnb.services.menu_service import MenuService
from fnb.services.order_service import OrderService
from fnb.services.payment_service import PaymentService
from fnb.services.report_service import ReportService
from fnb.storage.json_store import JsonStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DATA_FILES = ("menu.json", "orders.json")


@dataclass
class AppContext:
    """Tập hợp Controller mà UI cần gọi; cũng dùng trong kiểm thử tích hợp."""

    menu_controller: MenuController
    order_controller: OrderController
    kitchen_controller: KitchenController
    payment_controller: PaymentController
    report_controller: ReportController


def _ensure_data_files(data_dir: Path) -> None:
    """Tạo file từ mẫu nếu chưa có; không ghi đè dữ liệu đang tồn tại."""
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename in DATA_FILES:
        target = data_dir / filename
        source = DEFAULT_DATA_DIR / filename
        if not target.exists():
            if not source.exists():
                target.write_text("[]\n", encoding="utf-8")
            else:
                shutil.copyfile(source, target)


def build_context(data_dir: str | Path | None = None) -> AppContext:
    """Khởi tạo dependency; có thể dùng thư mục tạm khi chạy test."""
    chosen_data_dir = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    _ensure_data_files(chosen_data_dir)

    menu_repository = MenuRepository(JsonStore(chosen_data_dir / "menu.json"))
    order_repository = OrderRepository(JsonStore(chosen_data_dir / "orders.json"))

    menu_service = MenuService(menu_repository)
    kitchen_service = KitchenService(order_repository)  # Dựng lại Queue khi khởi động.
    order_service = OrderService(order_repository, menu_service, kitchen_service)
    payment_service = PaymentService(order_repository)
    report_service = ReportService(order_repository)

    return AppContext(
        menu_controller=MenuController(menu_service),
        order_controller=OrderController(order_service),
        kitchen_controller=KitchenController(kitchen_service),
        payment_controller=PaymentController(payment_service),
        report_controller=ReportController(report_service),
    )
