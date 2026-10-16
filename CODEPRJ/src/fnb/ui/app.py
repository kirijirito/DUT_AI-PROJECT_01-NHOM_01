"""Giao diện Gradio gọn nhẹ; toàn bộ quy tắc nghiệp vụ vẫn nằm ở Backend."""

import logging
import json

import gradio as gr

from fnb.bootstrap import AppContext
from fnb.exceptions import FNBError, StorageError


CSS = """
/* Giới hạn độ rộng trang và giảm cỡ tiêu đề mặc định của Markdown. */
.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    padding: 16px 22px 28px !important;
}
#app-title h1, #app-title h2, #app-title h3 {
    font-size: 1.75rem !important;
    line-height: 1.2 !important;
    margin: 0 0 4px 0 !important;
    font-weight: 700 !important;
}
#app-subtitle p {
    font-size: .95rem !important;
    margin-top: 0 !important;
    margin-bottom: 12px !important;
}
.menu-tile button {
    min-height: 68px !important;
    height: auto !important;
    padding: 10px 8px !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    line-height: 1.35 !important;
    font-size: .92rem !important;
    border-radius: 10px !important;
}
.menu-tile button span {
    white-space: pre-line !important;
}
.section-heading h2, .section-heading h3 {
    font-size: 1.15rem !important;
    margin-top: 4px !important;
    margin-bottom: 8px !important;
}
.small-help p {
    font-size: .85rem !important;
}
.primary-action button {
    min-height: 44px !important;
    font-weight: 650 !important;
}
@media (max-width: 760px) {
    .gradio-container { padding: 10px !important; }
    #app-title h1, #app-title h2, #app-title h3 { font-size: 1.45rem !important; }
    .menu-tile button { min-height: 60px !important; font-size: .86rem !important; }
}
"""


def _error_message(exc: Exception) -> str:
    if isinstance(exc, StorageError):
        logging.exception("Không thể đọc/ghi dữ liệu trong callback Gradio.")
        return "Không thể đọc/ghi dữ liệu. Hãy nhờ nhóm kiểm tra file JSON."
    if isinstance(exc, (FNBError, ValueError, TypeError, KeyError)):
        return str(exc)
    logging.exception("Lỗi chưa xử lý trong callback Gradio.")
    return "Có lỗi chưa xử lý. Hãy kiểm tra terminal để chẩn đoán."


def _call_message(callback, *args) -> str:
    try:
        callback(*args)
        return "✅ Thao tác thành công."
    except Exception as exc:  # UI chuyển lỗi thành thông báo dễ hiểu.
        return f"⚠️ {_error_message(exc)}"


def _format_vnd(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".") + " ₫"


def _valid_quantity(quantity) -> int:
    if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
        raise ValueError("Số lượng phải là số nguyên dương.")
    if not float(quantity).is_integer() or quantity <= 0:
        raise ValueError("Số lượng phải là số nguyên dương.")
    return int(quantity)


def _cart_view(cart: list[dict]) -> tuple[list[list[str]], str]:
    """Chỉ trình bày tên món và số lượng; tiền cuối do Backend tính."""
    rows: list[list[str]] = []
    quantity_total = 0
    for line in cart or []:
        quantity = int(line["quantity"])
        quantity_total += quantity
        name = str(line["name"])
        note = str(line.get("note", "")).strip()
        if note:
            name = f"{name} — {note}"
        rows.append([name, str(quantity)])
    if not rows:
        return [], "**Giỏ hàng đang trống**"
    return rows, f"**{len(rows)} dòng món · {quantity_total} phần ăn**"


