"""View màn hình Order (Đặt món & Giỏ hàng) — Thuần Gradio Native Components."""

from dataclasses import dataclass

import gradio as gr

from fnb.ui.presenter import FnbPresenter, format_vnd


@dataclass
class OrderViewComponents:
    """Tập hợp tất cả UI components của Màn hình Đặt món."""

    cart_state: gr.State
    selected_cart_idx: gr.State
    quantity_input: gr.Number
    note_input: gr.Textbox
    quick_menu_dropdown: gr.Dropdown
    btn_quick_add: gr.Button
    table_select_dropdown: gr.Dropdown
    menu_buttons: list[tuple[gr.Button, dict]]
    cart_table: gr.Dataframe
    btn_qty_up: gr.Button
    btn_qty_down: gr.Button
    btn_remove_item: gr.Button
    btn_clear_cart: gr.Button
    cart_summary_md: gr.Markdown
    btn_submit_order: gr.Button
    order_feedback_md: gr.Markdown


def build_order_view(presenter: FnbPresenter) -> OrderViewComponents:
    """Xây dựng layout View màn hình Đặt món, không chứa logic nghiệp vụ."""
    cart_state = gr.State([])
    selected_cart_idx = gr.State(None)

    menu_items = presenter.context.menu_controller.list_menu(available_only=True)
    menu_items = sorted(menu_items, key=lambda it: it["name"])

    with gr.Row(equal_height=False):
        # Cột Bên trái: Thực đơn món ăn
        with gr.Column(scale=7):
            gr.Markdown("## 📋 Thực đơn nhà hàng")

            with gr.Row():
                table_select_dropdown = gr.Dropdown(
                    label="Chọn bàn phục vụ (Tùy chọn)",
                    choices=presenter.get_table_dropdown_choices(),
                )

            with gr.Row():
                quantity_input = gr.Number(
                    label="Số lượng",
                    value=1,
                    precision=0,
                    minimum=1,
                    scale=1,
                )
                note_input = gr.Textbox(
                    label="Ghi chú món ăn",
                    placeholder="Ví dụ: không hành, ít đá, nhiều sốt...",
                    scale=2,
                )

            with gr.Row():
                quick_menu_dropdown = gr.Dropdown(
                    label="Tìm kiếm / Chọn nhanh món ăn",
                    choices=presenter.get_menu_choices(),
                    scale=3,
                )
                btn_quick_add = gr.Button("➕ Thêm vào giỏ", variant="secondary", scale=1)

            menu_buttons = []
            for start in range(0, len(menu_items), 3):
                with gr.Row():
                    for it in menu_items[start : start + 3]:
                        btn_text = f"✨ {it['name']}\n💵 {format_vnd(it['price'])}"
                        btn = gr.Button(btn_text, variant="secondary", scale=1)
                        menu_buttons.append((btn, it))

        # Cột Bên phải: Giỏ hàng & Tạo đơn
        with gr.Column(scale=5):
            gr.Markdown("## 🛒 Giỏ hàng đặt món")

            cart_table = gr.Dataframe(
                headers=["Tên món & Ghi chú", "SL", "Đơn giá", "Thành tiền"],
                datatype=["str", "str", "str", "str"],
                value=[],
                interactive=False,
                wrap=True,
                label="Danh sách món đã chọn (Bấm vào dòng để sửa số lượng/xóa)",
            )

            with gr.Row():
                btn_qty_up = gr.Button("➕ Tăng 1", size="sm")
                btn_qty_down = gr.Button("➖ Giảm 1", size="sm")
                btn_remove_item = gr.Button("❌ Xóa món chọn", size="sm")
                btn_clear_cart = gr.Button("🗑️ Xóa toàn bộ giỏ", size="sm")

            cart_summary_md = gr.Markdown("### 🛒 Giỏ hàng: Đang trống (0 phần ăn)")

            btn_submit_order = gr.Button(
                "⚡ XÁC NHẬN TẠO ĐƠN & GỬI BẾP (FIFO)",
                variant="primary",
                size="lg",
            )

            order_feedback_md = gr.Markdown()

    return OrderViewComponents(
        cart_state=cart_state,
        selected_cart_idx=selected_cart_idx,
        quantity_input=quantity_input,
        note_input=note_input,
        quick_menu_dropdown=quick_menu_dropdown,
        btn_quick_add=btn_quick_add,
        table_select_dropdown=table_select_dropdown,
        menu_buttons=menu_buttons,
        cart_table=cart_table,
        btn_qty_up=btn_qty_up,
        btn_qty_down=btn_qty_down,
        btn_remove_item=btn_remove_item,
        btn_clear_cart=btn_clear_cart,
        cart_summary_md=cart_summary_md,
        btn_submit_order=btn_submit_order,
        order_feedback_md=order_feedback_md,
    )
