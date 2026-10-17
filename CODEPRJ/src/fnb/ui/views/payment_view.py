"""View màn hình Thanh toán (Billing & Cashier) — Thuần Gradio Native Components."""

from dataclasses import dataclass

import gradio as gr

from fnb.ui.presenter import FnbPresenter


@dataclass
class PaymentViewComponents:
    """Tập hợp tất cả UI components của Màn hình Thanh toán."""

    order_select_dropdown: gr.Dropdown
    btn_refresh_unpaid: gr.Button
    bill_items_table: gr.Dataframe
    total_due_md: gr.Markdown
    payment_method_radio: gr.Radio
    btn_checkout: gr.Button
    checkout_feedback_md: gr.Markdown
    receipt_preview_md: gr.Markdown


def build_payment_view(presenter: FnbPresenter) -> PaymentViewComponents:
    """Xây dựng layout View màn hình Thanh toán, không chứa logic nghiệp vụ."""
    unpaid_choices = presenter.get_unpaid_order_choices()

    gr.Markdown("## 💳 Thanh toán hóa đơn dịch vụ")

    with gr.Row(equal_height=False):
        # Cột Bên trái: Chọn đơn hàng & Chi tiết món ăn
        with gr.Column(scale=7):
            with gr.Row():
                order_select_dropdown = gr.Dropdown(
                    label="Chọn đơn hàng cần thanh toán",
                    choices=unpaid_choices,
                    scale=3,
                )
                btn_refresh_unpaid = gr.Button("🔄 Làm mới đơn", scale=1)

            gr.Markdown("### 📋 Chi tiết các món trong hóa đơn")
            bill_items_table = gr.Dataframe(
                headers=["Tên món", "Số lượng", "Đơn giá", "Thành tiền", "Trạng thái món"],
                datatype=["str", "str", "str", "str", "str"],
                value=[],
                interactive=False,
                wrap=True,
            )

            total_due_md = gr.Markdown("## 💵 TỔNG CẦN THANH TOÁN: **0 ₫**")

        # Cột Bên phải: Phương thức thanh toán & Xác nhận
        with gr.Column(scale=5):
            gr.Markdown("### 💰 Hình thức thanh toán")
            payment_method_radio = gr.Radio(
                label="Chọn phương thức thanh toán",
                choices=[
                    "💵 TIỀN MẶT (CASH)",
                    "📲 CHUYỂN KHOẢN QR (TRANSFER)",
                    "💳 THẺ NGÂN HÀNG (CARD)",
                ],
                value="💵 TIỀN MẶT (CASH)",
            )

            btn_checkout = gr.Button(
                "✅ HOÀN TẤT THANH TOÁN & XUẤT HÓA ĐƠN",
                variant="primary",
                size="lg",
            )

            checkout_feedback_md = gr.Markdown()
            receipt_preview_md = gr.Markdown()

    return PaymentViewComponents(
        order_select_dropdown=order_select_dropdown,
        btn_refresh_unpaid=btn_refresh_unpaid,
        bill_items_table=bill_items_table,
        total_due_md=total_due_md,
        payment_method_radio=payment_method_radio,
        btn_checkout=btn_checkout,
        checkout_feedback_md=checkout_feedback_md,
        receipt_preview_md=receipt_preview_md,
    )
