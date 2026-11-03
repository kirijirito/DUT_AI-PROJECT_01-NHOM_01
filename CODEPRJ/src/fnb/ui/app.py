"""Giao diện Gradio 3 tab: Đặt món, Queue bếp, Thanh toán."""

import gradio as gr

from fnb.bootstrap import AppContext
from fnb.ui.presenter import FnbPresenter
from fnb.ui.views import build_kitchen_view, build_order_view, build_payment_view


FNB_THEME = gr.themes.Base(primary_hue="orange", neutral_hue="slate").set(
    body_background_fill="#101010",
    body_text_color="#f4f4f5",
    block_background_fill="#191919",
    block_border_color="#383838",
    input_background_fill="#111111",
    input_border_color="#3a3a3a",
)

CUSTOM_CSS = """
.gradio-container {
    max-width: 1580px !important;
    padding: 18px 24px 30px !important;
}
#fnb-title h1 {
    font-size: 30px !important;
    line-height: 1.25 !important;
    margin: 4px 0 8px !important;
}
#fnb-subtitle { opacity: .82; margin-bottom: 16px; }
.menu-panel, .cart-panel, .section-panel {
    border: 1px solid var(--border-color-primary);
    border-radius: 10px;
    padding: 12px;
}
button.primary { background: #e85d04 !important; border-color: #e85d04 !important; }
button.stop { background: #b91c1c !important; border-color: #b91c1c !important; }
footer { display: none !important; }
@media (max-width: 850px) {
    .gradio-container { padding: 10px !important; }
    #fnb-title h1 { font-size: 23px !important; }
}
"""


def create_app(context: AppContext) -> gr.Blocks:
    presenter = FnbPresenter(context)

    with gr.Blocks(
        title="F&B Simple Order System",
    ) as app:
        gr.Markdown("# 🍽️ HỆ THỐNG QUẢN LÝ ĐƠN HÀNG NHÀ HÀNG (F&B)", elem_id="fnb-title")
        gr.Markdown(
            "Giao diện Web trực quan · Hash Map tra cứu menu O(1) · "
            "Queue FIFO bằng Linked List tự cài đặt",
            elem_id="fnb-subtitle",
        )

        with gr.Tabs():
            with gr.Tab("🛒 1. Đặt món (Tạo đơn hàng)"):
                order_view = build_order_view(presenter)
            with gr.Tab("🍳 2. Hàng đợi bếp (Queue FIFO)"):
                kitchen_view = build_kitchen_view(presenter)
            with gr.Tab("🧾 3. Thanh toán & Hóa đơn"):
                payment_view = build_payment_view(presenter)

        # Tab 1: tạo giỏ hàng tạm và gửi đơn qua Controller.
        order_view.btn_add.click(
            fn=presenter.add_item_to_cart,
            inputs=[
                order_view.menu_dropdown,
                order_view.quantity_input,
                order_view.note_input,
                order_view.cart_state,
            ],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary,
                order_view.feedback,
            ],
        )

        def select_cart_row(evt: gr.SelectData):
            return evt.index[0] if evt and evt.index else None

        order_view.cart_table.select(
            fn=select_cart_row,
            outputs=[order_view.selected_cart_idx],
        )

        order_view.btn_increase.click(
            fn=lambda cart, index: presenter.adjust_cart_item(cart, index, 1),
            inputs=[order_view.cart_state, order_view.selected_cart_idx],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary,
                order_view.feedback,
            ],
        )
        order_view.btn_decrease.click(
            fn=lambda cart, index: presenter.adjust_cart_item(cart, index, -1),
            inputs=[order_view.cart_state, order_view.selected_cart_idx],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary,
                order_view.feedback,
            ],
        )
        order_view.btn_remove.click(
            fn=presenter.remove_selected_cart_item,
            inputs=[order_view.cart_state, order_view.selected_cart_idx],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary,
                order_view.feedback,
            ],
        )
        order_view.btn_clear.click(
            fn=presenter.clear_cart,
            inputs=[],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary,
                order_view.feedback,
            ],
        )

        def handle_submit_order(cart):
            new_cart, rows, summary, message, queue_rows, choices = presenter.submit_order(cart)
            return (
                new_cart, rows, summary, message, queue_rows,
                gr.update(choices=choices, value=None),
            )

        order_view.btn_create_order.click(
            fn=handle_submit_order,
            inputs=[order_view.cart_state],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary,
                order_view.feedback,
                kitchen_view.queue_table,
                payment_view.order_dropdown,
            ],
        )

        # Tab 2: chỉ được phục vụ Node ở đầu Queue để bảo toàn FIFO.
        kitchen_view.btn_refresh.click(
            fn=presenter.refresh_kitchen,
            inputs=[],
            outputs=[kitchen_view.queue_table, kitchen_view.served_table],
        )

        def handle_serve_next():
            message, queue_rows, served_rows, choices = presenter.serve_next_item()
            return (
                message, queue_rows, served_rows,
                gr.update(choices=choices),
            )

        kitchen_view.btn_serve_next.click(
            fn=handle_serve_next,
            inputs=[],
            outputs=[
                kitchen_view.feedback,
                kitchen_view.queue_table,
                kitchen_view.served_table,
                payment_view.order_dropdown,
            ],
        )

        # Tab 3: Backend tự kiểm tra tất cả món đã SERVED trước khi checkout.
        payment_view.order_dropdown.change(
            fn=presenter.load_bill_for_payment,
            inputs=[payment_view.order_dropdown],
            outputs=[payment_view.bill_table, payment_view.total_md, payment_view.status_md],
        )
        payment_view.btn_refresh.click(
            fn=lambda _current: gr.update(choices=presenter.get_unpaid_order_choices(), value=None),
            inputs=[payment_view.order_dropdown],
            outputs=[payment_view.order_dropdown],
        )
        def handle_checkout(order_id):
            message, receipt, choices, rows, total = presenter.checkout_and_print(order_id)
            return (
                message, receipt, gr.update(choices=choices, value=None), rows, total
            )

        payment_view.btn_checkout.click(
            fn=handle_checkout,
            inputs=[payment_view.order_dropdown],
            outputs=[
                payment_view.checkout_feedback,
                payment_view.receipt_md,
                payment_view.order_dropdown,
                payment_view.bill_table,
                payment_view.total_md,
            ],
        )

    return app
