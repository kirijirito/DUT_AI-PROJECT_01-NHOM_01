"""Giao diện Gradio Quản lý F&B Đơn Giản, Dễ Hiểu cho Đồ Án Sinh Viên OOP.

Hệ thống tập trung vào:
1. Dữ liệu vào là Đơn Hàng (Order)
2. Luồng 3 Hàng Đợi (Queues): Đang đợi -> Đang nấu -> Chờ phục vụ -> Đã phục vụ
3. Thanh toán đơn giản, dễ hiểu với chi tiết hóa đơn
4. Tra cứu O(1) bằng Bảng Băm (Hash Map) và Thống kê doanh thu
"""

import gradio as gr

from fnb.bootstrap import AppContext
from fnb.ui.presenter import FnbPresenter


def create_app(context: AppContext) -> gr.Blocks:
    """Tạo ứng dụng Gradio quản lý F&B."""
    presenter = FnbPresenter(context)

    with gr.Blocks(title="F&B Order Management System") as app:
        gr.Markdown(
            """
            # 🍽️ HỆ THỐNG QUẢN LÝ ĐƠN HÀNG NHÀ HÀNG (F&B)
            *Ứng dụng OOP cơ bản kết hợp Cấu trúc dữ liệu Hash Map O(1) & 3 Hàng đợi (Queues FIFO)*
            """
        )

        with gr.Tabs():
            # =================================================================
            # TAB 1: ĐẶT MÓN & TẠO ĐƠN HÀNG (INPUT DATA)
            # =================================================================
            with gr.Tab("🛒 1. Đặt món (Tạo đơn hàng)"):
                with gr.Row():
                    # Cột trái: Chọn món & Menu
                    with gr.Column(scale=6):
                        gr.Markdown("### 📋 Danh mục thực đơn (Hash Map)")
                        gr.Dataframe(
                            headers=["Mã món", "Tên món", "Danh mục", "Đơn giá", "Trạng thái"],
                            datatype=["str", "str", "str", "str", "str"],
                            value=presenter.get_menu_table_data(),
                            interactive=False,
                            wrap=True,
                        )

                        with gr.Group():
                            gr.Markdown("### ➕ Chọn món thêm vào giỏ")
                            item_dropdown = gr.Dropdown(
                                label="Chọn món ăn",
                                choices=presenter.get_menu_choices(),
                                value=presenter.get_menu_choices()[0][1]
                                if presenter.get_menu_choices()
                                else None,
                            )
                            with gr.Row():
                                qty_input = gr.Number(
                                    label="Số lượng", value=1, precision=0, minimum=1, scale=1
                                )
                                note_input = gr.Textbox(
                                    label="Ghi chú (Tùy chọn)",
                                    placeholder="Ví dụ: Ít đường, Không hành...",
                                    scale=2,
                                )
                            btn_add_to_cart = gr.Button("➕ Thêm vào giỏ hàng", variant="secondary")

                    # Cột phải: Giỏ hàng & Tạo đơn
                    with gr.Column(scale=6):
                        gr.Markdown("### 🛒 Giỏ hàng hiện tại")
                        cart_state = gr.State([])
                        selected_cart_idx = gr.State(None)

                        cart_table = gr.Dataframe(
                            headers=["Tên món & Ghi chú", "Số lượng", "Đơn giá", "Thành tiền"],
                            datatype=["str", "str", "str", "str"],
                            interactive=False,
                            wrap=True,
                        )

                        cart_summary_md = gr.Markdown("### 🛒 Giỏ hàng trống")

                        with gr.Row():
                            btn_qty_up = gr.Button("🔼 Tăng (+1)", size="sm")
                            btn_qty_down = gr.Button("🔽 Giảm (-1)", size="sm")
                            btn_clear_cart = gr.Button("🗑️ Xóa giỏ", size="sm", variant="stop")

                        btn_submit_order = gr.Button(
                            "🚀 TẠO ĐƠN HÀNG (GỬI VÀO BẾP)",
                            variant="primary",
                            size="lg",
                        )
                        order_feedback_md = gr.Markdown()

            # =================================================================
            # TAB 2: HÀNG ĐỢI BẾP & PHỤC VỤ (3 QUEUES FIFO)
            # =================================================================
            with gr.Tab("🍳 2. Quy trình Bếp & Phục vụ (3 Queues)"):
                gr.Markdown(
                    "### 🔄 Quy trình xử lý theo 3 Hàng đợi (Queues FIFO):\n"
                    "`Đơn mới` ➔ ⏳ **[Queue 1: Đang Đợi]** ➔ "
                    "🔥 **[Queue 2: Đang Nấu]** ➔ "
                    "🍽️ **[Queue 3: Chờ Phục Vụ]** ➔ ✔️ **[Đã Phục Vụ]**"
                )

                with gr.Row():
                    # Queue 1: Đang đợi
                    with gr.Column(scale=4):
                        gr.Markdown("#### ⏳ 1. Hàng đợi Đang Đợi (Waiting)")
                        queue_waiting_table = gr.Dataframe(
                            headers=["STT", "Mã đơn", "Tên món", "SL", "Ghi chú", "Item ID"],
                            datatype=["str", "str", "str", "str", "str", "str"],
                            value=presenter.get_waiting_queue_data(),
                            interactive=False,
                            wrap=True,
                        )
                        btn_start_cooking = gr.Button(
                            "🔥 Bắt đầu nấu món tiếp theo (FIFO)", variant="primary"
                        )

                    # Queue 2: Đang nấu
                    with gr.Column(scale=4):
                        gr.Markdown("#### 🔥 2. Hàng đợi Đang Nấu (Cooking)")
                        queue_cooking_table = gr.Dataframe(
                            headers=["STT", "Mã đơn", "Tên món", "SL", "Ghi chú", "Item ID"],
                            datatype=["str", "str", "str", "str", "str", "str"],
                            value=presenter.get_cooking_queue_data(),
                            interactive=False,
                            wrap=True,
                        )
                        btn_finish_cooking = gr.Button(
                            "🍽️ Nấu xong món tiếp theo (FIFO)", variant="primary"
                        )

                    # Queue 3: Chờ phục vụ
                    with gr.Column(scale=4):
                        gr.Markdown("#### 🍽️ 3. Hàng đợi Chờ Phục Vụ (Serving)")
                        queue_serving_table = gr.Dataframe(
                            headers=["STT", "Mã đơn", "Tên món", "SL", "Ghi chú", "Item ID"],
                            datatype=["str", "str", "str", "str", "str", "str"],
                            value=presenter.get_serving_queue_data(),
                            interactive=False,
                            wrap=True,
                        )
                        btn_serve_item = gr.Button(
                            "✔️ Đã phục vụ món tiếp theo (FIFO)", variant="primary"
                        )

                with gr.Row():
                    btn_refresh_all_queues = gr.Button(
                        "🔄 Làm mới tất cả Hàng đợi (3 Queues)", scale=1
                    )

                with gr.Accordion("⚡ Cập nhật theo Mã đơn / Mã món cụ thể (Tùy chọn)", open=False):
                    with gr.Row():
                        input_order_id = gr.Textbox(
                            label="Mã đơn hàng (Order ID)", placeholder="Ví dụ: ORD-..."
                        )
                        input_item_id = gr.Textbox(
                            label="Mã món (Item ID)", placeholder="Ví dụ: ITM-..."
                        )
                    with gr.Row():
                        btn_custom_ready = gr.Button("🍽️ Đã nấu xong (Chuyển sang Chờ phục vụ)")
                        btn_custom_served = gr.Button("✔️ Đã phục vụ khách")

                kitchen_feedback_md = gr.Markdown()

            # =================================================================
            # TAB 3: THANH TOÁN (PAYMENT)
            # =================================================================
            with gr.Tab("💳 3. Thanh toán đơn giản"):
                with gr.Row():
                    # Cột trái: Chọn đơn và thao tác thanh toán
                    with gr.Column(scale=6):
                        gr.Markdown("### 🧾 Chọn đơn hàng cần thanh toán")
                        payment_order_dropdown = gr.Dropdown(
                            label="Danh sách đơn chưa thanh toán (OPEN)",
                            choices=presenter.get_open_orders_choices(),
                        )
                        with gr.Row():
                            payment_discount_input = gr.Number(
                                label="Giảm giá (VNĐ)",
                                value=0,
                                precision=0,
                                minimum=0,
                            )
                            btn_load_bill = gr.Button("🔍 Tải thông tin đơn hàng", size="md")

                        payment_method_dropdown = gr.Dropdown(
                            label="Phương thức thanh toán",
                            choices=["💵 TIỀN MẶT (CASH)", "💳 CHUYỂN KHOẢN (BANKING)"],
                            value="💵 TIỀN MẶT (CASH)",
                        )

                        btn_checkout = gr.Button(
                            "💵 XÁC NHẬN THANH TOÁN ĐƠN HÀNG",
                            variant="primary",
                            size="lg",
                        )
                        payment_feedback_md = gr.Markdown()

                    # Cột phải: Xem trước chi tiết và Hóa đơn in ra
                    with gr.Column(scale=6):
                        payment_summary_md = gr.Markdown(
                            "### 🧾 Vui lòng chọn đơn hàng để xem chi tiết"
                        )
                        bill_items_table = gr.Dataframe(
                            headers=[
                                "Tên món",
                                "Số lượng",
                                "Đơn giá",
                                "Thành tiền",
                                "Trạng thái món",
                            ],
                            datatype=["str", "str", "str", "str", "str"],
                            interactive=False,
                            wrap=True,
                        )
                        receipt_output_text = gr.Textbox(
                            label="📄 Hóa đơn bán hàng (In ra sau khi thanh toán)",
                            lines=14,
                            interactive=False,
                        )

            # =================================================================
            # TAB 4: TRA CỨU HASH MAP & THỐNG KÊ (LOOKUP & SUMMARY)
            # =================================================================
            with gr.Tab("📊 4. Tra cứu (Hash Map) & Thống kê"):
                with gr.Row():
                    # Cột trái: Tra cứu Hash Map O(1)
                    with gr.Column(scale=5):
                        gr.Markdown("### 🔎 Tra cứu đơn hàng O(1) bằng Hash Map")
                        lookup_id_input = gr.Textbox(
                            label="Nhập mã đơn hàng",
                            placeholder="Ví dụ: ORD-...",
                        )
                        btn_lookup = gr.Button("🔍 Tra cứu tức thời", variant="secondary")
                        lookup_result_md = gr.Markdown()

                    # Cột phải: Báo cáo doanh thu
                    with gr.Column(scale=7):
                        gr.Markdown("### 📈 Thống kê doanh thu & Lịch sử")
                        summary_report_md = gr.Markdown()
                        btn_refresh_report = gr.Button("🔄 Cập nhật báo cáo", size="sm")

                        invoice_history_table = gr.Dataframe(
                            headers=["Mã đơn", "Thời gian", "Số món", "Tổng tiền", "Phương thức"],
                            datatype=["str", "str", "str", "str", "str"],
                            interactive=False,
                            wrap=True,
                        )

        # =====================================================================
        # BINDING SỰ KIỆN TAB 1: ĐẶT MÓN
        # =====================================================================
        btn_add_to_cart.click(
            fn=presenter.add_item_to_cart,
            inputs=[item_dropdown, qty_input, note_input, cart_state],
            outputs=[cart_state, cart_table, cart_summary_md, order_feedback_md],
        )

        def on_select_cart(evt: gr.SelectData):
            return evt.index[0] if evt and evt.index else None

        cart_table.select(
            fn=on_select_cart,
            outputs=[selected_cart_idx],
        )

        btn_qty_up.click(
            fn=lambda cart, idx: presenter.adjust_cart_item(cart, idx, 1),
            inputs=[cart_state, selected_cart_idx],
            outputs=[cart_state, cart_table, cart_summary_md, order_feedback_md],
        )

        btn_qty_down.click(
            fn=lambda cart, idx: presenter.adjust_cart_item(cart, idx, -1),
            inputs=[cart_state, selected_cart_idx],
            outputs=[cart_state, cart_table, cart_summary_md, order_feedback_md],
        )

        btn_clear_cart.click(
            fn=presenter.clear_cart,
            outputs=[cart_state, cart_table, cart_summary_md, order_feedback_md],
        )

        btn_submit_order.click(
            fn=presenter.submit_order,
            inputs=[cart_state],
            outputs=[cart_state, cart_table, cart_summary_md, order_feedback_md],
        ).then(
            # Tự động cập nhật 3 Queues và danh sách đơn thanh toán
            fn=lambda: (
                presenter.get_waiting_queue_data(),
                presenter.get_cooking_queue_data(),
                presenter.get_serving_queue_data(),
                gr.Dropdown(choices=presenter.get_open_orders_choices()),
            ),
            outputs=[
                queue_waiting_table,
                queue_cooking_table,
                queue_serving_table,
                payment_order_dropdown,
            ],
        )

        # =====================================================================
        # BINDING SỰ KIỆN TAB 2: 3 QUEUES
        # =====================================================================
        btn_start_cooking.click(
            fn=presenter.start_next_kitchen_item,
            outputs=[kitchen_feedback_md, queue_waiting_table, queue_cooking_table],
        )

        btn_finish_cooking.click(
            fn=presenter.finish_next_kitchen_item,
            outputs=[kitchen_feedback_md, queue_cooking_table, queue_serving_table],
        )

        btn_serve_item.click(
            fn=presenter.serve_next_kitchen_item,
            outputs=[kitchen_feedback_md, queue_serving_table],
        )

        btn_refresh_all_queues.click(
            fn=lambda: (
                presenter.get_waiting_queue_data(),
                presenter.get_cooking_queue_data(),
                presenter.get_serving_queue_data(),
                "🔄 Đã làm mới 3 Hàng đợi.",
            ),
            outputs=[
                queue_waiting_table,
                queue_cooking_table,
                queue_serving_table,
                kitchen_feedback_md,
            ],
        )

        btn_custom_ready.click(
            fn=lambda oid, iid: presenter.advance_kitchen_item(oid, iid, "READY"),
            inputs=[input_order_id, input_item_id],
            outputs=[
                kitchen_feedback_md,
                queue_waiting_table,
                queue_cooking_table,
                queue_serving_table,
            ],
        )

        btn_custom_served.click(
            fn=lambda oid, iid: presenter.advance_kitchen_item(oid, iid, "SERVED"),
            inputs=[input_order_id, input_item_id],
            outputs=[
                kitchen_feedback_md,
                queue_waiting_table,
                queue_cooking_table,
                queue_serving_table,
            ],
        )

        # =====================================================================
        # BINDING SỰ KIỆN TAB 3: THANH TOÁN
        # =====================================================================
        btn_load_bill.click(
            fn=presenter.load_bill_for_payment,
            inputs=[payment_order_dropdown, payment_discount_input],
            outputs=[bill_items_table, payment_summary_md, payment_feedback_md],
        )

        payment_order_dropdown.change(
            fn=presenter.load_bill_for_payment,
            inputs=[payment_order_dropdown, payment_discount_input],
            outputs=[bill_items_table, payment_summary_md, payment_feedback_md],
        )

        btn_checkout.click(
            fn=presenter.execute_checkout,
            inputs=[payment_order_dropdown, payment_method_dropdown, payment_discount_input],
            outputs=[payment_feedback_md, receipt_output_text, payment_order_dropdown],
        ).then(
            # Tự động làm mới bảng báo cáo sau khi thanh toán
            fn=presenter.get_summary_report,
            outputs=[summary_report_md, invoice_history_table],
        )

        # =====================================================================
        # BINDING SỰ KIỆN TAB 4: TRA CỨU & BÁO CÁO
        # =====================================================================
        btn_lookup.click(
            fn=presenter.lookup_order_hash,
            inputs=[lookup_id_input],
            outputs=[lookup_result_md],
        )

        btn_refresh_report.click(
            fn=presenter.get_summary_report,
            outputs=[summary_report_md, invoice_history_table],
        )

        # Khi mở ứng dụng thì nạp sẵn báo cáo
        app.load(
            fn=presenter.get_summary_report,
            outputs=[summary_report_md, invoice_history_table],
        )

    return app
