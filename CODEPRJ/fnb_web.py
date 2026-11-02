"""HỆ THỐNG QUẢN LÝ ĐƠN HÀNG NHÀ HÀNG (F&B) - GIAO DIỆN WEB GRADIO ĐƠN GIẢN.

Dành cho người mới bắt đầu học Lập trình & Cấu trúc dữ liệu.
Cấu trúc dữ liệu chính:
1. DICT (Bảng băm / Hash Map): Tra cứu Menu và Đơn hàng tức thì O(1).
2. QUEUE (Hàng đợi FIFO - collections.deque): Bếp chế biến theo thứ tự ai gọi trước nấu trước O(1).
"""

from collections import deque
from datetime import datetime
import gradio as gr

# ==============================================================================
# 1. DỮ LIỆU IN-MEMORY (LƯU TRONG BỘ NHỚ RAM)
# ==============================================================================

# THỰC ĐƠN: Dùng DICT (Hash Map) với Key là mã món -> Tra cứu O(1)
MENU = {
    "M01": {"ten": "Cơm gà xối mỡ", "gia": 45000, "loai": "Món chính"},
    "M02": {"ten": "Phở bò tái nạm", "gia": 50000, "loai": "Món chính"},
    "M03": {"ten": "Bún chả Hà Nội", "gia": 40000, "loai": "Món chính"},
    "M04": {"ten": "Trà đào cam sả", "gia": 25000, "loai": "Đồ uống"},
    "M05": {"ten": "Cà phê sữa đá", "gia": 20000, "loai": "Đồ uống"},
}

# HÀNG ĐỢI BẾP: Dùng collections.deque theo nguyên lý FIFO (First-In, First-Out)
# Thao tác thêm vào cuối: append() -> O(1)
# Thao tác lấy ra ở đầu: popleft() -> O(1)
KITCHEN_QUEUE = deque()

# QUẢN LÝ ĐƠN HÀNG: Dùng DICT với Key là mã đơn (ORD001, ORD002...) -> Tra cứu O(1)
ORDERS = {}

# Biến đếm sinh mã đơn tự động
order_counter = 1


# ==============================================================================
# 2. HÀM TIỆN ÍCH DỮ LIỆU CHO GIAO DIỆN WEB
# ==============================================================================

def lay_bang_menu():
    """Chuyển đổi DICT MENU thành dạng bảng (list of lists) cho Dataframe."""
    return [
        [ma, thong_tin["ten"], thong_tin["loai"], f"{thong_tin['gia']:,} đ"]
        for ma, thong_tin in MENU.items()
    ]


def lay_danh_sach_lua_chon_mon():
    """Tạo danh sách lựa chọn cho Dropdown món ăn: ['M01 - Cơm gà xối mỡ (45,000 đ)', ...]."""
    return [
        f"{ma} - {thong_tin['ten']} ({thong_tin['gia']:,} đ)"
        for ma, thong_tin in MENU.items()
    ]


def lay_bang_hang_doi():
    """Chuyển đổi KITCHEN_QUEUE thành dạng bảng cho Dataframe."""
    if not KITCHEN_QUEUE:
        return []
    return [
        [idx, item["ma_don"], item["ten_mon"], item["so_luong"], item["ghi_chu"] or "-"]
        for idx, item in enumerate(KITCHEN_QUEUE, start=1)
    ]


def lay_danh_sach_don_cho_thanh_toan():
    """Lấy danh sách các đơn chưa thanh toán (OPEN) để đưa vào Dropdown."""
    ds = []
    for ma, don in ORDERS.items():
        if don["trang_thai"] == "OPEN":
            so_mon = len(don["danh_sach_mon"])
            da_xong = sum(1 for m in don["danh_sach_mon"] if m["trang_thai"] == "DA_XONG")
            tt_bep = "Bếp đã nấu xong" if da_xong == so_mon else f"Bếp xong {da_xong}/{so_mon} món"
            ds.append(f"{ma} - {so_mon} món ({don['tong_tien']:,} đ) [{tt_bep}]")
    return ds


# ==============================================================================
# 3. HÀM XỬ LÝ SỰ KIỆN GIAO DIỆN (EVENT HANDLERS)
# ==============================================================================

# --- TAB 1: ĐẶT MÓN & TẠO ĐƠN ---

