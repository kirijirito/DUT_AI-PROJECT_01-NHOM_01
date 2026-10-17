"""UI Presenter / Controller cho tầng giao diện F&B theo mô hình MVC/MVP.

Toàn bộ logic nghiệp vụ, xử lý dữ liệu và điều phối sự kiện giao diện
được tách biệt hoàn toàn khỏi mã nguồn dựng layout (View).
Không sử dụng mã HTML/CSS thuần túy.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime

from fnb.bootstrap import AppContext
from fnb.exceptions import FNBError, StorageError
from fnb.models import ItemStatus


def format_vnd(value: int | float | None) -> str:
    """Định dạng số nguyên VND theo chuẩn Việt Nam (ví dụ: 45.000 ₫)."""
    if value is None:
        return "0 ₫"
    try:
        val = int(value)
        return f"{val:,}".replace(",", ".") + " ₫"
    except (ValueError, TypeError):
        return "0 ₫"


def format_datetime(iso_str: str | None) -> str:
    """Chuyển chuỗi ISO 8601 sang định dạng ngày giờ dễ đọc (DD/MM/YYYY HH:MM:SS)."""
    if not iso_str:
        return "—"
    try:
        clean_str = iso_str.strip()
        dt = datetime.fromisoformat(clean_str)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(iso_str).replace("T", " ")[:19]


def error_message(exc: Exception) -> str:
    """Chuyển đổi ngoại lệ thành thông báo thân thiện với người dùng."""
    if isinstance(exc, StorageError):
        logging.exception("Không thể đọc/ghi dữ liệu trong callback Gradio.")
        return "Lỗi đọc/ghi dữ liệu JSON. Vui lòng kiểm tra quyền truy cập file."
    if isinstance(exc, (FNBError, ValueError, TypeError, KeyError)):
        return str(exc)
    logging.exception("Lỗi chưa xử lý trong giao diện Gradio.")
    return "Đã xảy ra lỗi ngoài dự kiến. Vui lòng kiểm tra nhật ký hệ thống."


def valid_quantity(quantity) -> int:
    """Kiểm tra số lượng nguyên dương lớn hơn 0."""
    if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
        raise ValueError("Số lượng phải là số nguyên dương lớn hơn 0.")
    if not float(quantity).is_integer() or quantity <= 0:
        raise ValueError("Số lượng phải là số nguyên dương lớn hơn 0.")
    return int(quantity)


@dataclass
class TableInfo:
    id: str
    name: str
    area: str
    order_id: str | None = None


class TableManager:
    """Quản lý trạng thái và liên kết đơn hàng cho sơ đồ bàn trong UI."""

    def __init__(self, table_count: int = 12) -> None:
        self._tables: dict[str, TableInfo] = {}
        for i in range(1, table_count + 1):
            t_id = f"T-{i:02d}"
            name = f"Bàn {i:02d}"
            area = "Tầng 1 (Trong nhà)" if i <= 6 else "Tầng 2 (Sân thượng)"
            self._tables[t_id] = TableInfo(id=t_id, name=name, area=area)

    def list_tables(self) -> list[TableInfo]:
        return list(self._tables.values())

    def get_table(self, table_id: str) -> TableInfo | None:
        return self._tables.get(table_id)

    def assign_order(self, table_id: str, order_id: str) -> None:
        if table_id in self._tables:
            self._tables[table_id].order_id = order_id

    def free_table(self, table_id: str) -> None:
        if table_id in self._tables:
            self._tables[table_id].order_id = None

    def find_table_by_order(self, order_id: str) -> TableInfo | None:
        for table in self._tables.values():
            if table.order_id == order_id:
                return table
        return None

    def free_table_by_order(self, order_id: str) -> None:
        table = self.find_table_by_order(order_id)
        if table:
            table.order_id = None

    def transfer_table(self, from_id: str, to_id: str) -> str:
        t_from = self.get_table(from_id)
        t_to = self.get_table(to_id)
        if not t_from or not t_to:
            raise ValueError("Không tìm thấy bàn yêu cầu.")
        if not t_from.order_id:
            raise ValueError(f"{t_from.name} hiện đang trống, không có đơn để chuyển.")
        if t_to.order_id:
            raise ValueError(
                f"{t_to.name} đang có khách ({t_to.order_id}). Dùng chức năng Gộp bàn."
            )
        order_id = t_from.order_id
        t_to.order_id = order_id
        t_from.order_id = None
        return f"Đã chuyển đơn {order_id} từ {t_from.name} sang {t_to.name}."

    def get_table_status(self, table: TableInfo, context: AppContext) -> str:
        """Xác định trạng thái bàn dựa vào đơn hàng đang liên kết."""
        if not table.order_id:
            return "🟢 Trống"
        try:
            order = context.order_controller.get_order(table.order_id)
        except Exception:
            table.order_id = None
            return "🟢 Trống"

        if order.get("status") != "OPEN":
            table.order_id = None
            return "🟢 Trống"

        items = order.get("items", [])
        if not items:
            return "🟡 Có khách (Chưa có món)"

        statuses = [it.get("status") for it in items if it.get("status") != "CANCELLED"]
        if not statuses:
            return "🟡 Có khách"

        if all(s == "SERVED" for s in statuses):
            return "🟠 Chờ thanh toán"
        if all(s in ("READY", "SERVED") for s in statuses):
            return "🔵 Đã lên đủ món"
        if any(s == "PREPARING" for s in statuses):
            return "🔥 Đang nấu món"
        return "🟡 Có khách (Chờ bếp)"


class FnbPresenter:
    """Presenter chính điều phối UI Logic và kết nối với Backend Controllers."""

    def __init__(self, context: AppContext) -> None:
        self.context = context
        self.table_manager = TableManager(table_count=12)

    # -------------------------------------------------------------------------
    # 1. LOGIC MÀN HÌNH ORDER (ĐẶT MÓN & GIỎ HÀNG)
    # -------------------------------------------------------------------------
    def get_menu_choices(self) -> list[tuple[str, str]]:
        items = self.context.menu_controller.list_menu(available_only=True)
        items = sorted(items, key=lambda it: it["name"])
        return [(f"{it['name']} — {format_vnd(it['price'])}", it["id"]) for it in items]

    def get_table_dropdown_choices(self) -> list[tuple[str, str]]:
        tables = self.table_manager.list_tables()
        return [(f"{t.name} ({t.area})", t.id) for t in tables]

    def add_item_to_cart(
        self,
        item_id: str,
        quantity,
        note: str,
        current_cart: list[dict] | None,
    ) -> tuple[list[dict], list[list[str]], str, str]:
        cart = [dict(row) for row in (current_cart or [])]
        try:
            amt = valid_quantity(quantity)
        except ValueError as exc:
            rows, summary = self.format_cart_view(cart)
            return cart, rows, summary, f"⚠️ {exc}"

        try:
            menu_item = self.context.menu_controller.get_item(item_id)
        except Exception as exc:
            rows, summary = self.format_cart_view(cart)
            return cart, rows, summary, f"⚠️ {error_message(exc)}"

        clean_note = (note or "").strip()
        matched = next(
            (
                line
                for line in cart
                if line["menu_item_id"] == item_id and line.get("note", "") == clean_note
            ),
            None,
        )
        if matched:
            matched["quantity"] += amt
        else:
            cart.append({
                "menu_item_id": item_id,
                "name": menu_item["name"],
                "price": menu_item["price"],
                "quantity": amt,
                "note": clean_note,
            })

        rows, summary = self.format_cart_view(cart)
        msg = f"✅ Đã thêm **{menu_item['name']} × {amt}** vào giỏ hàng."
        return cart, rows, summary, msg

    def adjust_cart_item(
        self, cart: list[dict] | None, selected_idx: int | None, delta: int
    ) -> tuple[list[dict], list[list[str]], str, str]:
        current_cart = [dict(row) for row in (cart or [])]
        if not isinstance(selected_idx, int) or not (0 <= selected_idx < len(current_cart)):
            rows, summary = self.format_cart_view(current_cart)
            return current_cart, rows, summary, "⚠️ Vui lòng chọn một dòng món trong giỏ trước."

        line = current_cart[selected_idx]
        new_qty = line["quantity"] + delta
        if new_qty <= 0:
            removed = current_cart.pop(selected_idx)
            msg = f"Đã xóa món **{removed['name']}** khỏi giỏ."
        else:
            line["quantity"] = new_qty
            msg = f"Đã cập nhật số lượng **{line['name']}** thành **{new_qty}**."

        rows, summary = self.format_cart_view(current_cart)
        return current_cart, rows, summary, f"ℹ️ {msg}"

    def remove_selected_cart_item(
        self, cart: list[dict] | None, selected_idx: int | None
    ) -> tuple[list[dict], list[list[str]], str, str]:
        current_cart = [dict(row) for row in (cart or [])]
        if not isinstance(selected_idx, int) or not (0 <= selected_idx < len(current_cart)):
            rows, summary = self.format_cart_view(current_cart)
            return current_cart, rows, summary, "⚠️ Vui lòng chọn một dòng món trong giỏ để xóa."
        removed = current_cart.pop(selected_idx)
        rows, summary = self.format_cart_view(current_cart)
        return current_cart, rows, summary, f"ℹ️ Đã xóa món **{removed['name']}** khỏi giỏ."

    def clear_cart(self) -> tuple[list[dict], list[list[str]], str, str]:
        return [], [], "### 🛒 Giỏ hàng: Đang trống (0 phần ăn)", "ℹ️ Đã xóa toàn bộ giỏ hàng."

    def format_cart_view(self, cart: list[dict] | None) -> tuple[list[list[str]], str]:
        rows: list[list[str]] = []
        total_qty = 0
        subtotal = 0
        for line in cart or []:
            qty = int(line["quantity"])
            price = int(line.get("price", 0))
            line_total = price * qty
            total_qty += qty
            subtotal += line_total
            note_str = f" ({line['note']})" if line.get("note") else ""
            rows.append([
                f"{line['name']}{note_str}",
                str(qty),
                format_vnd(price),
                format_vnd(line_total),
            ])
        if not rows:
            return [], "### 🛒 Giỏ hàng: Đang trống (0 phần ăn)"
        summary = (
            f"### 🛒 Tổng cộng: **{len(rows)}** món · **{total_qty}** phần "
            f"| Tạm tính: **{format_vnd(subtotal)}**"
        )
        return rows, summary

    def submit_order(
        self, cart: list[dict] | None, table_id: str | None
    ) -> tuple[list[dict], list[list[str]], str, str]:
        if not cart:
            rows, summary = self.format_cart_view(cart)
            return cart or [], rows, summary, "⚠️ Giỏ hàng đang trống! Hãy chọn món trước."

        lines = [
            {
                "menu_item_id": line["menu_item_id"],
                "quantity": int(line["quantity"]),
                "note": str(line.get("note", "")),
            }
            for line in cart
        ]

        try:
            created = self.context.order_controller.create_order(lines)
            order_id = created["id"]
            table_name = ""
            if table_id:
                t = self.table_manager.get_table(table_id)
                if t:
                    self.table_manager.assign_order(table_id, order_id)
                    table_name = f" cho **{t.name}**"

            rows, summary = self.format_cart_view([])
            msg = (
                f"✅ **Tạo đơn thành công! Mã đơn: `{order_id}`{table_name}.**\n\n"
                f"Toàn bộ {len(lines)} dòng món đã được chuyển vào Queue bếp FIFO."
            )
            return [], rows, summary, msg
        except Exception as exc:
            rows, summary = self.format_cart_view(cart)
            return cart, rows, summary, f"⚠️ {error_message(exc)}"

    # -------------------------------------------------------------------------
    # 2. LOGIC MÀN HÌNH PHỤC VỤ (SƠ ĐỒ BÀN & QUẢN LÝ TRẠNG THÁI & BẾP)
    # -------------------------------------------------------------------------
    def get_tables_table_data(self) -> list[list[str]]:
        rows = []
        for t in self.table_manager.list_tables():
            status_text = self.table_manager.get_table_status(t, self.context)
            order_id_str = t.order_id or "—"
            items_count_str = "0 món"
            subtotal_str = "0 ₫"

            if t.order_id:
                try:
                    order = self.context.order_controller.get_order(t.order_id)
                    items = [
                        it
                        for it in order.get("items", [])
                        if it.get("status") != "CANCELLED"
                    ]
                    items_count_str = f"{len(items)} món"
                    total = sum(
                        int(it.get("unit_price", 0)) * int(it.get("quantity", 0))
                        for it in items
                    )
                    subtotal_str = format_vnd(total)
                except Exception:
                    pass

            rows.append([
                t.name,
                t.area,
                status_text,
                order_id_str,
                items_count_str,
                subtotal_str,
            ])
        return rows

    def get_table_details_markdown(self, table_id: str | None) -> str:
        if not table_id:
            return "### 🪑 Hãy chọn một bàn trên sơ đồ để xem thông tin phục vụ."
        t = self.table_manager.get_table(table_id)
        if not t:
            return "### ⚠️ Không tìm thấy thông tin bàn."

        status_text = self.table_manager.get_table_status(t, self.context)
        md = [
            f"## 🪑 Thông tin {t.name} — {t.area}",
            f"- **Trạng thái:** {status_text}",
        ]

        if not t.order_id:
            md.append("- **Đơn hàng:** Chưa có khách ngồi.")
            return "\n\n".join(md)

        try:
            order = self.context.order_controller.get_order(t.order_id)
            items = order.get("items", [])
            md.append(f"- **Mã đơn hàng:** `{order['id']}`")
            md.append(f"- **Thời gian mở đơn:** {format_datetime(order.get('created_at'))}")
            md.append("### 📋 Danh sách món ăn tại bàn:")

            item_status_emojis = {
                "QUEUED": "⏳ Chờ nấu (QUEUED)",
                "PREPARING": "🔥 Đang nấu (PREPARING)",
                "READY": "🍽️ Sẵn sàng giao (READY)",
                "SERVED": "✔️ Đã phục vụ (SERVED)",
                "CANCELLED": "❌ Đã hủy (CANCELLED)",
            }

            subtotal = 0
            for it in items:
                st = it.get("status", "QUEUED")
                st_emoji = item_status_emojis.get(st, st)
                qty = it.get("quantity", 0)
                price = it.get("unit_price", 0)
                line_total = price * qty
                if st != "CANCELLED":
                    subtotal += line_total
                note = f" *(Ghi chú: {it['note']})*" if it.get("note") else ""
                md.append(
                    f"  1. **{it['name']}** × {qty} phần — {format_vnd(line_total)} "
                    f"[{st_emoji}]{note}"
                )

            md.append(f"**Tổng tiền tạm tính:** `{format_vnd(subtotal)}`")
        except Exception as exc:
            md.append(f"⚠️ Lỗi đọc đơn hàng: {error_message(exc)}")

        return "\n\n".join(md)

    def transfer_table(self, from_id: str, to_id: str) -> tuple[str, list[list[str]]]:
        try:
            msg = self.table_manager.transfer_table(from_id, to_id)
            return f"✅ {msg}", self.get_tables_table_data()
        except Exception as exc:
            return f"⚠️ {error_message(exc)}", self.get_tables_table_data()

    def merge_tables(self, from_id: str, to_id: str) -> tuple[str, list[list[str]]]:
        t_from = self.table_manager.get_table(from_id)
        t_to = self.table_manager.get_table(to_id)
        if not t_from or not t_to:
            return "⚠️ Bàn không hợp lệ.", self.get_tables_table_data()
        if from_id == to_id:
            return "⚠️ Bàn nguồn và bàn đích phải khác nhau.", self.get_tables_table_data()
        if not t_from.order_id:
            return f"⚠️ {t_from.name} đang trống, không có đơn để gộp.", self.get_tables_table_data()
        if not t_to.order_id:
            return self.transfer_table(from_id, to_id)

        try:
            order_from = self.context.order_controller.get_order(t_from.order_id)
            lines_to_add = [
                {
                    "menu_item_id": it["menu_item_id"],
                    "quantity": int(it["quantity"]),
                    "note": f"[Gộp từ {t_from.name}] {it.get('note', '')}".strip(),
                }
                for it in order_from.get("items", [])
                if it.get("status") != "CANCELLED"
            ]

            if lines_to_add:
                self.context.order_controller.add_items(t_to.order_id, lines_to_add)

            # Hủy đơn nguồn nếu có thể hoặc giải phóng bàn nguồn
            try:
                self.context.order_controller.cancel_order(
                    t_from.order_id, f"Gộp vào {t_to.name}"
                )
            except Exception:
                pass

            t_from.order_id = None
            msg = f"✅ Đã gộp món từ {t_from.name} sang {t_to.name} (Đơn {t_to.order_id})."
            return msg, self.get_tables_table_data()
        except Exception as exc:
            return f"⚠️ {error_message(exc)}", self.get_tables_table_data()

    def mark_all_served_for_table(self, table_id: str) -> tuple[str, str, list[list[str]]]:
        t = self.table_manager.get_table(table_id)
        if not t or not t.order_id:
            return (
                "⚠️ Bàn này chưa có đơn hàng.",
                self.get_table_details_markdown(table_id),
                self.get_tables_table_data(),
            )
        try:
            order_service = self.context.order_controller._order_service
            kitchen_service = self.context.kitchen_controller._kitchen_service

            order = order_service.get_order(t.order_id)
            updated_count = 0
            for it in order.items:
                if it.status != ItemStatus.CANCELLED and it.status != ItemStatus.SERVED:
                    it.status = ItemStatus.SERVED
                    updated_count += 1

            if updated_count > 0:
                order_service._order_repository.upsert(order)
                kitchen_service.remove_order_from_queue(order.id)

            msg = f"✅ Đã chuyển trạng thái phục vụ cho {updated_count} món tại {t.name}."
            return msg, self.get_table_details_markdown(table_id), self.get_tables_table_data()
        except Exception as exc:
            return (
                f"⚠️ {error_message(exc)}",
                self.get_table_details_markdown(table_id),
                self.get_tables_table_data(),
            )

    # -------------------------------------------------------------------------
    # 2B. LOGIC BẾP / KDS (QUEUE FIFO)
    # -------------------------------------------------------------------------
    def get_kitchen_queue_data(self) -> list[list[str]]:
        tasks = self.context.kitchen_controller.get_queue()
        rows = []
        for task in tasks:
            t = self.table_manager.find_table_by_order(task.get("order_id", ""))
            table_str = t.name if t else "—"
            rows.append([
                f"#{task.get('queue_seq', '')}",
                str(task.get("order_id", "")),
                table_str,
                str(task.get("name", "")),
                f"{task.get('quantity', '')} phần",
                str(task.get("status", "")),
                str(task.get("note", "")) or "—",
                str(task.get("order_item_id", "")),
            ])
        return rows

    def start_next_kitchen_item(self) -> tuple[str, list[list[str]]]:
        try:
            item = self.context.kitchen_controller.start_next_item()
            t = self.table_manager.find_table_by_order(item["order_id"])
            table_info = f" ({t.name})" if t else ""
            msg = (
                f"🔔 Bếp đang chế biến: **{item['name']} × {item['quantity']}** "
                f"cho đơn `{item['order_id']}`{table_info}."
            )
            return msg, self.get_kitchen_queue_data()
        except Exception as exc:
            return f"⚠️ {error_message(exc)}", self.get_kitchen_queue_data()

    def advance_kitchen_item(
        self, order_id: str, item_id: str, target: str
    ) -> tuple[str, list[list[str]]]:
        clean_oid = str(order_id or "").strip()
        clean_iid = str(item_id or "").strip()
        if not clean_oid or not clean_iid:
            return "⚠️ Vui lòng chọn món cần chuyển trạng thái.", self.get_kitchen_queue_data()
        try:
            if target == "READY":
                res = self.context.kitchen_controller.mark_item_ready(clean_oid, clean_iid)
                msg = f"✅ Bếp đã nấu xong: **{res['name']}** (READY)."
            elif target == "SERVED":
                res = self.context.kitchen_controller.mark_item_served(clean_oid, clean_iid)
                msg = f"🍽️ Đã phục vụ: **{res['name']}** (SERVED)."
            else:
                msg = "Trạng thái không hợp lệ."
            return msg, self.get_kitchen_queue_data()
        except Exception as exc:
            return f"⚠️ {error_message(exc)}", self.get_kitchen_queue_data()

    def select_kitchen_item_by_row(self, row_idx: int) -> tuple[str, str]:
        """Lấy Order ID và Item ID khi người dùng click vào dòng trong hàng đợi bếp."""
        tasks = self.context.kitchen_controller.get_queue()
        if 0 <= row_idx < len(tasks):
            return str(tasks[row_idx].get("order_id", "")), str(
                tasks[row_idx].get("order_item_id", "")
            )
        return "", ""

    # -------------------------------------------------------------------------
    # 3. LOGIC MÀN HÌNH THANH TOÁN (BILLING & CASHIER)
    # -------------------------------------------------------------------------
    def get_unpaid_order_choices(self) -> list[tuple[str, str]]:
        orders = self.context.order_controller.list_orders()
        choices = []
        for o in orders:
            if o.get("status") == "OPEN":
                t = self.table_manager.find_table_by_order(o["id"])
                t_str = f" [{t.name}]" if t else ""
                choices.append((f"{o['id']}{t_str} ({len(o.get('items', []))} món)", o["id"]))
        return choices

    def load_bill_for_payment(
        self, order_id: str
    ) -> tuple[list[list[str]], str, str]:
        clean_oid = str(order_id or "").strip()
        if not clean_oid:
            return [], "## 💵 TỔNG CẦN THANH TOÁN: **0 ₫**", "⚠️ Vui lòng chọn mã đơn hàng."

        try:
            bill = self.context.payment_controller.preview_bill(clean_oid, 0)
            items = bill.get("items", [])
            rows = []
            for it in items:
                rows.append([
                    it["name"],
                    str(it["quantity"]),
                    format_vnd(it["unit_price"]),
                    format_vnd(it["line_total"]),
                    it["status"],
                ])

            total_due = bill.get("total_due", bill.get("total_before_discount", 0))
            due_md = f"## 💵 TỔNG CẦN THANH TOÁN: **{format_vnd(total_due)}**"
            msg = f"Đã nạp hóa đơn cho đơn `{clean_oid}`. Sẵn sàng thanh toán."
            return rows, due_md, msg
        except Exception as exc:
            return [], "## 💵 TỔNG CẦN THANH TOÁN: **0 ₫**", f"⚠️ {error_message(exc)}"

    def execute_checkout(
        self,
        order_id: str,
        payment_method: str,
    ) -> tuple[str, str, list[tuple[str, str]]]:
        clean_oid = str(order_id or "").strip()
        if not clean_oid:
            return "⚠️ Vui lòng chọn mã đơn để thanh toán.", "", self.get_unpaid_order_choices()

        try:
            method_key = "CASH"
            if "TRANSFER" in payment_method:
                method_key = "TRANSFER"
            elif "CARD" in payment_method:
                method_key = "CARD"

            receipt = self.context.payment_controller.checkout(
                clean_oid, payment_method=method_key, discount_amount=0
            )

            # Giải phóng bàn nếu có
            t = self.table_manager.find_table_by_order(clean_oid)
            table_info = f" ({t.name})" if t else ""
            if t:
                self.table_manager.free_table_by_order(clean_oid)

            paid_total = receipt.get("total_paid", 0)
            receipt_preview = self.build_markdown_receipt(receipt)
            msg = (
                f"🎉 **Thanh toán thành công đơn `{clean_oid}`{table_info}!**\n"
                f"Tổng tiền đã thu: **{format_vnd(paid_total)}** qua phương thức "
                f"**{payment_method}**.\n"
                f"Bàn đã được giải phóng về trạng thái trống."
            )
            return msg, receipt_preview, self.get_unpaid_order_choices()
        except Exception as exc:
            return f"⚠️ {error_message(exc)}", "", self.get_unpaid_order_choices()

    # -------------------------------------------------------------------------
    # 4. LOGIC MÀN HÌNH HÓA ĐƠN & BÁO CÁO (INVOICE HISTORY & PREVIEW)
    # -------------------------------------------------------------------------
    def get_invoice_history(self, date_str: str | None) -> tuple[list[list[str]], str]:
        clean_date = str(date_str or "").strip() or date.today().isoformat()
        try:
            summary = self.context.report_controller.daily_summary(clean_date)
            order_ids = summary.get("order_ids", [])
            rows = []
            for oid in order_ids:
                try:
                    ord_data = self.context.order_controller.get_order(oid)
                    t = self.table_manager.find_table_by_order(oid)
                    table_name = t.name if t else "Mang về / Bàn —"
                    rows.append([
                        ord_data["id"],
                        table_name,
                        f"{len(ord_data.get('items', []))} món",
                        format_vnd(ord_data.get("total_paid", 0)),
                        str(ord_data.get("payment_method", "CASH")),
                        format_datetime(ord_data.get("paid_at")),
                    ])
                except Exception:
                    rows.append([oid, "—", "—", "—", "—", "—"])

            rev = summary.get("revenue_vnd", 0)
            cnt = summary.get("paid_order_count", 0)
            aov = int(rev / cnt) if cnt > 0 else 0
            stats_md = (
                f"### 📊 Báo cáo ngày **{clean_date}**\n"
                f"- **Tổng doanh thu:** `{format_vnd(rev)}`\n"
                f"- **Số hóa đơn đã thanh toán:** `{cnt}` đơn\n"
                f"- **Giá trị trung bình / đơn:** `{format_vnd(aov)}`"
            )
            return rows, stats_md
        except Exception as exc:
            return [], f"⚠️ {error_message(exc)}"

    def get_invoice_preview(self, order_id: str) -> str:
        """Lấy thông tin và tạo định dạng xem trước hóa đơn theo mã đơn."""
        clean_oid = str(order_id or "").strip()
        if not clean_oid:
            return "*(Chưa nhập hoặc chọn mã đơn hàng để xem)*"
        try:
            order = self.context.order_controller.get_order(clean_oid)
            return self.build_markdown_receipt(order)
        except Exception as exc:
            return f"⚠️ Lỗi đọc hóa đơn: {error_message(exc)}"

    def select_invoice_by_index(self, date_str: str, row_idx: int) -> tuple[str, str]:
        """Lấy Order ID và nội dung hóa đơn khi người dùng chọn một dòng trong bảng lịch sử."""
        clean_date = str(date_str or "").strip() or date.today().isoformat()
        try:
            summary = self.context.report_controller.daily_summary(clean_date)
            oids = summary.get("order_ids", [])
            if 0 <= row_idx < len(oids):
                oid = oids[row_idx]
                return oid, self.get_invoice_preview(oid)
        except Exception:
            pass
        return "", "*(Không tìm thấy hóa đơn)*"

    def build_markdown_receipt(self, order_or_bill: dict, cash_given: int = 0) -> str:
        """Tạo định dạng xem trước hóa đơn dạng văn bản/Markdown thuần túy."""
        if not order_or_bill:
            return "*(Chưa chọn hóa đơn để xem trước)*"

        order_id = order_or_bill.get("order_id", order_or_bill.get("id", "ORD-—"))
        paid_at = format_datetime(order_or_bill.get("paid_at"))
        if paid_at == "—":
            paid_at = format_datetime(datetime.now().isoformat())

        method = order_or_bill.get("payment_method") or "TIỀN MẶT"
        t = self.table_manager.find_table_by_order(order_id)
        table_str = t.name if t else "Bàn phục vụ"

        items = order_or_bill.get("items", [])
        subtotal = int(order_or_bill.get("total_before_discount", 0) or 0)
        discount = int(order_or_bill.get("discount_amount", 0) or 0)
        raw_due = order_or_bill.get("total_due") or order_or_bill.get("total_paid")
        total_due = int(raw_due if raw_due is not None else (subtotal - discount))

        lines = [
            "```text",
            "============================================================",
            "                   🍽️ NHÀ HÀNG F&B STARTER                   ",
            "                 HÓA ĐƠN BÁN HÀNG DỊCH VỤ                   ",
            "============================================================",
            f"Mã đơn:     {order_id:<20} Khu vực: {table_str}",
            f"Thời gian:  {paid_at:<20} Phương thức: {method}",
            "------------------------------------------------------------",
            f"{'Tên món':<28} {'SL':<5} {'Đơn giá':<12} {'Thành tiền':<12}",
            "------------------------------------------------------------",
        ]

        for it in items:
            name = str(it.get("name", ""))[:26]
            qty = str(it.get("quantity", 0))
            price = format_vnd(it.get("unit_price", 0))
            total = format_vnd(it.get("line_total", 0))
            lines.append(f"{name:<28} {qty:<5} {price:<12} {total:<12}")

        lines.append("------------------------------------------------------------")
        if discount > 0:
            lines.extend([
                f"{'Tạm tính:':<46} {format_vnd(subtotal):>13}",
                f"{'Giảm giá / Chiết khấu:':<46} -{format_vnd(discount):>12}",
                "============================================================",
            ])
        lines.extend([
            f"{'TỔNG TIỀN THANH TOÁN:':<46} {format_vnd(total_due):>13}",
        ])

        if cash_given > 0:
            change = max(0, cash_given - total_due)
            lines.extend([
                f"{'Tiền khách đưa:':<46} {format_vnd(cash_given):>13}",
                f"{'Tiền thừa trả khách:':<46} {format_vnd(change):>13}",
            ])

        lines.extend([
            "============================================================",
            "           CẢM ƠN QUÝ KHÁCH VÀ HẸN GẶP LẠI!                 ",
            "============================================================",
            "```",
        ])
        return "\n".join(lines)