def _add_to_cart(
    item: dict,
    quantity,
    note: str,
    cart: list[dict] | None,
) -> tuple[list[dict], list[list[str]], str, str]:
    current_cart = [dict(line) for line in (cart or [])]
    try:
        amount = _valid_quantity(quantity)
    except ValueError as exc:
        rows, summary = _cart_view(current_cart)
        return current_cart, rows, summary, f"⚠️ {exc}"

    clean_note = (note or "").strip()
    matching_line = next(
        (
            line
            for line in current_cart
            if line["menu_item_id"] == item["id"] and line.get("note", "") == clean_note
        ),
        None,
    )
    if matching_line:
        matching_line["quantity"] += amount
    else:
        current_cart.append(
            {
                "menu_item_id": item["id"],
                "name": item["name"],
                "quantity": amount,
                "note": clean_note,
            }
        )
    rows, summary = _cart_view(current_cart)
    return current_cart, rows, summary, f"✅ Đã thêm **{item['name']} × {amount}** vào giỏ."


def _orders_table(orders: list[dict]) -> list[list[str]]:
    return [
        [
            str(order.get("id", "")),
            str(order.get("status", "")),
            str(len(order.get("items", []))),
            _format_vnd(
                order.get("total_paid")
                if order.get("status") == "PAID" and order.get("total_paid") is not None
                else sum(
                    int(item.get("unit_price", 0)) * int(item.get("quantity", 0))
                    for item in order.get("items", [])
                    if item.get("status") != "CANCELLED"
                )
            ),
            str(order.get("created_at", ""))[:16].replace("T", " "),
        ]
        for order in orders
    ]


def _queue_table(tasks: list[dict]) -> list[list[str]]:
    """Hàng chờ FIFO: chỉ những thông tin nhân viên bếp cần nhìn thấy."""
    return [
        [
            str(index),
            str(task.get("name", "")),
            str(task.get("quantity", "")),
            str(task.get("order_id", "")),
            str(task.get("note", "")),
        ]
        for index, task in enumerate(tasks, start=1)
    ]


