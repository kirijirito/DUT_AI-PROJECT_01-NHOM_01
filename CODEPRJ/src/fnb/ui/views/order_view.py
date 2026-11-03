"""View chọn món và tạo đơn."""

from dataclasses import dataclass

import gradio as gr

from fnb.ui.presenter import FnbPresenter


@dataclass
class OrderViewComponents:
    cart_state: gr.State
    selected_cart_idx: gr.State
    menu_table: gr.Dataframe
    menu_dropdown: gr.Dropdown
    quantity_input: gr.Number
    note_input: gr.Textbox
    btn_add: gr.Button
    cart_table: gr.Dataframe
    cart_summary: gr.Markdown
    btn_increase: gr.Button
    btn_decrease: gr.Button
    btn_remove: gr.Button
    btn_clear: gr.Button
    btn_create_order: gr.Button
    feedback: gr.Markdown


def build_order_view(presenter: FnbPresenter) -> OrderViewComponents:
    cart_state = gr.State([])
    selected_cart_idx = gr.State(None)

    with gr.Row(equal_height=False):
        with gr.Column(scale=8, min_width=420):
            gr.Markdown("### 📋 Thực đơn quán ăn (Tra cứu O(1))")
            menu_table = gr.Dataframe(
                headers=["Mã", "Tên món", "Loại", "Đơn giá"],
                datatype=["str", "str", "str", "str"],
                value=presenter.get_menu_table_data(),
                interactive=False,
                wrap=True,
            )

        with gr.Column(scale=11, min_width=480):
            gr.Markdown("### ➕ Thêm món vào đơn")
            menu_dropdown = gr.Dropdown(
                label="Chọn món ăn",
                choices=presenter.get_menu_choices(),
                interactive=True,
            )
            with gr.Row():
                quantity_input = gr.Number(
                    label="Số lượng", value=1, precision=0, minimum=1, scale=1
                )
                note_input = gr.Textbox(
                    label="Ghi chú món", placeholder="Ví dụ: ít cay, ít đá...", scale=2
                )
            with gr.Row():
                btn_add = gr.Button("➕ Thêm vào giỏ", variant="secondary", scale=1)
                btn_clear = gr.Button("🗑️ Xóa giỏ hàng", variant="stop", scale=1)

            gr.Markdown("### 🛍️ Giỏ hàng tạm")
            cart_table = gr.Dataframe(
                headers=["STT", "Mã món", "Tên món", "SL", "Thành tiền", "Ghi chú"],
                datatype=["str", "str", "str", "str", "str", "str"],
                value=[],
                interactive=False,
                wrap=True,
            )
            with gr.Row():
                btn_increase = gr.Button("＋ Tăng SL", size="sm")
                btn_decrease = gr.Button("－ Giảm SL", size="sm")
                btn_remove = gr.Button("Xóa dòng chọn", size="sm", variant="stop")
            cart_summary = gr.Markdown("Giỏ hàng đang trống.")
            btn_create_order = gr.Button(
                "🚀 XÁC NHẬN TẠO ĐƠN & GỬI VÀO QUEUE",
                variant="primary",
                size="lg",
            )
            feedback = gr.Markdown()

    return OrderViewComponents(
        cart_state=cart_state,
        selected_cart_idx=selected_cart_idx,
        menu_table=menu_table,
        menu_dropdown=menu_dropdown,
        quantity_input=quantity_input,
        note_input=note_input,
        btn_add=btn_add,
        cart_table=cart_table,
        cart_summary=cart_summary,
        btn_increase=btn_increase,
        btn_decrease=btn_decrease,
        btn_remove=btn_remove,
        btn_clear=btn_clear,
        btn_create_order=btn_create_order,
        feedback=feedback,
    )