def them_mon_vao_gio(mon_duoc_chon, so_luong, ghi_chu, gio_hang_hien_tai):
    """Thêm một món ăn vào giỏ hàng tạm (chưa gửi xuống bếp)."""
    if not mon_duoc_chon:
        return gio_hang_hien_tai, [], "⚠️ Vui lòng chọn một món ăn từ danh sách!"

    # Tách mã món từ chuỗi "M01 - Cơm gà xối mỡ..."
    ma_mon = mon_duoc_chon.split(" - ")[0].strip()

    # Tra cứu trong DICT MENU -> O(1)
    if ma_mon not in MENU:
        return gio_hang_hien_tai, [], "❌ Món ăn không hợp lệ!"

    if so_luong is None or so_luong <= 0:
        return gio_hang_hien_tai, [], "⚠️ Số lượng món phải lớn hơn 0!"

    gio = list(gio_hang_hien_tai) if gio_hang_hien_tai else []
    mon_moi = {
        "ma_mon": ma_mon,
        "ten_mon": MENU[ma_mon]["ten"],
        "don_gia": MENU[ma_mon]["gia"],
        "so_luong": int(so_luong),
        "ghi_chu": ghi_chu.strip() if ghi_chu else "",
        "trang_thai": "CHO_NAU"
    }
    gio.append(mon_moi)

    # Bảng hiển thị giỏ hàng
    bang_gio = [
        [idx, m["ma_mon"], m["ten_mon"], m["so_luong"], f"{m['don_gia'] * m['so_luong']:,} đ", m["ghi_chu"] or "-"]
        for idx, m in enumerate(gio, start=1)
    ]
    thong_bao = f"✔️ Đã thêm [{mon_moi['ten_mon']}] (SL: {so_luong}) vào giỏ hàng."
    return gio, bang_gio, thong_bao


def xoa_gio_hang():
    """Xóa toàn bộ món trong giỏ hàng tạm."""
    return [], [], "🗑️ Đã làm trống giỏ hàng."


def xac_nhan_tao_don(gio_hang_hien_tai):
    """Xác nhận đơn hàng, lưu vào ORDERS (dict), đẩy món vào KITCHEN_QUEUE (FIFO) và cập nhật Dropdown thanh toán."""
    global order_counter

    if not gio_hang_hien_tai:
        return [], [], lay_bang_hang_doi(), "⚠️ Giỏ hàng đang trống! Vui lòng thêm món trước.", gr.update()

    ma_don = f"ORD{order_counter:03d}"
    order_counter += 1

    ds_mon = list(gio_hang_hien_tai)
    tong_tien = sum(m["don_gia"] * m["so_luong"] for m in ds_mon)

    # Lưu đơn hàng vào DICT ORDERS -> O(1)
    ORDERS[ma_don] = {
        "ma_don": ma_don,
        "thoi_gian": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
        "danh_sach_mon": ds_mon,
        "trang_thai": "OPEN",
        "tong_tien": tong_tien,
        "giam_gia": 0,
        "thanh_toan": 0
    }

    # ĐẨY TỪNG MÓN VÀO HÀNG ĐỢI BẾP (ENQUEUE / FIFO O(1))
    for mon in ds_mon:
        task_bep = {
            "ma_don": ma_don,
            "ten_mon": mon["ten_mon"],
            "so_luong": mon["so_luong"],
            "ghi_chu": mon["ghi_chu"],
            "ref_mon": mon  # Giữ tham chiếu để cập nhật trạng thái món khi bếp nấu xong
        }
        KITCHEN_QUEUE.append(task_bep)

    thong_bao = (
        f"🎉 **TẠO ĐƠN THÀNH CÔNG: [{ma_don}]**\n\n"
        f"• Tổng tiền: **{tong_tien:,} đ**\n"
        f"• Số món gửi xuống bếp: **{len(ds_mon)} món**\n"
        f"• Hiện có **{len(KITCHEN_QUEUE)}** món đang chờ trong hàng đợi bếp."
    )

    # Cập nhật danh sách đơn chờ thanh toán cho Dropdown ở Tab 3
    ds_don_moi = lay_danh_sach_don_cho_thanh_toan()

    return [], [], lay_bang_hang_doi(), thong_bao, gr.update(choices=ds_don_moi, value=ds_don_moi[-1] if ds_don_moi else None)


# --- TAB 2: BẾP & HÀNG ĐỢI FIFO ---

