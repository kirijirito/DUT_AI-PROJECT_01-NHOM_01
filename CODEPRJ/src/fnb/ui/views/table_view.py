"""View màn hình Phục vụ (Sơ đồ bàn, Quản lý trạng thái & Bếp) — Thuần Gradio Native Components."""

from dataclasses import dataclass

import gradio as gr

from fnb.ui.presenter import FnbPresenter


@dataclass
class TableViewComponents:
    """Tập hợp tất cả UI components của Màn hình Phục vụ."""

    selected_table_id: gr.State
    table_buttons: list[tuple[gr.Button, str]]
    tables_dataframe: gr.Dataframe
    btn_refresh_tables: gr.Button
    table_details_md: gr.Markdown
    btn_mark_served: gr.Button
    transfer_from_dropdown: gr.Dropdown
    transfer_to_dropdown: gr.Dropdown
    btn_transfer: gr.Button
    merge_from_dropdown: gr.Dropdown
    merge_to_dropdown: gr.Dropdown
    btn_merge: gr.Button
    table_feedback_md: gr.Markdown
    kitchen_queue_table: gr.Dataframe
    btn_start_next_item: gr.Button
    kitchen_order_id_input: gr.Textbox
    kitchen_item_id_input: gr.Textbox
    btn_mark_ready: gr.Button
    btn_mark_served_item: gr.Button
    btn_refresh_kitchen: gr.Button
    kitchen_feedback_md: gr.Markdown


