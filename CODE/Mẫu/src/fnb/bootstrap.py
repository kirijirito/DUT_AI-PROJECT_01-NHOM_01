"""Composition root: tạo Repository, Service, Controller và nối chúng với nhau."""

from dataclasses import dataclass
from pathlib import Path
import shutil

from fnb.controllers.kitchen_controller import KitchenController
from fnb.controllers.menu_controller import MenuController
from fnb.controllers.order_controller import OrderController
from fnb.controllers.payment_controller import PaymentController
from fnb.controllers.report_controller import ReportController
from fnb.controllers.table_controller import TableController
from fnb.repositories.menu_repository import MenuRepository
from fnb.repositories.order_repository import OrderRepository
from fnb.repositories.table_repository import TableRepository
from fnb.services.kitchen_service import KitchenService
from fnb.services.menu_service import MenuService
from fnb.services.order_service import OrderService
from fnb.services.payment_service import PaymentService
from fnb.services.report_service import ReportService
from fnb.services.table_service import TableService
from fnb.storage.json_store import JsonStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DATA_FILES = ("menu.json", "tables.json", "orders.json")


@dataclass
class AppContext:
    """Giữ các Controller mà UI cần gọi; cũng tiện cho integration test."""

    menu_controller: MenuController
    table_controller: TableController
    order_controller: OrderController
    kitchen_controller: KitchenController
    payment_controller: PaymentController
    report_controller: ReportController


def _ensure_data_files(data_dir: Path) -> None:
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
    """Khởi tạo dependency. Có thể truyền thư mục tạm để test không đụng data thật."""
    chosen_data_dir = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    _ensure_data_files(chosen_data_dir)

    menu_repository = MenuRepository(JsonStore(chosen_data_dir / "menu.json"))
    table_repository = TableRepository(JsonStore(chosen_data_dir / "tables.json"))
    order_repository = OrderRepository(JsonStore(chosen_data_dir / "orders.json"))

    menu_service = MenuService(menu_repository)
    table_service = TableService(table_repository)
    kitchen_service = KitchenService(order_repository)
    order_service = OrderService(
        order_repository=order_repository,
        menu_service=menu_service,
        table_service=table_service,
        kitchen_service=kitchen_service,
    )
    payment_service = PaymentService(order_repository, table_service)
    report_service = ReportService(order_repository)

    return AppContext(
        menu_controller=MenuController(menu_service),
        table_controller=TableController(table_service),
        order_controller=OrderController(order_service),
        kitchen_controller=KitchenController(kitchen_service),
        payment_controller=PaymentController(payment_service),
        report_controller=ReportController(report_service),
    )
