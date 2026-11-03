"""View hàng đợi bếp và danh sách món đã phục vụ."""

from dataclasses import dataclass

import gradio as gr

from fnb.ui.presenter import FnbPresenter


@dataclass
class KitchenViewComponents:
    queue_table: gr.Dataframe
    served_table: gr.Dataframe
    btn_refresh: gr.Button
    btn_serve_next: gr.Button
    feedback: gr.Markdown


def build_kitchen_view(presenter: FnbPresenter) -> KitchenViewComponents:
    gr.Markdown("### 🍳 Hàng đợi bếp — Queue FIFO tự cài đặt bằng Linked List")
    gr.Markdown(
        "Món được phục vụ theo thứ tự vào trước, ra trước. "
        "Mỗi dòng món là một Node; số lượng nằm trong Node đó."
    )

    queue_table = gr.Dataframe(
        headers=["STT", "Mã đơn", "Mã dòng món", "Tên món", "SL", "Ghi chú", "Trạng thái"],
        datatype=["str", "str", "str", "str", "str", "str", "str"],
        value=presenter.get_queue_rows(),
        interactive=False,
        wrap=True,
    )
    with gr.Row():
        btn_refresh = gr.Button("🔄 Làm mới Queue", variant="secondary")
        btn_serve_next = gr.Button("✅ XÁC NHẬN MÓN ĐẦU HÀNG ĐỢI ĐÃ PHỤC VỤ", variant="primary")
    feedback = gr.Markdown()

    gr.Markdown("### ✅ Các món đã phục vụ")
    served_table = gr.Dataframe(
        headers=["Mã đơn", "Mã dòng món", "Tên món", "SL", "Trạng thái"],
        datatype=["str", "str", "str", "str", "str"],
        value=presenter.get_served_rows(),
        interactive=False,
        wrap=True,
    )

    return KitchenViewComponents(
        queue_table=queue_table,
        served_table=served_table,
        btn_refresh=btn_refresh,
        btn_serve_next=btn_serve_next,
        feedback=feedback,
    )