def build_table_view(presenter: FnbPresenter) -> TableViewComponents:
    """Xây dựng layout View màn hình Sơ đồ bàn & Bếp, không chứa logic nghiệp vụ."""
    selected_table_id = gr.State("T-01")
    table_choices = presenter.get_table_dropdown_choices()

    gr.Markdown("## 🪑 Sơ đồ bàn & Quản lý phục vụ")

    with gr.Row(equal_height=False):
        # Cột Bên trái: Sơ đồ bàn trực quan & Bảng trạng thái
        with gr.Column(scale=7):
            gr.Markdown("### 📍 Khu vực Tầng 1 (Trong nhà)")
            table_buttons: list[tuple[gr.Button, str]] = []
            with gr.Row():
                for i in range(1, 4):
                    t_id = f"T-{i:02d}"
                    btn = gr.Button(f"Bàn {i:02d}", variant="secondary", size="lg")
                    table_buttons.append((btn, t_id))
            with gr.Row():
                for i in range(4, 7):
                    t_id = f"T-{i:02d}"
                    btn = gr.Button(f"Bàn {i:02d}", variant="secondary", size="lg")
                    table_buttons.append((btn, t_id))

            gr.Markdown("### 🌿 Khu vực Tầng 2 (Sân thượng)")
            with gr.Row():
                for i in range(7, 10):
                    t_id = f"T-{i:02d}"
                    btn = gr.Button(f"Bàn {i:02d}", variant="secondary", size="lg")
                    table_buttons.append((btn, t_id))
            with gr.Row():
                for i in range(10, 13):
                    t_id = f"T-{i:02d}"
                    btn = gr.Button(f"Bàn {i:02d}", variant="secondary", size="lg")
                    table_buttons.append((btn, t_id))

            gr.Markdown("### 📊 Danh sách tất cả bàn & Đơn hàng liên kết")
            tables_dataframe = gr.Dataframe(
                headers=["Tên bàn", "Khu vực", "Trạng thái", "Mã đơn", "Số món", "Tạm tính"],
                datatype=["str", "str", "str", "str", "str", "str"],
                value=presenter.get_tables_table_data(),
                interactive=False,
                wrap=True,
            )
            btn_refresh_tables = gr.Button("🔄 Cập nhật sơ đồ bàn", size="sm")

        # Cột Bên phải: Chi tiết bàn được chọn & Thao tác chuyển/gộp bàn
        with gr.Column(scale=5):
            table_details_md = gr.Markdown(presenter.get_table_details_markdown("T-01"))

            btn_mark_served = gr.Button(
                "✔️ Đã lên đủ món cho bàn này",
                variant="primary",
                size="md",
            )

            gr.Markdown("### 🔀 Thao tác nhanh: Chuyển bàn")
            with gr.Row():
                transfer_from_dropdown = gr.Dropdown(
                    label="Từ bàn (Có khách)",
                    choices=table_choices,
                    scale=1,
                )
                transfer_to_dropdown = gr.Dropdown(
                    label="Sang bàn (Trống)",
                    choices=table_choices,
                    scale=1,
                )
            btn_transfer = gr.Button("➡️ Thực hiện chuyển bàn", size="sm")

            gr.Markdown("### 👥 Thao tác nhanh: Gộp bàn")
            with gr.Row():
                merge_from_dropdown = gr.Dropdown(
                    label="Bàn cần gộp",
                    choices=table_choices,
                    scale=1,
                )
                merge_to_dropdown = gr.Dropdown(
                    label="Gộp vào bàn chính",
                    choices=table_choices,
                    scale=1,
                )
            btn_merge = gr.Button("🔗 Thực hiện gộp bàn", size="sm")

            table_feedback_md = gr.Markdown()

    gr.Markdown("---")
    # Khu vực Bếp KDS (Kitchen Display System) FIFO Queue
    gr.Markdown("## 🍳 Hàng đợi chế biến món Bếp (FIFO Queue)")
    with gr.Row():
        with gr.Column(scale=8):
            kitchen_queue_table = gr.Dataframe(
                headers=[
                    "STT Bếp",
                    "Mã đơn",
                    "Vị trí bàn",
                    "Tên món",
                    "Số lượng",
                    "Trạng thái",
                    "Ghi chú",
                    "Item ID",
                ],
                datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                value=presenter.get_kitchen_queue_data(),
                interactive=False,
                wrap=True,
            )
            with gr.Row():
                btn_start_next_item = gr.Button(
                    "🔥 Bếp bắt đầu nấu món tiếp theo (FIFO)",
                    variant="primary",
                    scale=2,
                )
                btn_refresh_kitchen = gr.Button("🔄 Làm mới hàng đợi bếp", scale=1)

        with gr.Column(scale=4):
            gr.Markdown("### ⚡ Cập nhật trạng thái món ăn")
            kitchen_order_id_input = gr.Textbox(
                label="Mã đơn hàng",
                placeholder="Ví dụ: ORD-...",
            )
            kitchen_item_id_input = gr.Textbox(
                label="Mã món (Item ID)",
                placeholder="Ví dụ: ITM-...",
            )
            with gr.Row():
                btn_mark_ready = gr.Button("🍽️ Đã nấu xong (READY)", variant="secondary")
                btn_mark_served_item = gr.Button("✔️ Đã phục vụ (SERVED)", variant="secondary")

            kitchen_feedback_md = gr.Markdown()

    return TableViewComponents(
        selected_table_id=selected_table_id,
        table_buttons=table_buttons,
        tables_dataframe=tables_dataframe,
        btn_refresh_tables=btn_refresh_tables,
        table_details_md=table_details_md,
        btn_mark_served=btn_mark_served,
        transfer_from_dropdown=transfer_from_dropdown,
        transfer_to_dropdown=transfer_to_dropdown,
        btn_transfer=btn_transfer,
        merge_from_dropdown=merge_from_dropdown,
        merge_to_dropdown=merge_to_dropdown,
        btn_merge=btn_merge,
        table_feedback_md=table_feedback_md,
        kitchen_queue_table=kitchen_queue_table,
        btn_start_next_item=btn_start_next_item,
        kitchen_order_id_input=kitchen_order_id_input,
        kitchen_item_id_input=kitchen_item_id_input,
        btn_mark_ready=btn_mark_ready,
        btn_mark_served_item=btn_mark_served_item,
        btn_refresh_kitchen=btn_refresh_kitchen,
        kitchen_feedback_md=kitchen_feedback_md,
    )
