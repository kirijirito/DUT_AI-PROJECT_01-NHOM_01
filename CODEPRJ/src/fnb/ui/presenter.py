"""Presenter: Cầu nối điều phối giữa Giao diện người dùng (UI) và Backend.

Thiết kế đơn giản, dễ hiểu theo nguyên lý OOP:
- Sử dụng Hash Map để tra cứu O(1)
- Điều phối 3 Hàng đợi (Queues): Đang đợi -> Đang nấu -> Chờ phục vụ
- Xử lý Giỏ hàng, Đặt đơn hàng và Thanh toán
"""

from datetime import datetime

from fnb.bootstrap import AppContext


def format_vnd(amount: int | float | None) -> str:
    """Định dạng số tiền sang chuẩn tiền Việt Nam (VNĐ)."""
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        return "0 ₫"
    return f"{int(amount):,}".replace(",", ".") + " ₫"


class FnbPresenter:
    def __init__(self, context: AppContext) -> None:
        self.context = context

    # =========================================================================
    # 1. QUẢN LÝ THỰC ĐƠN & GIỎ HÀNG (ORDER & CART)
    # =========================================================================
    def get_menu_choices(self) -> list[tuple[str, str]]:
        """Lấy danh sách món để đưa vào Dropdown."""
        items = self.context.menu_controller.list_menu()
        return [
            (f"{item['name']} - {format_vnd(item['price'])} ({item['id']})", item["id"])
            for item in items
            if item.get("is_available", True)
        ]

    def get_menu_table_data(self) -> list[list[str]]:
        """Lấy bảng danh mục thực đơn đầy đủ."""
        items = self.context.menu_controller.list_menu()
        return [
            [
                item["id"],
                item["name"],
                item.get("category", "Món ăn"),
                format_vnd(item["price"]),
                "Đang bán" if item.get("is_available", True) else "Tạm ngưng",
            ]
            for item in items
        ]

    def add_item_to_cart(
        self,
        menu_item_id: str,
        quantity: int,
        note: str,
        cart: list[dict] | None,
    ) -> tuple[list[dict], list[list[str]], str, str]:
        """Thêm món vào giỏ hàng."""
        cart = list(cart) if cart is not None else []
        if not menu_item_id:
            return (
                cart,
                self._format_cart_table(cart),
                self._cart_summary(cart),
                "⚠️ Vui lòng chọn món ăn!",
            )
        if not quantity or int(quantity) <= 0:
            return (
                cart,
                self._format_cart_table(cart),
                self._cart_summary(cart),
                "⚠️ Số lượng phải lớn hơn 0!",
            )

        # Tra cứu món qua Hash Map (O(1))
        menu_item = self.context.menu_controller.get_item(menu_item_id)
        if not menu_item:
            return (
                cart,
                self._format_cart_table(cart),
                self._cart_summary(cart),
                "❌ Không tìm thấy món này!",
            )

        # Nếu đã có trong giỏ với cùng ghi chú thì cộng dồn số lượng
        for item in cart:
            if item["menu_item_id"] == menu_item_id and item.get("note", "") == note.strip():
                item["quantity"] += int(quantity)
                item["line_total"] = item["quantity"] * item["unit_price"]
                break
        else:
            cart.append(
                {
                    "menu_item_id": menu_item_id,
                    "name": menu_item["name"],
                    "unit_price": menu_item["price"],
                    "quantity": int(quantity),
                    "note": note.strip(),
                    "line_total": int(quantity) * menu_item["price"],
                }
            )

        return (
            cart,
            self._format_cart_table(cart),
            self._cart_summary(cart),
            f"✅ Đã thêm '{menu_item['name']}' (x{quantity}) vào giỏ hàng.",
        )

    def adjust_cart_item(
        self, cart: list[dict] | None, item_idx: int | None, delta: int
    ) -> tuple[list[dict], list[list[str]], str, str]:
        """Tăng hoặc giảm số lượng món trong giỏ hàng."""
        cart = list(cart) if cart is not None else []
        if item_idx is None or item_idx < 0 or item_idx >= len(cart):
            return (
                cart,
                self._format_cart_table(cart),
                self._cart_summary(cart),
                "⚠️ Vui lòng chọn dòng món trong bảng giỏ hàng!",
            )

        cart[item_idx]["quantity"] += delta
        if cart[item_idx]["quantity"] <= 0:
            removed = cart.pop(item_idx)
            msg = f"🗑️ Đã xóa '{removed['name']}' khỏi giỏ hàng."
        else:
            cart[item_idx]["line_total"] = (
                cart[item_idx]["quantity"] * cart[item_idx]["unit_price"]
            )
            msg = (
                f"🔄 Đã cập nhật số lượng '{cart[item_idx]['name']}': "
                f"{cart[item_idx]['quantity']}."
            )

        return cart, self._format_cart_table(cart), self._cart_summary(cart), msg

    def clear_cart(self) -> tuple[list[dict], list[list[str]], str, str]:
        """Xóa trắng giỏ hàng."""
        return [], [], "### 🛒 Giỏ hàng trống", "ℹ️ Đã làm trống giỏ hàng."

    def submit_order(
        self, cart: list[dict] | None
    ) -> tuple[list[dict], list[list[str]], str, str]:
        """Tạo đơn hàng từ giỏ hàng. Món tự động vào Queue Đang Đợi."""
        if not cart:
            return [], [], "### 🛒 Giỏ hàng trống", "⚠️ Giỏ hàng đang trống, vui lòng chọn món!"

        lines = [
            {
                "menu_item_id": item["menu_item_id"],
                "quantity": item["quantity"],
                "note": item.get("note", ""),
            }
            for item in cart
        ]

        try:
            created_order = self.context.order_controller.create_order(lines)
            order_id = created_order["id"]
            total_items = sum(it["quantity"] for it in created_order["items"])
            msg = (
                f"🎉 Tạo đơn thành công! Mã đơn: **{order_id}** "
                f"({total_items} món). Đã chuyển vào **Queue Đang Đợi**."
            )
            return [], [], "### 🛒 Giỏ hàng trống", msg
        except Exception as ex:
            return (
                cart,
                self._format_cart_table(cart),
                self._cart_summary(cart),
                f"❌ Lỗi tạo đơn: {str(ex)}",
            )

    def _format_cart_table(self, cart: list[dict]) -> list[list[str]]:
        return [
            [
                f"{item['name']}" + (f" ({item['note']})" if item.get("note") else ""),
                str(item["quantity"]),
                format_vnd(item["unit_price"]),
                format_vnd(item["line_total"]),
            ]
            for item in cart
        ]

    def _cart_summary(self, cart: list[dict]) -> str:
        if not cart:
            return "### 🛒 Giỏ hàng trống"
        total = sum(item["line_total"] for item in cart)
        count = sum(item["quantity"] for item in cart)
        return f"### 🛒 Tổng số món: **{count}** | Tạm tính: **{format_vnd(total)}**"

    # =========================================================================
    # 2. QUẢN LÝ 3 HÀNG ĐỢI (QUEUES): ĐANG ĐỢI -> ĐANG NẤU -> CHỜ PHỤC VỤ
    # =========================================================================
    def get_waiting_queue_data(self) -> list[list[str]]:
        """Lấy dữ liệu bảng Queue 1: Đang Đợi."""
        queue = self.context.kitchen_controller.get_waiting_queue()
        return [
            [
                str(idx + 1),
                task["order_id"],
                task["name"],
                str(task["quantity"]),
                task.get("note", ""),
                task["order_item_id"],
            ]
            for idx, task in enumerate(queue)
        ]

    def get_cooking_queue_data(self) -> list[list[str]]:
        """Lấy dữ liệu bảng Queue 2: Đang Nấu."""
        queue = self.context.kitchen_controller.get_cooking_queue()
        return [
            [
                str(idx + 1),
                task["order_id"],
                task["name"],
                str(task["quantity"]),
                task.get("note", ""),
                task["order_item_id"],
            ]
            for idx, task in enumerate(queue)
        ]

    def get_serving_queue_data(self) -> list[list[str]]:
        """Lấy dữ liệu bảng Queue 3: Đang Chờ Phục Vụ."""
        queue = self.context.kitchen_controller.get_serving_queue()
        return [
            [
                str(idx + 1),
                task["order_id"],
                task["name"],
                str(task["quantity"]),
                task.get("note", ""),
                task["order_item_id"],
            ]
            for idx, task in enumerate(queue)
        ]

    def start_next_kitchen_item(self) -> tuple[str, list[list[str]], list[list[str]]]:
        """FIFO: Lấy món đầu tiên từ Queue Đang Đợi -> Chuyển sang Queue Đang Nấu."""
        try:
            task = self.context.kitchen_controller.start_next_item()
            msg = (
                f"🔥 Bếp bắt đầu nấu: **{task['name']}** (x{task['quantity']}) "
                f"của đơn {task['order_id']}."
            )
        except Exception as ex:
            msg = f"⚠️ {str(ex)}"
        return msg, self.get_waiting_queue_data(), self.get_cooking_queue_data()

    def finish_next_kitchen_item(self) -> tuple[str, list[list[str]], list[list[str]]]:
        """FIFO: Lấy món đầu tiên từ Queue Đang Nấu -> Chuyển sang Queue Chờ Phục Vụ."""
        try:
            task = self.context.kitchen_controller.finish_next_item()
            msg = (
                f"🍽️ Bếp đã nấu xong: **{task['name']}** (x{task['quantity']}) "
                f"của đơn {task['order_id']}. Đang chờ phục vụ!"
            )
        except Exception as ex:
            msg = f"⚠️ {str(ex)}"
        return msg, self.get_cooking_queue_data(), self.get_serving_queue_data()

    def serve_next_kitchen_item(self) -> tuple[str, list[list[str]]]:
        """FIFO: Lấy món đầu tiên từ Queue Chờ Phục Vụ -> Đã Phục Vụ khách."""
        try:
            task = self.context.kitchen_controller.serve_next_item()
            msg = (
                f"✔️ Đã phục vụ cho khách: **{task['name']}** (x{task['quantity']}) "
                f"của đơn {task['order_id']}!"
            )
        except Exception as ex:
            msg = f"⚠️ {str(ex)}"
        return msg, self.get_serving_queue_data()

    def advance_kitchen_item(
        self, order_id: str, item_id: str, action: str
    ) -> tuple[str, list[list[str]], list[list[str]], list[list[str]]]:
        """Cập nhật trạng thái món theo mã đơn và mã món cụ thể."""
        order_id = str(order_id).strip()
        item_id = str(item_id).strip()
        if not order_id or not item_id:
            return (
                "⚠️ Vui lòng nhập Mã đơn hàng và Mã món (Item ID)!",
                self.get_waiting_queue_data(),
                self.get_cooking_queue_data(),
                self.get_serving_queue_data(),
            )

        try:
            if action == "READY":
                self.context.kitchen_controller.mark_item_ready(order_id, item_id)
                msg = f"🍽️ Món {item_id} của đơn {order_id} đã nấu xong -> Chờ Phục Vụ."
            elif action == "SERVED":
                self.context.kitchen_controller.mark_item_served(order_id, item_id)
                msg = f"✔️ Món {item_id} của đơn {order_id} đã được phục vụ cho khách!"
            else:
                msg = "⚠️ Thao tác không hợp lệ."
        except Exception as ex:
            msg = f"❌ {str(ex)}"

        return (
            msg,
            self.get_waiting_queue_data(),
            self.get_cooking_queue_data(),
            self.get_serving_queue_data(),
        )

    # =========================================================================
    # 3. THANH TOÁN ĐƠN GIẢN DỄ HIỂU (PAYMENT)
    # =========================================================================
    def get_open_orders_choices(self) -> list[tuple[str, str]]:
        """Lấy danh sách các đơn hàng OPEN để thanh toán."""
        orders = self.context.order_controller.list_orders()
        open_orders = [o for o in orders if o["status"] == "OPEN"]
        choices = []
        for o in open_orders:
            items_count = sum(i["quantity"] for i in o["items"])
            subtotal = sum(
                i["unit_price"] * i["quantity"]
                for i in o["items"]
                if i["status"] != "CANCELLED"
            )
            choices.append((f"{o['id']} ({items_count} món - {format_vnd(subtotal)})", o["id"]))
        return choices

    def load_bill_for_payment(
        self, order_id: str, discount: int = 0
    ) -> tuple[list[list[str]], str, str]:
        """Xem trước chi tiết hóa đơn của đơn hàng."""
        if not order_id:
            return [], "### Vui lòng chọn hoặc nhập mã đơn hàng", ""

        try:
            bill = self.context.payment_controller.preview_bill(order_id, int(discount or 0))
            rows = [
                [
                    item["name"],
                    str(item["quantity"]),
                    format_vnd(item["unit_price"]),
                    format_vnd(item["line_total"]),
                    item["status"],
                ]
                for item in bill["items"]
            ]
            due_str = format_vnd(bill['total_due'])
            summary_md = (
                f"### 🧾 Chi tiết đơn: **{bill['order_id']}**\n"
                f"- Trạng thái đơn: **{bill['status']}**\n"
                f"- Tổng tiền món: **{format_vnd(bill['total_before_discount'])}**\n"
                f"- Giảm giá: **{format_vnd(bill['discount_amount'])}**\n"
                f"### 💳 TỔNG CẦN THANH TOÁN: "
                f"<span style='color:green; font-size: 1.3em;'>{due_str}</span>"
            )
            return rows, summary_md, ""
        except Exception as ex:
            return [], f"❌ Không thể tải hóa đơn: {str(ex)}", str(ex)

    def execute_checkout(
        self, order_id: str, payment_method: str = "CASH", discount: int = 0
    ) -> tuple[str, str, list[tuple[str, str]]]:
        """Thực hiện thanh toán đơn hàng."""
        if not order_id:
            return "⚠️ Vui lòng chọn đơn hàng cần thanh toán!", "", self.get_open_orders_choices()

        # Chuẩn hóa tên phương thức thanh toán
        clean_method = (
            "CASH"
            if "TIỀN MẶT" in payment_method.upper() or "CASH" in payment_method.upper()
            else "BANKING"
        )

        try:
            paid_order = self.context.payment_controller.checkout(
                order_id=order_id,
                payment_method=clean_method,
                discount_amount=int(discount or 0),
            )
            receipt = self._generate_receipt_text(paid_order)
            msg = (
                f"✅ Thanh toán thành công đơn hàng **{order_id}**! "
                f"Tổng tiền: {format_vnd(paid_order['total_paid'])}."
            )
            return msg, receipt, self.get_open_orders_choices()
        except Exception as ex:
            return f"❌ Thanh toán thất bại: {str(ex)}", "", self.get_open_orders_choices()

    def _generate_receipt_text(self, order: dict) -> str:
        """Tạo biên nhận / hóa đơn bán hàng định dạng văn bản dễ đọc."""
        paid_time = order.get("paid_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        lines = [
            "=" * 50,
            "               HÓA ĐƠN BÁN HÀNG",
            "=" * 50,
            f"Mã hóa đơn:       {order['id']}",
            f"Thời gian:        {paid_time}",
            f"Phương thức:      {order.get('payment_method', 'CASH')}",
            "-" * 50,
            f"{'Tên món':<22} {'SL':<4} {'Đơn giá':<11} {'Thành tiền':<11}",
            "-" * 50,
        ]
        for it in order.get("items", []):
            if it.get("status") == "CANCELLED":
                continue
            name = it["name"][:21]
            u_price = format_vnd(it["unit_price"])
            l_price = format_vnd(it["quantity"] * it["unit_price"])
            line_str = f"{name:<22} {it['quantity']:<4} {u_price:<11} {l_price:<11}"
            lines.append(line_str)
        lines.append("-" * 50)
        lines.append(
            f"Tổng tiền món:          {format_vnd(order.get('total_before_discount', 0)):>25}"
        )
        lines.append(
            f"Giảm giá:               {format_vnd(order.get('discount_amount', 0)):>25}"
        )
        lines.append("-" * 50)
        lines.append(
            f"TỔNG THANH TOÁN:        {format_vnd(order.get('total_paid', 0)):>25}"
        )
        lines.append("=" * 50)
        lines.append("          CẢM ƠN QUÝ KHÁCH - HẸN GẶP LẠI!")
        lines.append("=" * 50)
        return "\n".join(lines)

    # =========================================================================
    # 4. TRA CỨU HASH MAP O(1) & THỐNG KÊ DOANH THU
    # =========================================================================
    def lookup_order_hash(self, order_id: str) -> str:
        """Tra cứu đơn hàng tức thời bằng Hash Map O(1)."""
        order_id = str(order_id).strip()
        if not order_id:
            return "⚠️ Vui lòng nhập mã đơn hàng để tra cứu."
        try:
            order = self.context.order_controller.get_order(order_id)
            items_lines = []
            for it in order["items"]:
                total = format_vnd(it["unit_price"] * it["quantity"])
                items_lines.append(f"  - {it['name']} x{it['quantity']} ({it['status']}) - {total}")
            items_text = "\n".join(items_lines)
            total_disp = format_vnd(
                order.get("total_paid") or order.get("total_before_discount") or 0
            )
            return (
                f"### 🔎 Kết quả tra cứu Hash Map O(1) cho đơn: `{order['id']}`\n"
                f"- **Trạng thái:** `{order['status']}`\n"
                f"- **Thời gian tạo:** {order.get('created_at', 'N/A')}\n"
                f"- **Thời gian thanh toán:** {order.get('paid_at', 'Chưa thanh toán')}\n"
                f"- **Danh sách món ăn:**\n{items_text}\n"
                f"- **Tổng cộng:** {total_disp}"
            )
        except Exception:
            return f"❌ Không tìm thấy đơn hàng `{order_id}` trong bảng băm (Hash Table)!"

    def get_summary_report(self) -> tuple[str, list[list[str]]]:
        """Thống kê tổng số đơn và doanh thu."""
        orders = self.context.order_controller.list_orders()
        total_orders = len(orders)
        paid_orders = [o for o in orders if o["status"] == "PAID"]
        open_orders = [o for o in orders if o["status"] == "OPEN"]
        cancelled_orders = [o for o in orders if o["status"] == "CANCELLED"]

        total_revenue = sum(o.get("total_paid", 0) or 0 for o in paid_orders)

        summary_md = (
            f"### 📈 BÁO CÁO TỔNG QUAN\n"
            f"- **Tổng số đơn hàng đã tạo:** {total_orders} đơn\n"
            f"- **Đơn đang xử lý (OPEN):** {len(open_orders)} đơn\n"
            f"- **Đơn đã thanh toán (PAID):** {len(paid_orders)} đơn\n"
            f"- **Đơn đã hủy (CANCELLED):** {len(cancelled_orders)} đơn\n"
            f"- **TỔNG DOANH THU THỰC TẾ:** "
            f"<span style='color:green; font-size:1.4em; font-weight:bold;'>"
            f"{format_vnd(total_revenue)}</span>"
        )

        history_rows = [
            [
                o["id"],
                o.get("paid_at", o.get("created_at", "")),
                str(sum(i["quantity"] for i in o["items"])),
                format_vnd(o.get("total_paid", 0)),
                o.get("payment_method", "N/A"),
            ]
            for o in paid_orders
        ]
        return summary_md, history_rows
