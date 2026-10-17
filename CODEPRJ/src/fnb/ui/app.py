"""Giao diện Gradio F&B chuyên nghiệp, sạch sẽ theo mô hình MVC/MVP.

Toàn bộ UI View và UI Logic được phân tách độc lập hoàn toàn.
100% sử dụng Gradio Native Components, không sử dụng HTML/CSS thuần túy.
"""

from datetime import date, timedelta

import gradio as gr

from fnb.bootstrap import AppContext
from fnb.ui.presenter import FnbPresenter
from fnb.ui.views import (
    build_invoice_view,
    build_order_view,
    build_payment_view,
    build_table_view,
)


def create_app(context: AppContext) -> gr.Blocks:
    """Khởi tạo giao diện ứng dụng quản lý nhà hàng F&B."""
    presenter = FnbPresenter(context)

    with gr.Blocks(title="F&B Order Management System") as app:
        gr.Markdown("# 🍽️ HỆ THỐNG QUẢN LÝ NHÀ HÀNG & QUÁN ĂN (F&B POS)")

        with gr.Tabs():
            with gr.Tab("🛒 1. Đặt món (Order)"):
                order_view = build_order_view(presenter)

            with gr.Tab("🪑 2. Sơ đồ bàn & Phục vụ (Tables & Kitchen)"):
                table_view = build_table_view(presenter)

            with gr.Tab("💳 3. Thanh toán (Payment)"):
                payment_view = build_payment_view(presenter)

            with gr.Tab("📑 4. Hóa đơn & Báo cáo (Invoices)"):
                invoice_view = build_invoice_view(presenter)

        # =====================================================================
        # BINDING SỰ KIỆN: 1. MÀN HÌNH ORDER (ĐẶT MÓN & GIỎ HÀNG)
        # =====================================================================
        order_view.btn_quick_add.click(
            fn=presenter.add_item_to_cart,
            inputs=[
                order_view.quick_menu_dropdown,
                order_view.quantity_input,
                order_view.note_input,
                order_view.cart_state,
            ],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary_md,
                order_view.order_feedback_md,
            ],
        )

        for btn, item in order_view.menu_buttons:
            btn.click(
                fn=lambda qty, note, cart, iid=item["id"]: presenter.add_item_to_cart(
                    iid, qty, note, cart
                ),
                inputs=[
                    order_view.quantity_input,
                    order_view.note_input,
                    order_view.cart_state,
                ],
                outputs=[
                    order_view.cart_state,
                    order_view.cart_table,
                    order_view.cart_summary_md,
                    order_view.order_feedback_md,
                ],
            )

        def on_select_cart(evt: gr.SelectData):
            return evt.index[0] if evt and evt.index else None

        order_view.cart_table.select(
            fn=on_select_cart,
            outputs=[order_view.selected_cart_idx],
        )

        order_view.btn_qty_up.click(
            fn=lambda cart, idx: presenter.adjust_cart_item(cart, idx, 1),
            inputs=[order_view.cart_state, order_view.selected_cart_idx],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary_md,
                order_view.order_feedback_md,
            ],
        )

        order_view.btn_qty_down.click(
            fn=lambda cart, idx: presenter.adjust_cart_item(cart, idx, -1),
            inputs=[order_view.cart_state, order_view.selected_cart_idx],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary_md,
                order_view.order_feedback_md,
            ],
        )

        order_view.btn_remove_item.click(
            fn=presenter.remove_selected_cart_item,
            inputs=[order_view.cart_state, order_view.selected_cart_idx],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary_md,
                order_view.order_feedback_md,
            ],
        )

        order_view.btn_clear_cart.click(
            fn=presenter.clear_cart,
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary_md,
                order_view.order_feedback_md,
            ],
        )

        def handle_submit_order(cart, table_id):
            new_cart, rows, summary, msg = presenter.submit_order(cart, table_id)
            tables_data = presenter.get_tables_table_data()
            kitchen_data = presenter.get_kitchen_queue_data()
            unpaid_choices = presenter.get_unpaid_order_choices()
            return (
                new_cart,
                rows,
                summary,
                msg,
                tables_data,
                kitchen_data,
                gr.update(choices=unpaid_choices),
            )

        order_view.btn_submit_order.click(
            fn=handle_submit_order,
            inputs=[order_view.cart_state, order_view.table_select_dropdown],
            outputs=[
                order_view.cart_state,
                order_view.cart_table,
                order_view.cart_summary_md,
                order_view.order_feedback_md,
                table_view.tables_dataframe,
                table_view.kitchen_queue_table,
                payment_view.order_select_dropdown,
            ],
        )

        # =====================================================================
        # BINDING SỰ KIỆN: 2. MÀN HÌNH PHỤC VỤ (SƠ ĐỒ BÀN & BẾP FIFO)
        # =====================================================================
        for btn, t_id in table_view.table_buttons:
            btn.click(
                fn=lambda tid=t_id: (tid, presenter.get_table_details_markdown(tid)),
                outputs=[table_view.selected_table_id, table_view.table_details_md],
            )

        table_view.btn_refresh_tables.click(
            fn=lambda tid: (
                presenter.get_tables_table_data(),
                presenter.get_table_details_markdown(tid),
            ),
            inputs=[table_view.selected_table_id],
            outputs=[table_view.tables_dataframe, table_view.table_details_md],
        )

        table_view.btn_mark_served.click(
            fn=presenter.mark_all_served_for_table,
            inputs=[table_view.selected_table_id],
            outputs=[
                table_view.table_feedback_md,
                table_view.table_details_md,
                table_view.tables_dataframe,
            ],
        )

        table_view.btn_transfer.click(
            fn=presenter.transfer_table,
            inputs=[
                table_view.transfer_from_dropdown,
                table_view.transfer_to_dropdown,
            ],
            outputs=[table_view.table_feedback_md, table_view.tables_dataframe],
        )

        table_view.btn_merge.click(
            fn=presenter.merge_tables,
            inputs=[
                table_view.merge_from_dropdown,
                table_view.merge_to_dropdown,
            ],
            outputs=[table_view.table_feedback_md, table_view.tables_dataframe],
        )

        table_view.btn_start_next_item.click(
            fn=presenter.start_next_kitchen_item,
            outputs=[table_view.kitchen_feedback_md, table_view.kitchen_queue_table],
        )

        table_view.btn_refresh_kitchen.click(
            fn=presenter.get_kitchen_queue_data,
            outputs=[table_view.kitchen_queue_table],
        )

        table_view.btn_mark_ready.click(
            fn=lambda oid, iid: presenter.advance_kitchen_item(oid, iid, "READY"),
            inputs=[
                table_view.kitchen_order_id_input,
                table_view.kitchen_item_id_input,
            ],
            outputs=[table_view.kitchen_feedback_md, table_view.kitchen_queue_table],
        )

        table_view.btn_mark_served_item.click(
            fn=lambda oid, iid: presenter.advance_kitchen_item(oid, iid, "SERVED"),
            inputs=[
                table_view.kitchen_order_id_input,
                table_view.kitchen_item_id_input,
            ],
            outputs=[table_view.kitchen_feedback_md, table_view.kitchen_queue_table],
        )

        def on_select_kitchen(evt: gr.SelectData):
            if evt and evt.index:
                return presenter.select_kitchen_item_by_row(evt.index[0])
            return ("", "")

        table_view.kitchen_queue_table.select(
            fn=on_select_kitchen,
            outputs=[
                table_view.kitchen_order_id_input,
                table_view.kitchen_item_id_input,
            ],
        )

        # =====================================================================
        # BINDING SỰ KIỆN: 3. MÀN HÌNH THANH TOÁN (BILLING & CASHIER)
        # =====================================================================
        payment_view.order_select_dropdown.change(
            fn=presenter.load_bill_for_payment,
            inputs=[payment_view.order_select_dropdown],
            outputs=[
                payment_view.bill_items_table,
                payment_view.total_due_md,
                payment_view.checkout_feedback_md,
            ],
        )

        payment_view.btn_refresh_unpaid.click(
            fn=lambda: gr.update(choices=presenter.get_unpaid_order_choices()),
            outputs=[payment_view.order_select_dropdown],
        )

        def handle_checkout(order_id, method, current_date):
            msg, receipt, choices = presenter.execute_checkout(order_id, method)
            tables_data = presenter.get_tables_table_data()
            invoices_data, kpi_md = presenter.get_invoice_history(current_date)
            return (
                msg,
                receipt,
                gr.update(choices=choices, value=None),
                tables_data,
                invoices_data,
                kpi_md,
            )

        payment_view.btn_checkout.click(
            fn=handle_checkout,
            inputs=[
                payment_view.order_select_dropdown,
                payment_view.payment_method_radio,
                invoice_view.date_input,
            ],
            outputs=[
                payment_view.checkout_feedback_md,
                payment_view.receipt_preview_md,
                payment_view.order_select_dropdown,
                table_view.tables_dataframe,
                invoice_view.invoices_table,
                invoice_view.kpi_summary_md,
            ],
        )

        # =====================================================================
        # BINDING SỰ KIỆN: 4. MÀN HÌNH HÓA ĐƠN & BÁO CÁO (INVOICES & PREVIEW)
        # =====================================================================
        invoice_view.btn_today.click(
            fn=lambda: (
                date.today().isoformat(),
                *presenter.get_invoice_history(date.today().isoformat()),
            ),
            outputs=[
                invoice_view.date_input,
                invoice_view.invoices_table,
                invoice_view.kpi_summary_md,
            ],
        )

        invoice_view.btn_yesterday.click(
            fn=lambda: (
                (date.today() - timedelta(days=1)).isoformat(),
                *presenter.get_invoice_history(
                    (date.today() - timedelta(days=1)).isoformat()
                ),
            ),
            outputs=[
                invoice_view.date_input,
                invoice_view.invoices_table,
                invoice_view.kpi_summary_md,
            ],
        )

        invoice_view.btn_load_history.click(
            fn=presenter.get_invoice_history,
            inputs=[invoice_view.date_input],
            outputs=[invoice_view.invoices_table, invoice_view.kpi_summary_md],
        )

        invoice_view.btn_preview_receipt.click(
            fn=presenter.get_invoice_preview,
            inputs=[invoice_view.order_id_preview_input],
            outputs=[invoice_view.receipt_preview_display],
        )

        def on_select_invoice(dt: str, evt: gr.SelectData):
            if evt and evt.index:
                return presenter.select_invoice_by_index(dt, evt.index[0])
            return ("", "")

        invoice_view.invoices_table.select(
            fn=on_select_invoice,
            inputs=[invoice_view.date_input],
            outputs=[
                invoice_view.order_id_preview_input,
                invoice_view.receipt_preview_display,
            ],
        )

    return app
