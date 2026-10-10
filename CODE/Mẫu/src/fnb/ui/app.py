"""Giao diện demo tối giản để thử backend trước khi làm UI hoàn chỉnh."""

import json

import gradio as gr

from fnb.bootstrap import AppContext
from fnb.exceptions import FNBError


def _pretty(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _safe_call(callback, *args) -> str:
    try:
        return _pretty(callback(*args))
    except (FNBError, ValueError, TypeError, KeyError) as exc:
        return _pretty({"error": str(exc)})
    except Exception as exc:  # Lớp UI cần báo lỗi thay vì làm callback im lặng thất bại.
        return _pretty({"error": f"Lỗi chưa xử lý: {exc}"})


def create_app(context: AppContext) -> gr.Blocks:
    """UI rất mỏng: nhập JSON để gọi Controller. FE có thể thay bằng form đẹp hơn."""
    with gr.Blocks(title="F&B Order System — Backend Demo") as demo:
        gr.Markdown(
            "# F&B Order System — Backend Demo\n"
            "Giao diện kỹ thuật ban đầu để nhóm thử Controller/Service/JSON. "
            "Không đặt logic nghiệp vụ tại đây."
        )
        with gr.Tab("Menu và bàn"):
            refresh_button = gr.Button("Tải menu và bàn")
            catalog_output = gr.Code(label="Menu + Bàn (JSON)", language="json")
            refresh_button.click(
                fn=lambda: _pretty({
                    "menu": context.menu_controller.list_menu(),
                    "tables": context.table_controller.list_tables(),
                }),
                outputs=catalog_output,
            )

        with gr.Tab("Tạo đơn"):
            table_id = gr.Textbox(label="Mã bàn", value="TBL-01")
            lines_json = gr.Code(
                label="Các dòng món (JSON list)",
                language="json",
                value='[\n  {"menu_item_id": "MI-001", "quantity": 2, "note": ""}\n]',
            )
            create_button = gr.Button("Tạo đơn")
            order_output = gr.Code(label="Kết quả tạo đơn", language="json")

            def create_order_from_json(chosen_table: str, raw_lines: str) -> str:
                try:
                    lines = json.loads(raw_lines or "[]")
                except json.JSONDecodeError as exc:
                    return _pretty({"error": f"JSON không hợp lệ: {exc}"})
                return _safe_call(context.order_controller.create_order, chosen_table, lines)

            create_button.click(
                fn=create_order_from_json,
                inputs=[table_id, lines_json],
                outputs=order_output,
            )

        with gr.Tab("Bếp / Queue"):
            queue_button = gr.Button("Xem Queue")
            queue_output = gr.Code(label="Queue FIFO", language="json")
            queue_button.click(
                fn=lambda: _pretty(context.kitchen_controller.get_queue()),
                outputs=queue_output,
            )
            start_button = gr.Button("Bắt đầu món tiếp theo")
            start_output = gr.Code(label="Món vừa nhận", language="json")
            start_button.click(
                fn=lambda: _safe_call(context.kitchen_controller.start_next_item),
                outputs=start_output,
            )
            ready_order_id = gr.Textbox(label="Order ID để đánh dấu READY")
            ready_item_id = gr.Textbox(label="Order Item ID để đánh dấu READY")
            ready_button = gr.Button("Đánh dấu READY")
            ready_output = gr.Code(label="Kết quả READY", language="json")
            ready_button.click(
                fn=lambda oid, iid: _safe_call(
                    context.kitchen_controller.mark_item_ready, oid, iid
                ),
                inputs=[ready_order_id, ready_item_id],
                outputs=ready_output,
            )
            served_button = gr.Button("Đánh dấu SERVED")
            served_output = gr.Code(label="Kết quả SERVED", language="json")
            served_button.click(
                fn=lambda oid, iid: _safe_call(
                    context.kitchen_controller.mark_item_served, oid, iid
                ),
                inputs=[ready_order_id, ready_item_id],
                outputs=served_output,
            )

        with gr.Tab("Thanh toán / Báo cáo"):
            checkout_order_id = gr.Textbox(label="Order ID cần thanh toán")
            checkout_button = gr.Button("Checkout (mô phỏng)")
            checkout_output = gr.Code(label="Hóa đơn / trạng thái đơn", language="json")
            checkout_button.click(
                fn=lambda oid: _safe_call(context.payment_controller.checkout, oid),
                inputs=checkout_order_id,
                outputs=checkout_output,
            )
            report_day = gr.Textbox(label="Ngày báo cáo YYYY-MM-DD (để trống = hôm nay)")
            report_button = gr.Button("Xem doanh thu")
            report_output = gr.Code(label="Báo cáo ngày", language="json")
            report_button.click(
                fn=lambda day: _safe_call(
                    context.report_controller.daily_summary, day.strip() or None
                ),
                inputs=report_day,
                outputs=report_output,
            )

    return demo