def bep_nau_mon_tiep_theo():
    """Lấy phần tử đầu tiên trong Queue ra nấu (DEQUEUE FIFO O(1))."""
    if len(KITCHEN_QUEUE) == 0:
        return lay_bang_hang_doi(), "🟢 Hàng đợi rỗng! Hiện tại bếp không có món nào cần nấu.", gr.update()

    # DEQUEUE O(1) bằng popleft()
    mon_can_nau = KITCHEN_QUEUE.popleft()

    # Cập nhật trạng thái của món trong đơn hàng thành ĐÃ XONG
    mon_can_nau["ref_mon"]["trang_thai"] = "DA_XONG"

    ghi_chu_txt = f" (Ghi chú: {mon_can_nau['ghi_chu']})" if mon_can_nau["ghi_chu"] else ""
    thong_bao = (
        f"👨‍🍳 **BẾP ĐÃ NẤU XONG:** [{mon_can_nau['ten_mon']}] x {mon_can_nau['so_luong']}{ghi_chu_txt}\n\n"
        f"• Thuộc đơn hàng: **{mon_can_nau['ma_don']}**\n"
        f"• Trạng thái món: **ĐÃ SẴN SÀNG PHỤC VỤ (DA_XONG)**\n"
        f"• Còn lại trong hàng đợi bếp: **{len(KITCHEN_QUEUE)} món**"
    )

    # Đồng thời cập nhật trạng thái trong Dropdown đơn hàng thanh toán
    ds_don_cap_nhat = lay_danh_sach_don_cho_thanh_toan()
    return lay_bang_hang_doi(), thong_bao, gr.update(choices=ds_don_cap_nhat)


# --- TAB 3: THANH TOÁN & HÓA ĐƠN ---

def khi_chon_don_thanh_toan(don_duoc_chon):
    """Khi người dùng chọn một đơn từ Dropdown, tự động hiển thị chi tiết hóa đơn (Tra cứu O(1))."""
    if not don_duoc_chon:
        return [], "*(Chưa chọn đơn hàng nào)*", "", ""

    ma_don = don_duoc_chon.split(" - ")[0].strip()
    if ma_don not in ORDERS:
        return [], "❌ Không tìm thấy mã đơn hàng!", "", ""

    don = ORDERS[ma_don]
    bang_chi_tiet = [
        [
            m["ten_mon"],
            m["so_luong"],
            f"{m['don_gia']:,} đ",
            f"{m['don_gia'] * m['so_luong']:,} đ",
            "✔️ Đã xong" if m["trang_thai"] == "DA_XONG" else "⏳ Chờ nấu"
        ]
        for m in don["danh_sach_mon"]
    ]

    so_mon = len(don["danh_sach_mon"])
    da_xong = sum(1 for m in don["danh_sach_mon"] if m["trang_thai"] == "DA_XONG")
    canh_bao = ""
    if da_xong < so_mon:
        canh_bao = f"⚠️ Lưu ý: Đơn này vẫn còn {so_mon - da_xong} món đang chờ bếp nấu!"

    thong_tin = (
        f"### 📋 Chi tiết đơn hàng: **{ma_don}**\n"
        f"- Thời gian đặt: **{don['thoi_gian']}**\n"
        f"- Trạng thái chế biến: **{da_xong}/{so_mon} món đã xong**\n"
        f"- Tổng tiền thanh toán: **{don['tong_tien']:,} đ**"
    )
    return bang_chi_tiet, thong_tin, canh_bao, ""


def thanh_toan_hoa_don(don_duoc_chon, giam_gia):
    """Thanh toán đơn hàng đã chọn từ Dropdown, cập nhật trạng thái PAID."""
    if not don_duoc_chon:
        return "", "⚠️ Vui lòng chọn một đơn hàng từ danh sách!", gr.update()

    ma_don = don_duoc_chon.split(" - ")[0].strip()
    if ma_don not in ORDERS:
        return "", "❌ Không tìm thấy mã đơn hàng!", gr.update()

    don = ORDERS[ma_don]
    if don["trang_thai"] == "PAID":
        return "", f"⚠️ Đơn [{ma_don}] đã được thanh toán trước đó!", gr.update()

    giam = int(giam_gia) if giam_gia and giam_gia > 0 else 0
    if giam > don["tong_tien"]:
        return "", "❌ Số tiền giảm giá không được lớn hơn tổng tiền!", gr.update()

    thuc_thu = don["tong_tien"] - giam
    don["giam_gia"] = giam
    don["thanh_toan"] = thuc_thu
    don["trang_thai"] = "PAID"
    don["thoi_gian_tra"] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    hoa_don_md = (
        f"## 🧾 BIÊN LAI THANH TOÁN HỢP LỆ\n"
        f"**Mã đơn hàng:** {ma_don}  \n"
        f"**Thời gian thanh toán:** {don['thoi_gian_tra']}  \n\n"
        f"| Tên món | SL | Đơn giá | Thành tiền |\n"
        f"| :--- | :---: | :---: | :---: |\n"
    )
    for m in don["danh_sach_mon"]:
        hoa_don_md += f"| {m['ten_mon']} | {m['so_luong']} | {m['don_gia']:,} đ | {m['don_gia'] * m['so_luong']:,} đ |\n"

    hoa_don_md += (
        f"\n**Tổng tiền gốc:** {don['tong_tien']:,} đ  \n"
        f"**Giảm giá:** -{giam:,} đ  \n"
        f"### 👉 SỐ TIỀN THỰC THU: {thuc_thu:,} đ\n\n"
        f"*(Cảm ơn quý khách và hẹn gặp lại!)*"
    )

    # Cập nhật lại dropdown: loại bỏ đơn vừa thanh toán
    ds_con_lai = lay_danh_sach_don_cho_thanh_toan()
    val_moi = ds_con_lai[0] if ds_con_lai else None

    return hoa_don_md, f"🎉 Đơn [{ma_don}] đã thanh toán thành công: {thuc_thu:,} đ", gr.update(choices=ds_con_lai, value=val_moi)


