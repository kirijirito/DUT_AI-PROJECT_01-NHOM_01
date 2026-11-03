"""Presenter: chuyển thao tác Gradio thành lời gọi Controller."""

import logging
from datetime import datetime

from fnb.bootstrap import AppContext
from fnb.exceptions import FNBError, StorageError


def format_vnd(value: int | float | None) -> str:
    if value is None:
        return "0 đ"
    try:
        return f"{int(value):,}".replace(",", ".") + " đ"
    except (TypeError, ValueError):
        return "0 đ"


def format_datetime(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return value


def error_message(exc: Exception) -> str:
    if isinstance(exc, StorageError):
        logging.exception("Lỗi lưu dữ liệu JSON trong UI")
        return "Không thể lưu dữ liệu. Hãy kiểm tra file JSON và quyền truy cập."
    if isinstance(exc, (FNBError, ValueError, TypeError, KeyError)):
        return str(exc)
    logging.exception("Lỗi chưa xử lý trong UI")
    return "Đã xảy ra lỗi. Vui lòng kiểm tra terminal để xem chi tiết."


def valid_quantity(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Số lượng phải là số nguyên dương.")
    if not float(value).is_integer() or value <= 0:
        raise ValueError("Số lượng phải là số nguyên dương.")
    return int(value)


class FnbPresenter:
    """Giữ trạng thái tạm của giỏ hàng và gọi Controller cho nghiệp vụ thật."""

    def __init__(self, context: AppContext) -> None:
        self.context = context

    def get_menu_table_data(self) -> list[list[str]]:
        items = self.context.menu_controller.list_menu(available_only=True)
        return [
            [item["id"], item["name"], item["category"], format_vnd(item["price"])]
            for item in items
        ]

    def get_menu_choices(self) -> list[tuple[str, str]]:
        items = self.context.menu_controller.list_menu(available_only=True)
        return [
            (f'{item["id"]} - {item["name"]} ({format_vnd(item["price"])})', item["id"])
            for item in items
        ]

    def add_item_to_cart(
        self,
        menu_item_id: str,
        quantity,
        note: str | None,
        current_cart: list[dict] | None,
    ) -> tuple[list[dict], list[list[str]], str, str]:
        cart = [dict(row) for row in (current_cart or [])]
        try:
            amount = valid_quantity(quantity)
            item = self.context.menu_controller.get_item(str(menu_item_id or ""))
            clean_note = (note or "").strip()
            matched = next(
                (
                    row
                    for row in cart
                    if row["menu_item_id"] == item["id"]
                    and row.get("note", "") == clean_note
                ),
                None,
            )
            if matched:
                matched["quantity"] += amount
            else:
                cart.append(
                    {
                        "menu_item_id": item["id"],
                        "name": item["name"],
                        "unit_price": item["price"],
                        "quantity": amount,
                        "note": clean_note,
                    }
                )
            rows, summary = self.format_cart_view(cart)
            return cart, rows, summary, f'Đã thêm **{item["name"]} × {amount}** vào giỏ.'
        except Exception as exc:
            rows, summary = self.format_cart_view(cart)
            return cart, rows, summary, f"⚠️ {error_message(exc)}"

    def adjust_cart_item(
        self, cart: list[dict] | None, selected_index: int | None, delta: int
    ) -> tuple[list[dict], list[list[str]], str, str]:
        current = [dict(row) for row in (cart or [])]
        if not isinstance(selected_index, int) or not 0 <= selected_index < len(current):
            rows, summary = self.format_cart_view(current)
            return current, rows, summary, "Hãy chọn một dòng trong giỏ trước."

        item = current[selected_index]
        item["quantity"] += delta
        if item["quantity"] <= 0:
            current.pop(selected_index)
            message = "Đã xóa món khỏi giỏ."
        else:
            message = f'Đã cập nhật {item["name"]}: {item["quantity"]} phần.'
        rows, summary = self.format_cart_view(current)
        return current, rows, summary, message

    def remove_selected_cart_item(
        self, cart: list[dict] | None, selected_index: int | None
    ) -> tuple[list[dict], list[list[str]], str, str]:
        current = [dict(row) for row in (cart or [])]
        if not isinstance(selected_index, int) or not 0 <= selected_index < len(current):
            rows, summary = self.format_cart_view(current)
            return current, rows, summary, "Hãy chọn một dòng trong giỏ để xóa."
        removed = current.pop(selected_index)
        rows, summary = self.format_cart_view(current)
        return current, rows, summary, f'Đã xóa {removed["name"]} khỏi giỏ.'

    def clear_cart(self) -> tuple[list[dict], list[list[str]], str, str]:
        return [], [], "Giỏ hàng đang trống.", "Đã xóa giỏ hàng tạm."

    def format_cart_view(self, cart: list[dict] | None) -> tuple[list[list[str]], str]:
        rows = []
        total_quantity = 0
        subtotal = 0
        for index, item in enumerate(cart or [], start=1):
            quantity = int(item["quantity"])
            unit_price = int(item["unit_price"])
            line_total = quantity * unit_price
            total_quantity += quantity
            subtotal += line_total
            rows.append(
                [
                    str(index),
                    item["menu_item_id"],
                    item["name"],
                    str(quantity),
                    format_vnd(line_total),
                    item.get("note", ""),
                ]
            )
        if not rows:
            return [], "Giỏ hàng đang trống."
        return rows, (
            f"**{len(rows)} dòng món · {total_quantity} phần · Tạm tính: "
            f"{format_vnd(subtotal)}**"
        )

    def submit_order(
        self, cart: list[dict] | None
    ) -> tuple[list[dict], list[list[str]], str, str, list[list[str]], list[tuple[str, str]]]:
        if not cart:
            rows, summary = self.format_cart_view(cart)
            return (
                cart or [], rows, summary, "Giỏ hàng đang trống.",
                self.get_queue_rows(), self.get_unpaid_order_choices(),
            )

        lines = [
            {
                "menu_item_id": item["menu_item_id"],
                "quantity": int(item["quantity"]),
                "note": item.get("note", ""),
            }
            for item in cart
        ]
        try:
            order = self.context.order_controller.create_order(lines)
            empty_rows, empty_summary = self.format_cart_view([])
            message = (
                f'✅ Đã tạo đơn **{order["id"]}**. '
                f'{len(order["items"])} dòng món đã được đưa vào cuối Queue FIFO.'
            )
            return (
                [], empty_rows, empty_summary, message,
                self.get_queue_rows(), self.get_unpaid_order_choices(),
            )
        except Exception as exc:
            rows, summary = self.format_cart_view(cart)
            return (
                cart, rows, summary, f"⚠️ {error_message(exc)}",
                self.get_queue_rows(), self.get_unpaid_order_choices(),
            )

    def get_queue_rows(self) -> list[list[str]]:
        tasks = self.context.kitchen_controller.get_queue()
        return [
            [
                str(index), task["order_id"], task["order_item_id"], task["name"],
                str(task["quantity"]), task.get("note", ""), "QUEUED",
            ]
            for index, task in enumerate(tasks, start=1)
        ]

    def get_served_rows(self) -> list[list[str]]:
        tasks = self.context.kitchen_controller.get_served_items()
        return [
            [task["order_id"], task["order_item_id"], task["name"], str(task["quantity"]), "SERVED"]
            for task in tasks
        ]

    def refresh_kitchen(self) -> tuple[list[list[str]], list[list[str]]]:
        return self.get_queue_rows(), self.get_served_rows()

    def serve_next_item(
        self,
    ) -> tuple[str, list[list[str]], list[list[str]], list[tuple[str, str]]]:
        try:
            task = self.context.kitchen_controller.serve_next_item()
            message = (
                f'✅ Đã phục vụ **{task["name"]} × {task["quantity"]}** '
                f'(đơn `{task["order_id"]}`). Đã lấy Node đầu tiên khỏi Queue.'
            )
        except Exception as exc:
            message = f"⚠️ {error_message(exc)}"
        return (
            message,
            self.get_queue_rows(),
            self.get_served_rows(),
            self.get_unpaid_order_choices(),
        )

    def get_unpaid_order_choices(self) -> list[tuple[str, str]]:
        orders = self.context.payment_controller.list_unpaid_orders()
        choices = []
        for order in orders:
            total = sum(int(item["quantity"]) for item in order.get("items", []))
            choices.append((f'{order["id"]} — {total} phần', order["id"]))
        return choices

    def load_bill_for_payment(
        self, order_id: str | None
    ) -> tuple[list[list[str]], str, str]:
        clean_id = str(order_id or "").strip()
        if not clean_id:
            return [], "Tổng thanh toán: 0 đ", "Chọn mã đơn để xem hóa đơn."
        try:
            bill = self.context.payment_controller.preview_bill(clean_id)
            rows = self._bill_rows(bill)
            total_text = f'**Tổng thanh toán: {format_vnd(bill["total_due"])}**'
            if bill["status"] == "PAID":
                message = "Đơn này đã được thanh toán. Đây là thông tin hóa đơn đã lưu."
            elif bill["can_pay"]:
                message = "Tất cả món đã SERVED. Đơn đủ điều kiện thanh toán."
            else:
                pending = sum(1 for item in bill["items"] if item["status"] != "SERVED")
                message = f"Còn món chưa SERVED ({pending} dòng món). Chưa thể thanh toán."
            return rows, total_text, message
        except Exception as exc:
            return [], "Tổng thanh toán: 0 đ", f"⚠️ {error_message(exc)}"

    def checkout_and_print(
        self, order_id: str | None
    ) -> tuple[str, str, list[tuple[str, str]], list[list[str]], str]:
        clean_id = str(order_id or "").strip()
        if not clean_id:
            return (
                "Hãy chọn đơn hàng cần thanh toán.", "",
                self.get_unpaid_order_choices(), [], "Tổng thanh toán: 0 đ",
            )

        try:
            paid_order = self.context.payment_controller.checkout(clean_id)
            bill = self.context.payment_controller.preview_bill(clean_id)
            receipt = self.build_receipt(bill)
            message = f'✅ Đã thanh toán đơn **{clean_id}**. Hóa đơn đã hiển thị bên dưới.'
            rows = self._bill_rows(bill)
            total = f'**Tổng đã thanh toán: {format_vnd(paid_order["total_paid"])}**'
            return message, receipt, self.get_unpaid_order_choices(), rows, total
        except Exception as exc:
            return (
                f"⚠️ {error_message(exc)}", "",
                self.get_unpaid_order_choices(), [], "Tổng thanh toán: 0 đ",
            )

    @staticmethod
    def _bill_rows(bill: dict) -> list[list[str]]:
        return [
            [
                str(index), item["name"], str(item["quantity"]),
                format_vnd(item["unit_price"]), format_vnd(item["line_total"]),
                item.get("note", ""), item["status"],
            ]
            for index, item in enumerate(bill.get("items", []), start=1)
        ]

    @staticmethod
    def build_receipt(bill: dict) -> str:
        lines = [
            "## HÓA ĐƠN F&B",
            f'**Mã đơn:** `{bill["order_id"]}`  ',
            f'**Thời gian tạo:** {format_datetime(bill.get("created_at"))}  ',
            f'**Thời gian thanh toán:** {format_datetime(bill.get("paid_at"))}',
            "",
            "| Món ăn | Số lượng | Đơn giá | Thành tiền | Ghi chú |",
            "|---|---:|---:|---:|---|",
        ]
        for item in bill.get("items", []):
            note = item.get("note", "").replace("|", "\\|")
            lines.append(
                f'| {item["name"]} | {item["quantity"]} | '
                f'{format_vnd(item["unit_price"])} | {format_vnd(item["line_total"])} | {note} |'
            )
        lines.extend(
            [
                "",
                f'### TỔNG THANH TOÁN: {format_vnd(bill.get("total_due", 0))}',
                "Cảm ơn quý khách!",
            ]
        )
        return "\n".join(lines)