def _kitchen_choices(orders: list[dict]) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Tạo danh sách món đang làm/đã xong từ dữ liệu Controller trả về.

    Tên món hiển thị cho nhân viên; mã đơn và mã dòng món được giữ trong
    giá trị lựa chọn để gửi lại Controller, không yêu cầu gõ bằng tay.
    """
    preparing = []
    ready = []

    for order in orders:
        if order.get("status") == "CANCELLED":
            continue
        order_id = str(order.get("id", ""))
        if not order_id:
            continue

        for position, item in enumerate(order.get("items", []), start=1):
            status = item.get("status")
            if status not in ("PREPARING", "READY"):
                continue

            item_id = str(item.get("id") or item.get("order_item_id") or "")
            if not item_id:
                continue
            name = str(item.get("name") or item.get("item_name") or "Món chưa đặt tên")
            quantity = item.get("quantity", 1)
            note = str(item.get("note", "")).strip()
            label = f"{name} × {quantity} — đơn {order_id} (món {position})"
            if note:
                label += f" — {note}"

            # json.dumps biến cặp mã thành một chuỗi mà Dropdown lưu được.
            # Khi bấm nút, json.loads khôi phục đúng hai mã này.
            selection_key = json.dumps([order_id, item_id], ensure_ascii=False)
            if status == "PREPARING":
                preparing.append((label, selection_key))
            else:
                ready.append((label, selection_key))

    return preparing, ready


def _safe_json(callback, *args):
    try:
        return callback(*args)
    except Exception as exc:
        return {"error": _error_message(exc)}


def create_app(context: AppContext) -> gr.Blocks:
    """Tạo UI nhỏ gọn cho menu/đơn/bếp/thanh toán; không có báo cáo ngày."""
    menu_items = context.menu_controller.list_menu(available_only=True)
    menu_items = sorted(menu_items, key=lambda item: (item.get("category", "Khác"), item["name"]))
    menu_choices = [
        (f"{item['name']} · {_format_vnd(item['price'])}", item["id"])
        for item in menu_items
    ]

    menu_button_bindings = []

    with gr.Blocks(title="Hệ thống quản lý đơn hàng F&B") as demo:
        gr.Markdown("# Hệ thống quản lý đơn hàng F&B", elem_id="app-title")
        gr.Markdown(
            "Chọn món bằng cách bấm vào nút tên món và giá. Sau đó tạo đơn để chuyển món vào Queue bếp.",
            elem_id="app-subtitle",
        )

        with gr.Tabs():
            with gr.Tab("🍔 Đặt món", id="order"):
                cart_state = gr.State([])
                selected_cart_row = gr.State(None)
                with gr.Row(equal_height=False):
                    with gr.Column(scale=3, min_width=360):
                        with gr.Row():
                            quantity = gr.Number(
                                label="Số lượng thêm mỗi lần bấm",
                                value=1,
                                precision=0,
                                minimum=1,
                                scale=1,
                            )
                            note = gr.Textbox(
                                label="Ghi chú món (không bắt buộc)",
                                placeholder="Ví dụ: không hành",
                                scale=2,
                            )

                        if not menu_items:
                            gr.Markdown("⚠️ Chưa có món nào được nạp từ thực đơn.")
                        else:
                            categories = list(dict.fromkeys(item.get("category", "Khác") for item in menu_items))
                            for category in categories:
                                category_items = [item for item in menu_items if item.get("category", "Khác") == category]
                                gr.Markdown(f"### {category}", elem_classes=["section-heading"])
                                for start in range(0, len(category_items), 4):
                                    with gr.Row():
                                        for item in category_items[start : start + 4]:
                                            button = gr.Button(
                                                f"{item['name']}\n{_format_vnd(item['price'])}",
                                                variant="secondary",
                                                elem_classes=["menu-tile"],
                                                scale=1,
                                            )

                                            menu_button_bindings.append((button, item, quantity, note, cart_state))

                    with gr.Column(scale=2, min_width=320):
                        gr.Markdown("### Giỏ hàng", elem_classes=["section-heading"])
                        cart_table = gr.Dataframe(
                            headers=["Tên món", "Số lượng"],
                            datatype=["str", "str"],
                            value=[],
                            interactive=False,
                            wrap=True,
                            label="Các món đã chọn",
                        )
                        cart_summary = gr.Markdown("**Giỏ hàng đang trống**")
                        cart_message = gr.Markdown(
                            "Bấm vào một món bên trái để thêm vào giỏ.",
                            elem_classes=["small-help"],
                        )
                        with gr.Row():
                            remove_selected_button = gr.Button("Xóa món chọn", variant="secondary")
                            clear_cart = gr.Button("Xóa giỏ", variant="secondary")
                        create_order_button = gr.Button(
                            "TẠO ĐƠN", variant="primary", elem_classes=["primary-action"]
                        )
                        created_order_id = gr.Textbox(
                            label="Mã đơn vừa tạo",
                            interactive=False,
                            placeholder="Mã đơn sẽ xuất hiện ở đây",
                        )
                        created_order_result = gr.JSON(label="Kết quả", open=False, visible=False)

                # Đăng ký sự kiện sau khi các component giỏ hàng đã được tạo.
                for menu_button, selected_item, quantity_input, note_input, state_input in menu_button_bindings:
                    def add_item(q, item_note, cart, item=selected_item):
                        new_cart, rows, summary, message = _add_to_cart(item, q, item_note, cart)
                        return new_cart, rows, summary, message, None

                    menu_button.click(
                        fn=add_item,
                        inputs=[quantity_input, note_input, state_input],
                        outputs=[cart_state, cart_table, cart_summary, cart_message, selected_cart_row],
                    )

                def select_cart_row(cart, evt: gr.SelectData):
                    index = evt.index[0] if isinstance(evt.index, (tuple, list)) else evt.index
                    if isinstance(index, int) and 0 <= index < len(cart or []):
                        name = cart[index].get("name", "món")
                        return index, f"Đã chọn **{name}**. Bấm 'Xóa món chọn' nếu muốn bỏ món này."
                    return None, "Không xác định được dòng món đang chọn."

                cart_table.select(
                    fn=select_cart_row,
                    inputs=[cart_state],
                    outputs=[selected_cart_row, cart_message],
                )

                def remove_selected_action(cart, selected_index):
                    current_cart = [dict(line) for line in (cart or [])]
                    if not isinstance(selected_index, int) or not 0 <= selected_index < len(current_cart):
                        rows, summary = _cart_view(current_cart)
                        return current_cart, rows, summary, "Hãy bấm vào một dòng trong giỏ trước khi xóa.", None
                    removed = current_cart.pop(selected_index)
                    rows, summary = _cart_view(current_cart)
                    return current_cart, rows, summary, f"Đã xóa **{removed['name']}** khỏi giỏ.", None

                remove_selected_button.click(
                    fn=remove_selected_action,
                    inputs=[cart_state, selected_cart_row],
                    outputs=[cart_state, cart_table, cart_summary, cart_message, selected_cart_row],
                )

                def clear_cart_action():
                    return [], [], "**Giỏ hàng đang trống**", "Đã xóa toàn bộ giỏ hàng.", None

                clear_cart.click(
                    fn=clear_cart_action,
                    outputs=[cart_state, cart_table, cart_summary, cart_message, selected_cart_row],
                )

                def submit_new_order(cart):
                    if not cart:
                        rows, summary = _cart_view(cart)
                        return cart, rows, summary, "⚠️ Vui lòng chọn ít nhất một món.", "", None, None
                    lines = [
                        {
                            "menu_item_id": line["menu_item_id"],
                            "quantity": int(line["quantity"]),
                            "note": str(line.get("note", "")),
                        }
                        for line in cart
                    ]
                    try:
                        created = context.order_controller.create_order(lines)
                    except Exception as exc:
                        rows, summary = _cart_view(cart)
                        return cart, rows, summary, f"⚠️ {_error_message(exc)}", "", {"error": str(exc)}, None
                    message = f"✅ Đã tạo đơn **{created['id']}**. Các món đã được đưa vào Queue bếp."
                    return [], [], "**Giỏ hàng đang trống**", message, created["id"], created, None

                create_order_button.click(
                    fn=submit_new_order,
                    inputs=[cart_state],
                    outputs=[cart_state, cart_table, cart_summary, cart_message, created_order_id, created_order_result, selected_cart_row],
                )

            with gr.Tab("🍳 Bếp / Queue", id="kitchen") as kitchen_tab:
                gr.Markdown("### Quản lý chế biến món", elem_classes=["section-heading"])
                gr.Markdown("Nhận món theo **FIFO**, sau đó chọn món để xác nhận đã làm xong hoặc đã phục vụ.")

                with gr.Row():
                    refresh_queue = gr.Button("↻ Làm mới", variant="secondary")
                    start_next = gr.Button("▶ Nhận món tiếp theo", variant="primary")

                kitchen_counts = gr.Markdown("Đang tải thông tin bếp...")
                queue_table = gr.Dataframe(
                    headers=["STT", "Tên món", "SL", "Mã đơn", "Ghi chú"],
                    datatype=["str"] * 5,
                    value=[],
                    interactive=False,
                    wrap=True,
                    label="Hàng chờ FIFO",
                )

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🔥 Đang chế biến", elem_classes=["section-heading"])
                        preparing_select = gr.Dropdown(
                            choices=[],
                            label="Chọn món đang chế biến",
                            info="Chọn món đã nhận làm để xác nhận hoàn thành.",
                        )
                        ready_button = gr.Button("✓ Hoàn thành món", variant="primary")
                    with gr.Column():
                        gr.Markdown("### ✅ Chờ phục vụ", elem_classes=["section-heading"])
                        ready_select = gr.Dropdown(
                            choices=[],
                            label="Chọn món chờ phục vụ",
                            info="Chọn món đã làm xong để xác nhận phục vụ.",
                        )
                        served_button = gr.Button("✓ Đã phục vụ", variant="secondary")

                kitchen_message = gr.Markdown("Chọn **Làm mới** để xem thông tin mới nhất.")
                kitchen_outputs = [
                    queue_table, preparing_select, ready_select,
                    kitchen_counts, kitchen_message,
                ]

                def refresh_kitchen(message="✅ Đã cập nhật danh sách bếp."):
                    """Chỉ đọc dữ liệu qua Controller, không đọc JSON trực tiếp."""
                    try:
                        tasks = context.kitchen_controller.get_queue()
                        orders = context.order_controller.list_orders()
                        preparing_choices, ready_choices = _kitchen_choices(orders)
                        counts = (
                            f"**⏳ Chờ làm:** {len(tasks)} dòng món  |  "
                            f"**🔥 Đang chế biến:** {len(preparing_choices)} dòng món  |  "
                            f"**✅ Chờ phục vụ:** {len(ready_choices)} dòng món"
                        )
                        return (
                            _queue_table(tasks),
                            gr.update(choices=preparing_choices, value=None),
                            gr.update(choices=ready_choices, value=None),
                            counts,
                            message,
                        )
                    except Exception as exc:
                        return (
                            [],
                            gr.update(choices=[], value=None),
                            gr.update(choices=[], value=None),
                            "Không tải được dữ liệu bếp.",
                            f"⚠️ {_error_message(exc)}",
                        )

                def start_next_action():
                    try:
                        item = context.kitchen_controller.start_next_item()
                        message = f"✅ Đang chế biến: **{item.get('name', 'món vừa nhận')}**."
                    except Exception as exc:
                        message = f"⚠️ {_error_message(exc)}"
                    return refresh_kitchen(message)

                def finish_item_action(selected):
                    if not selected:
                        return refresh_kitchen("⚠️ Hãy chọn một món đang chế biến trước.")
                    try:
                        order_id, item_id = json.loads(selected)
                        context.kitchen_controller.mark_item_ready(order_id, item_id)
                        message = "✅ Món đã hoàn thành và chuyển sang Chờ phục vụ."
                    except Exception as exc:
                        message = f"⚠️ {_error_message(exc)}"
                    return refresh_kitchen(message)

                def serve_item_action(selected):
                    if not selected:
                        return refresh_kitchen("⚠️ Hãy chọn một món chờ phục vụ trước.")
                    try:
                        order_id, item_id = json.loads(selected)
                        context.kitchen_controller.mark_item_served(order_id, item_id)
                        message = "✅ Đã xác nhận món được phục vụ."
                    except Exception as exc:
                        message = f"⚠️ {_error_message(exc)}"
                    return refresh_kitchen(message)

                # Mỗi nút nhận kết quả của hàm Python rồi cập nhật giao diện.
                refresh_queue.click(
                    fn=refresh_kitchen,
                    outputs=kitchen_outputs,
                )
                start_next.click(
                    fn=start_next_action,
                    outputs=kitchen_outputs,
                )
                ready_button.click(
                    fn=finish_item_action,
                    inputs=[preparing_select],
                    outputs=kitchen_outputs,
                )
                served_button.click(
                    fn=serve_item_action,
                    inputs=[ready_select],
                    outputs=kitchen_outputs,
                )
                # Tự cập nhật khi chuyển sang thẻ Bếp.
                kitchen_tab.select(fn=refresh_kitchen, outputs=kitchen_outputs)

            with gr.Tab("🧾 Đơn hàng", id="orders"):
                gr.Markdown("### Tra cứu và quản lý đơn", elem_classes=["section-heading"])
                with gr.Row():
                    refresh_orders = gr.Button("Tải danh sách đơn", variant="secondary")
                    search_order_id = gr.Textbox(label="Mã đơn cần xem", placeholder="ORD-...")
                    search_order_button = gr.Button("Tra cứu")
                orders_table = gr.Dataframe(
                    headers=["Mã đơn", "Trạng thái", "Số dòng món", "Tổng tiền", "Ngày tạo"],
                    datatype=["str"] * 5,
                    value=[],
                    interactive=False,
                    wrap=True,
                    label="Lịch sử đơn hàng",
                )
                order_result = gr.JSON(label="Chi tiết đơn", open=False)
                refresh_orders.click(
                    fn=lambda: _orders_table(context.order_controller.list_orders()),
                    outputs=[orders_table],
                )
                search_order_button.click(
                    fn=lambda oid: _safe_json(context.order_controller.get_order, oid.strip()),
                    inputs=[search_order_id],
                    outputs=[order_result],
                )

                gr.Markdown("### Thêm món vào đơn OPEN", elem_classes=["section-heading"])
                with gr.Row():
                    add_order_id = gr.Textbox(label="Mã đơn đang mở")
                    add_menu_id = gr.Dropdown(label="Món cần thêm", choices=menu_choices, scale=2)
                    add_quantity = gr.Number(label="Số lượng", value=1, precision=0, minimum=1)
                add_note = gr.Textbox(label="Ghi chú (không bắt buộc)")
                add_item_button = gr.Button("Thêm món vào đơn")
                add_item_result = gr.JSON(label="Kết quả thêm món", open=False)

                def add_item_to_order(order_id, menu_item_id, amount, item_note):
                    try:
                        clean_amount = _valid_quantity(amount)
                        return context.order_controller.add_items(
                            order_id.strip(),
                            [{"menu_item_id": menu_item_id, "quantity": clean_amount, "note": item_note or ""}],
                        )
                    except Exception as exc:
                        return {"error": _error_message(exc)}

                add_item_button.click(
                    fn=add_item_to_order,
                    inputs=[add_order_id, add_menu_id, add_quantity, add_note],
                    outputs=[add_item_result],
                )

                gr.Markdown("### Hủy đơn (chỉ khi tất cả món còn QUEUED)", elem_classes=["section-heading"])
                with gr.Row():
                    cancel_order_id = gr.Textbox(label="Mã đơn cần hủy")
                    cancel_reason = gr.Textbox(label="Lý do hủy (không bắt buộc)")
                    cancel_button = gr.Button("Hủy đơn", variant="stop")
                cancel_result = gr.JSON(label="Kết quả hủy đơn", open=False)
                cancel_button.click(
                    fn=lambda oid, reason: _safe_json(context.order_controller.cancel_order, oid.strip(), reason or ""),
                    inputs=[cancel_order_id, cancel_reason],
                    outputs=[cancel_result],
                )

            with gr.Tab("💳 Thanh toán", id="payment"):
                gr.Markdown("### Hóa đơn và thanh toán", elem_classes=["section-heading"])
                with gr.Row():
                    payment_order_id = gr.Textbox(label="Mã đơn", placeholder="ORD-...")
                    discount = gr.Number(label="Giảm giá (VND)", value=0, precision=0, minimum=0)
                    payment_method = gr.Dropdown(
                        label="Phương thức",
                        choices=["CASH", "CARD", "TRANSFER"],
                        value="CASH",
                    )
                with gr.Row():
                    preview_button = gr.Button("Xem hóa đơn", variant="secondary")
                    checkout_button = gr.Button("Xác nhận thanh toán", variant="primary")
                bill_output = gr.JSON(label="Hóa đơn / biên nhận", open=False)
                payment_message = gr.Markdown("Chọn đơn để xem hóa đơn.")

                def preview_bill(order_id, discount_amount):
                    try:
                        amount = _valid_quantity(discount_amount) if discount_amount else 0
                        bill = context.payment_controller.preview_bill(order_id.strip(), amount)
                        return bill, "Đã tải hóa đơn. Hãy kiểm tra kỹ trước khi thanh toán."
                    except Exception as exc:
                        return {"error": _error_message(exc)}, "⚠️ Không thể xem hóa đơn."

                preview_button.click(
                    fn=preview_bill,
                    inputs=[payment_order_id, discount],
                    outputs=[bill_output, payment_message],
                )

                def checkout(order_id, method, discount_amount):
                    try:
                        amount = int(discount_amount or 0)
                        receipt = context.payment_controller.checkout(
                            order_id.strip(), method, amount
                        )
                        return receipt, f"✅ Thanh toán thành công cho đơn **{receipt['id']}**."
                    except Exception as exc:
                        return {"error": _error_message(exc)}, "⚠️ Thanh toán chưa thành công."

                checkout_button.click(
                    fn=checkout,
                    inputs=[payment_order_id, payment_method, discount],
                    outputs=[bill_output, payment_message],
                )

    return demo
