"""Giao diện demo mỏng: mọi quy tắc nghiệp vụ nằm phía Backend."""

import json
import logging

import gradio as gr

from fnb.bootstrap import AppContext
from fnb.exceptions import FNBError, StorageError


def _pretty(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _safe_call(callback, *args) -> str:
    try:
        return _pretty(callback(*args))
    except StorageError:
        logging.exception("Không thể đọc/ghi dữ liệu trong callback Gradio.")
        return _pretty(
            {"error": "Không thể đọc/ghi dữ liệu. Hãy nhờ nhóm kiểm tra file JSON."}
        )
    except (FNBError, ValueError, TypeError, KeyError) as exc:
        return _pretty({"error": str(exc)})
    except Exception:
        # Ghi chi tiết ở terminal, chỉ đưa thông báo chung ra giao diện.
        logging.exception("Lỗi chưa xử lý trong callback Gradio.")
        return _pretty(
            {"error": "Có lỗi chưa xử lý. Hãy kiểm tra terminal để chẩn đoán."}
        )


def _parse_lines(raw_lines: str) -> list[dict]:
    try:
        lines = json.loads(raw_lines or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Danh sách món không phải JSON hợp lệ: {exc.msg}.") from exc
    if not isinstance(lines, list):
        raise ValueError("Danh sách món phải là một JSON array.")
    return lines


def _parse_discount(raw_discount: str) -> int:
    try:
        value = int(raw_discount.strip() or "0")
    except ValueError as exc:
        raise ValueError("Giảm giá phải là số nguyên VND.") from exc
    if value < 0:
        raise ValueError("Giảm giá không được âm.")
    return value


def create_app(context: AppContext) -> gr.Blocks:
    with gr.Blocks(title="F&B Order System — Backend-first") as demo:
        gr.Markdown(
            "# Hệ thống quản lý đơn hàng F&B\n"
            "Backend-first: thực đơn → đơn hàng → Queue bếp → thanh toán. "
            "Không triển khai nghiệp vụ quản lý bàn ăn."
        )

        with gr.Tab("Thực đơn"):
            refresh_menu = gr.Button("Tải thực đơn còn bán")
            menu_output = gr.Code(label="Thực đơn", language="json")
            refresh_menu.click(
                fn=lambda: _pretty(context.menu_controller.list_menu()), outputs=menu_output
            )
            menu_code = gr.Textbox(label="Mã món cần tra cứu", placeholder="MI-001")
            lookup_menu = gr.Button("Tra cứu món")
            lookup_output = gr.Code(label="Kết quả tra cứu", language="json")
            lookup_menu.click(
                fn=lambda item_id: _safe_call(context.menu_controller.get_item, item_id.strip()),
                inputs=menu_code,
                outputs=lookup_output,
            )

        with gr.Tab("Tạo đơn / Thêm món"):
            lines_json = gr.Code(
                label="Danh sách dòng món (JSON)",
                language="json",
                value='[\n  {"menu_item_id": "MI-001", "quantity": 2, "note": ""}\n]',
            )
            create_button = gr.Button("Tạo đơn")
            create_output = gr.Code(label="Đơn vừa tạo", language="json")

            def create_order(raw_lines: str) -> str:
                try:
                    lines = _parse_lines(raw_lines)
                except ValueError as exc:
                    return _pretty({"error": str(exc)})
                return _safe_call(context.order_controller.create_order, lines)

            create_button.click(fn=create_order, inputs=lines_json, outputs=create_output)

            gr.Markdown("### Thêm món vào đơn đang mở")
            add_order_id = gr.Textbox(label="Mã đơn đang OPEN")
            add_lines_json = gr.Code(
                label="Các món bổ sung (JSON)",
                language="json",
                value='[\n  {"menu_item_id": "MI-008", "quantity": 1, "note": ""}\n]',
            )
            add_button = gr.Button("Thêm món")
            add_output = gr.Code(label="Đơn sau khi thêm món", language="json")

            def add_items(order_id: str, raw_lines: str) -> str:
                try:
                    lines = _parse_lines(raw_lines)
                except ValueError as exc:
                    return _pretty({"error": str(exc)})
                return _safe_call(context.order_controller.add_items, order_id.strip(), lines)

            add_button.click(
                fn=add_items,
                inputs=[add_order_id, add_lines_json],
                outputs=add_output,
            )

            list_orders_button = gr.Button("Tải toàn bộ đơn hàng")
            orders_output = gr.Code(label="Lịch sử đơn", language="json")
            list_orders_button.click(
                fn=lambda: _pretty(context.order_controller.list_orders()),
                outputs=orders_output,
            )

            gr.Markdown("### Hủy đơn (chỉ khi mọi món còn QUEUED)")
            cancel_order_id = gr.Textbox(label="Mã đơn cần hủy")
            cancel_reason = gr.Textbox(label="Lý do hủy (không bắt buộc)")
            cancel_button = gr.Button("Hủy đơn")
            cancel_output = gr.Code(label="Kết quả hủy đơn", language="json")
            cancel_button.click(
                fn=lambda oid, reason: _safe_call(
                    context.order_controller.cancel_order, oid.strip(), reason
                ),
                inputs=[cancel_order_id, cancel_reason],
                outputs=cancel_output,
            )

        with gr.Tab("Bếp / Queue FIFO"):
            get_queue = gr.Button("Xem hàng đợi")
            queue_output = gr.Code(label="Món đang chờ", language="json")
            get_queue.click(
                fn=lambda: _pretty(context.kitchen_controller.get_queue()),
                outputs=queue_output,
            )
            start_next = gr.Button("Nhận món tiếp theo (QUEUED → PREPARING)")
            start_output = gr.Code(label="Món vừa nhận", language="json")
            start_next.click(
                fn=lambda: _safe_call(context.kitchen_controller.start_next_item),
                outputs=start_output,
            )
            kitchen_order_id = gr.Textbox(label="Mã đơn")
            kitchen_item_id = gr.Textbox(label="Mã dòng món (order_item_id)")
            ready_button = gr.Button("Đánh dấu READY")
            ready_output = gr.Code(label="Kết quả READY", language="json")
            ready_button.click(
                fn=lambda oid, iid: _safe_call(
                    context.kitchen_controller.mark_item_ready, oid.strip(), iid.strip()
                ),
                inputs=[kitchen_order_id, kitchen_item_id],
                outputs=ready_output,
            )
            served_button = gr.Button("Đánh dấu SERVED")
            served_output = gr.Code(label="Kết quả SERVED", language="json")
            served_button.click(
                fn=lambda oid, iid: _safe_call(
                    context.kitchen_controller.mark_item_served, oid.strip(), iid.strip()
                ),
                inputs=[kitchen_order_id, kitchen_item_id],
                outputs=served_output,
            )

        with gr.Tab("Hóa đơn / Thanh toán"):
            payment_order_id = gr.Textbox(label="Mã đơn cần xem hóa đơn / thanh toán")
            discount = gr.Textbox(label="Giảm giá (VND, số nguyên)", value="0")
            preview_button = gr.Button("Xem trước hóa đơn")
            preview_output = gr.Code(label="Hóa đơn", language="json")

            def preview(order_id: str, raw_discount: str) -> str:
                try:
                    amount = _parse_discount(raw_discount)
                except ValueError as exc:
                    return _pretty({"error": str(exc)})
                return _safe_call(
                    context.payment_controller.preview_bill, order_id.strip(), amount
                )

            preview_button.click(
                fn=preview,
                inputs=[payment_order_id, discount],
                outputs=preview_output,
            )
            payment_method = gr.Dropdown(
                label="Phương thức thanh toán mô phỏng",
                choices=["CASH", "CARD", "TRANSFER"],
                value="CASH",
            )
            checkout_button = gr.Button("Xác nhận thanh toán")
            checkout_output = gr.Code(label="Biên nhận", language="json")

            def checkout(order_id: str, method: str, raw_discount: str) -> str:
                try:
                    amount = _parse_discount(raw_discount)
                except ValueError as exc:
                    return _pretty({"error": str(exc)})
                return _safe_call(
                    context.payment_controller.checkout,
                    order_id.strip(),
                    method,
                    amount,
                )

            checkout_button.click(
                fn=checkout,
                inputs=[payment_order_id, payment_method, discount],
                outputs=checkout_output,
            )

        with gr.Tab("Báo cáo ngày"):
            report_day = gr.Textbox(
                label="Ngày YYYY-MM-DD (để trống = hôm nay)", placeholder="2026-10-14"
            )
            report_button = gr.Button("Xem doanh thu ngày")
            report_output = gr.Code(label="Báo cáo", language="json")
            report_button.click(
                fn=lambda day: _safe_call(
                    context.report_controller.daily_summary, day.strip() or None
                ),
                inputs=report_day,
                outputs=report_output,
            )

    return demo
