"""View màn hình Hóa đơn (Lịch sử & Xuất hóa đơn) — Thuần Gradio Native Components."""

from dataclasses import dataclass
from datetime import date

import gradio as gr

from fnb.ui.presenter import FnbPresenter


@dataclass
class InvoiceViewComponents:
    """Tập hợp tất cả UI components của Màn hình Hóa đơn & Báo cáo."""

    date_input: gr.Textbox
    btn_today: gr.Button
    btn_yesterday: gr.Button
    btn_load_history: gr.Button
    kpi_summary_md: gr.Markdown
    invoices_table: gr.Dataframe
    order_id_preview_input: gr.Textbox
    btn_preview_receipt: gr.Button
    receipt_preview_display: gr.Markdown


def build_invoice_view(presenter: FnbPresenter) -> InvoiceViewComponents:
    """Xây dựng layout View màn hình Hóa đơn & Báo cáo, không chứa logic nghiệp vụ."""
    today_iso = date.today().isoformat()
    init_rows, init_summary = presenter.get_invoice_history(today_iso)

    gr.Markdown("## 📑 Lịch sử hóa đơn & Báo cáo ca làm việc")

    with gr.Row():
        date_input = gr.Textbox(
            label="Chọn ngày (YYYY-MM-DD)",
            value=today_iso,
            scale=2,
        )
        btn_today = gr.Button("📅 Hôm nay", scale=1)
        btn_yesterday = gr.Button("⏮️ Hôm qua", scale=1)
        btn_load_history = gr.Button("🔍 Tra cứu lịch sử", variant="primary", scale=1)

    with gr.Row(equal_height=False):
        # Cột Bên trái: Tổng kết doanh thu & Bảng hóa đơn
        with gr.Column(scale=7):
            kpi_summary_md = gr.Markdown(init_summary)

            gr.Markdown("### 📜 Danh sách hóa đơn đã hoàn tất trong ngày")
            invoices_table = gr.Dataframe(
                headers=[
                    "Mã đơn",
                    "Khu vực / Bàn",
                    "Số món",
                    "Tổng tiền",
                    "Hình thức",
                    "Thời gian thanh toán",
                ],
                datatype=["str", "str", "str", "str", "str", "str"],
                value=init_rows,
                interactive=False,
                wrap=True,
            )

        # Cột Bên phải: Xem trước hóa đơn trước khi xuất/in
        with gr.Column(scale=5):
            gr.Markdown("### 🖨️ Xem trước hóa đơn trước khi in / xuất")
            with gr.Row():
                order_id_preview_input = gr.Textbox(
                    label="Mã đơn hàng cần in",
                    placeholder="Ví dụ: ORD-...",
                    scale=3,
                )
                btn_preview_receipt = gr.Button("🔍 Xem hóa đơn", scale=1)

            receipt_preview_display = gr.Markdown("*(Chọn hoặc nhập mã đơn để xem hóa đơn)*")

    return InvoiceViewComponents(
        date_input=date_input,
        btn_today=btn_today,
        btn_yesterday=btn_yesterday,
        btn_load_history=btn_load_history,
        kpi_summary_md=kpi_summary_md,
        invoices_table=invoices_table,
        order_id_preview_input=order_id_preview_input,
        btn_preview_receipt=btn_preview_receipt,
        receipt_preview_display=receipt_preview_display,
    )