# ==============================================================================
# 4. THIẾT KẾ GIAO DIỆN WEB VỚI GRADIO BLOCKS
# ==============================================================================

def tao_giao_dien_web():
    with gr.Blocks(title="F&B Simple Order System") as demo:
        gr.Markdown(
            """
            # 🍽️ HỆ THỐNG QUẢN LÝ ĐƠN HÀNG NHÀ HÀNG (F&B)
            *Giao diện Web trực quan - Sử dụng Cấu trúc Dữ liệu: **Bảng băm (Dict O(1))** & **Hàng đợi Bếp (Queue FIFO O(1))***
            """
        )

        with gr.Tabs():
            # ------------------------------------------------------------------
            # TAB 1: ĐẶT MÓN & TẠO ĐƠN HÀNG
            # ------------------------------------------------------------------
            with gr.Tab("🛒 1. Đặt món (Tạo đơn hàng)"):
                with gr.Row():
                    # Cột trái: Thực đơn
                    with gr.Column(scale=5):
                        gr.Markdown("### 📋 Thực đơn quán ăn (Tra cứu O(1))")
                        gr.Dataframe(
                            headers=["Mã", "Tên món", "Loại", "Đơn giá"],
                            value=lay_bang_menu(),
                            interactive=False,
                            wrap=True
                        )

                    # Cột phải: Chọn món & Giỏ hàng
                    with gr.Column(scale=7):
                        gr.Markdown("### ➕ Thêm món vào đơn")
                        mon_input = gr.Dropdown(
                            label="Chọn món ăn",
                            choices=lay_danh_sach_lua_chon_mon(),
                            value=lay_danh_sach_lua_chon_mon()[0] if lay_danh_sach_lua_chon_mon() else None
                        )
                        with gr.Row():
                            so_luong_input = gr.Number(label="Số lượng", value=1, precision=0, minimum=1, scale=1)
                            ghi_chu_input = gr.Textbox(label="Ghi chú món", placeholder="Vd: Ít cay, ít đá...", scale=2)

                        with gr.Row():
                            btn_them_mon = gr.Button("➕ Thêm vào giỏ", variant="secondary")
                            btn_xoa_gio = gr.Button("🗑️ Xóa giỏ hàng", variant="stop")

                        gr.Markdown("### 🛍️ Giỏ hàng tạm")
                        state_gio_hang = gr.State([])
                        bang_gio_hang = gr.Dataframe(
                            headers=["STT", "Mã món", "Tên món", "SL", "Thành tiền", "Ghi chú"],
                            value=[],
                            interactive=False
                        )

                        btn_gui_don = gr.Button("🚀 XÁC NHẬN TẠO ĐƠN & GỬI XUỐNG BẾP", variant="primary")
                        tb_dat_mon = gr.Markdown("")

            # ------------------------------------------------------------------
            # TAB 2: HÀNG ĐỢI BẾP (QUEUE FIFO)
            # ------------------------------------------------------------------
            with gr.Tab("🍳 2. Hàng đợi bếp (Queue FIFO)"):
                gr.Markdown(
                    """
                    ### 👨‍🍳 Hàng đợi các món đang chờ chế biến
                    *Áp dụng giải thuật Hàng đợi FIFO: Món khách đặt trước sẽ được bếp lấy ra nấu trước ($O(1)$).*
                    """
                )
                bang_hang_doi = gr.Dataframe(
                    headers=["Thứ tự (FIFO)", "Mã đơn", "Tên món", "Số lượng", "Ghi chú"],
                    value=lay_bang_hang_doi(),
                    interactive=False
                )

                with gr.Row():
                    btn_nau_mon = gr.Button("👨‍🍳 Bếp nấu món tiếp theo (Dequeue O(1))", variant="primary", scale=2)
                    btn_lam_moi_queue = gr.Button("🔄 Làm mới hàng đợi", scale=1)

                tb_bep = gr.Markdown("")

            # ------------------------------------------------------------------
            # TAB 3: THANH TOÁN & HÓA ĐƠN (CHỌN TRỰC TIẾP TỪ DROPDOWN)
            # ------------------------------------------------------------------
            with gr.Tab("🧾 3. Thanh toán & Hóa đơn"):
                with gr.Row():
                    # Cột trái: Chọn đơn và thao tác
                    with gr.Column(scale=5):
                        gr.Markdown("### 📑 Chọn đơn hàng cần thanh toán")
                        don_dropdown = gr.Dropdown(
                            label="Danh sách đơn chưa thanh toán",
                            choices=lay_danh_sach_don_cho_thanh_toan(),
                            value=lay_danh_sach_don_cho_thanh_toan()[0] if lay_danh_sach_don_cho_thanh_toan() else None,
                            interactive=True
                        )
                        btn_lam_moi_don = gr.Button("🔄 Làm mới danh sách đơn", variant="secondary")

                        giam_gia_input = gr.Number(label="Số tiền giảm giá (VND)", value=0, precision=0, minimum=0)
                        btn_thanh_toan = gr.Button("💰 XÁC NHẬN THANH TOÁN", variant="primary")
                        tb_thanh_toan = gr.Markdown("")

                    # Cột phải: Chi tiết đơn & Hóa đơn xuất
                    with gr.Column(scale=7):
                        info_don_md = gr.Markdown("*(Vui lòng chọn đơn hàng ở bên trái)*")
                        bang_chi_tiet_don = gr.Dataframe(
                            headers=["Tên món", "SL", "Đơn giá", "Thành tiền", "Trạng thái bếp"],
                            value=[],
                            interactive=False
                        )
                        canh_bao_bep_md = gr.Markdown("")
                        hoa_don_xuat_md = gr.Markdown("")

        # ----------------------------------------------------------------------
        # GẮN SỰ KIỆN NÚT BẤM (EVENT LISTENERS)
        # ----------------------------------------------------------------------

        # Tab 1: Đặt món
        btn_them_mon.click(
            fn=them_mon_vao_gio,
            inputs=[mon_input, so_luong_input, ghi_chu_input, state_gio_hang],
            outputs=[state_gio_hang, bang_gio_hang, tb_dat_mon]
        )

        btn_xoa_gio.click(
            fn=xoa_gio_hang,
            inputs=[],
            outputs=[state_gio_hang, bang_gio_hang, tb_dat_mon]
        )

        btn_gui_don.click(
            fn=xac_nhan_tao_don,
            inputs=[state_gio_hang],
            outputs=[state_gio_hang, bang_gio_hang, bang_hang_doi, tb_dat_mon, don_dropdown]
        )

        # Tab 2: Hàng đợi bếp
        btn_nau_mon.click(
            fn=bep_nau_mon_tiep_theo,
            inputs=[],
            outputs=[bang_hang_doi, tb_bep, don_dropdown]
        )

        btn_lam_moi_queue.click(
            fn=lay_bang_hang_doi,
            inputs=[],
            outputs=[bang_hang_doi]
        )

        # Tab 3: Thanh toán
        don_dropdown.change(
            fn=khi_chon_don_thanh_toan,
            inputs=[don_dropdown],
            outputs=[bang_chi_tiet_don, info_don_md, canh_bao_bep_md, hoa_don_xuat_md]
        )

        btn_lam_moi_don.click(
            fn=lambda: gr.update(choices=lay_danh_sach_don_cho_thanh_toan()),
            inputs=[],
            outputs=[don_dropdown]
        )

        btn_thanh_toan.click(
            fn=thanh_toan_hoa_don,
            inputs=[don_dropdown, giam_gia_input],
            outputs=[hoa_don_xuat_md, tb_thanh_toan, don_dropdown]
        )

    return demo


def main():
    demo = tao_giao_dien_web()
    # Chạy web server tại localhost
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)


if __name__ == "__main__":
    main()
