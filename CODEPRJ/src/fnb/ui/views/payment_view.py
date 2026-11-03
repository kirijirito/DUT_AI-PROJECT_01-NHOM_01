"""View xem hóa đơn và xác nhận thanh toán."""

from dataclasses import dataclass

import gradio as gr

from fnb.ui.presenter import FnbPresenter


@dataclass
class PaymentViewComponents:
    order_dropdown: gr.Dropdown
    btn_refresh: gr.Button
    bill_table: gr.Dataframe
    total_md: gr.Markdown
    status_md: gr.Markdown
    btn_checkout: gr.Button
    checkout_feedback: gr.Markdown
    receipt_md: gr.Markdown


def build_payment_view(presenter: FnbPresenter) -> PaymentViewComponents:
    gr.Markdown("### 💳 Thanh toán & Hóa đơn")
    with gr.Row():
        order_dropdown = gr.Dropdown(
            label="Chọn đơn hàng cần thanh toán",
            choices=presenter.get_unpaid_order_choices(),
            scale=5,
        )
        btn_refresh = gr.Button("🔄 Làm mới đơn", scale=1)

    bill_table = gr.Dataframe(
        headers=["STT", "Tên món", "SL", "Đơn giá", "Thành tiền", "Ghi chú", "Trạng thái"],
        datatype=["str", "str", "str", "str", "str", "str", "str"],
        value=[],
        interactive=False,
        wrap=True,
    )
    total_md = gr.Markdown("**Tổng thanh toán: 0 đ**")
    status_md = gr.Markdown("Chọn một đơn để xem tình trạng các món.")
    btn_checkout = gr.Button("🧾 XÁC NHẬN THANH TOÁN & IN BILL", variant="primary", size="lg")
    checkout_feedback = gr.Markdown()
    receipt_md = gr.Markdown()

    return PaymentViewComponents(
        order_dropdown=order_dropdown,
        btn_refresh=btn_refresh,
        bill_table=bill_table,
        total_md=total_md,
        status_md=status_md,
        btn_checkout=btn_checkout,
        checkout_feedback=checkout_feedback,
        receipt_md=receipt_md,
    )
