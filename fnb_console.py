"""HỆ THỐNG QUẢN LÝ ĐƠN HÀNG NHÀ HÀNG (F&B) - BẢN CONSOLE DÀNH CHO NGƯỜI MỚI BẮT ĐẦU.

Cấu trúc dữ liệu chính sử dụng:
1. DICT (Bảng băm / Hash Map): Tra cứu Menu và Đơn hàng theo ID tức thì với độ phức tạp O(1).
2. QUEUE (Hàng đợi FIFO - collections.deque): Quản lý thứ tự chế biến món trong bếp, ai đặt trước nấu trước.
"""

import sys
from collections import deque
from datetime import datetime

# Đảm bảo hiển thị tốt tiếng Việt và ký tự đặc biệt trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

# ==============================================================================
# 1. KHỞI TẠO DỮ LIỆU BAN ĐẦU (IN-MEMORY DATABASE)
# ==============================================================================

# THỰC ĐƠN: Dùng DICT (Hash Map) với Key là mã món -> Tra cứu O(1)
MENU = {
    "M01": {"ten": "Cơm gà xối mỡ", "gia": 45000, "loai": "Món chính"},
    "M02": {"ten": "Phở bò tái nạm", "gia": 50000, "loai": "Món chính"},
    "M03": {"ten": "Bún chả Hà Nội", "gia": 40000, "loai": "Món chính"},
    "M04": {"ten": "Trà đào cam sả", "gia": 25000, "loai": "Đồ uống"},
    "M05": {"ten": "Cà phê sữa đá", "gia": 20000, "loai": "Đồ uống"},
}

# HÀNG ĐỢI BẾP: Dùng QUEUE (deque) theo nguyên lý FIFO (Vào trước - Ra trước)
# Thao tác thêm vào cuối: append() -> O(1)
# Thao tác lấy ra từ đầu: popleft() -> O(1)
KITCHEN_QUEUE = deque()

# QUẢN LÝ ĐƠN HÀNG: Dùng DICT lưu các đơn với Key là mã đơn (ORD001, ORD002...)
ORDERS = {}

# Biến đếm để tự động sinh mã đơn hàng tăng dần
order_counter = 1


# ==============================================================================
# 2. CÁC HÀM XỬ LÝ NGHIỆP VỤ (CHIA NHỎ TỪNG CHỨC NĂNG)
# ==============================================================================

def hien_thi_menu():
    """Hiển thị toàn bộ thực đơn ra màn hình console."""
    print("\n" + "=" * 55)
    print("                 📋 THỰC ĐƠN QUÁN ĂN")
    print("=" * 55)
    print(f"{'Mã món':<8} | {'Tên món ăn':<20} | {'Loại':<12} | {'Đơn giá':>10}")
    print("-" * 55)
    for ma_mon, thong_tin in MENU.items():
        gia_str = f"{thong_tin['gia']:,} đ"
        print(f"{ma_mon:<8} | {thong_tin['ten']:<20} | {thong_tin['loai']:<12} | {gia_str:>10}")
    print("=" * 55)


def tao_don_hang():
    """Tạo đơn hàng mới và đẩy các món vào Hàng đợi bếp (Queue)."""
    global order_counter
    hien_thi_menu()

    ds_mon_chon = []

    print("\n👉 NHẬP MÓN ĐẶT HÀNG (Nhập '0' để kết thúc việc chọn món):")
    while True:
        ma_mon = input("Nhập mã món (vd: M01): ").strip().upper()
        if ma_mon == "0":
            break

        # Tra cứu món trong DICT (Hash Map) -> Tốc độ O(1) cực nhanh
        if ma_mon not in MENU:
            print("[!] Mã món không tồn tại! Vui lòng kiểm tra lại thực đơn.")
            continue

        try:
            so_luong = int(input(f"Số lượng cho [{MENU[ma_mon]['ten']}]: "))
            if so_luong <= 0:
                print("[!] Số lượng phải là số nguyên dương lớn hơn 0!")
                continue
        except ValueError:
            print("[!] Vui lòng nhập số nguyên hợp lệ!")
            continue

        ghi_chu = input("Ghi chú (nhấn Enter nếu không có): ").strip()

        # Thêm món vào danh sách của đơn
        ds_mon_chon.append({
            "ma_mon": ma_mon,
            "ten_mon": MENU[ma_mon]["ten"],
            "don_gia": MENU[ma_mon]["gia"],
            "so_luong": so_luong,
            "ghi_chu": ghi_chu,
            "trang_thai": "CHO_NAU"  # CHO_NAU -> DANG_NAU -> DA_XONG
        })
        print(f"[OK] Đã thêm: {MENU[ma_mon]['ten']} (SL: {so_luong})")

    if not ds_mon_chon:
        print("[!] Đơn rỗng, đã hủy thao tác tạo đơn.")
        return

    # Sinh mã đơn tự động
    ma_don = f"ORD{order_counter:03d}"
    order_counter += 1

    # Lưu thông tin đơn hàng vào DICT ORDERS
    ORDERS[ma_don] = {
        "ma_don": ma_don,
        "thoi_gian": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
        "danh_sach_mon": ds_mon_chon,
        "trang_thai": "OPEN",  # OPEN -> PAID (Đã thanh toán)
        "tong_tien": sum(item["don_gia"] * item["so_luong"] for item in ds_mon_chon),
        "giam_gia": 0,
        "thanh_toan": 0
    }

    # ĐẨY TỪNG MÓN VÀO HÀNG ĐỢI BẾP (ENQUEUE / FIFO)
    for mon in ds_mon_chon:
        task_bep = {
            "ma_don": ma_don,
            "ten_mon": mon["ten_mon"],
            "so_luong": mon["so_luong"],
            "ghi_chu": mon["ghi_chu"],
            "ref_mon": mon  # Giữ liên kết để cập nhật trạng thái món
        }
        KITCHEN_QUEUE.append(task_bep)  # Enqueue: Thêm vào cuối hàng đợi

    print("\n" + "=" * 50)
    print(f"🎉 TẠO ĐƠN THÀNH CÔNG! Mã đơn của bạn là: [{ma_don}]")
    print(f"📌 Tổng tiền tạm tính: {ORDERS[ma_don]['tong_tien']:,} đ")
    print(f"🍳 Các món đã được xếp vào Hàng đợi Bếp (Hiện có {len(KITCHEN_QUEUE)} món chờ).")
    print("=" * 50)


def xem_hang_doi_bep():
    """Xem danh sách các món đang xếp hàng chờ bếp chế biến."""
    print("\n" + "=" * 60)
    print("             🍳 HÀNG ĐỢI BẾP CHẾ BIẾN (FIFO QUEUE)")
    print("=" * 60)

    if len(KITCHEN_QUEUE) == 0:
        print("🟢 Hiện tại bếp không có món nào đang chờ chế biến!")
        print("=" * 60)
        return

    print(f"Tổng số món đang xếp hàng: {len(KITCHEN_QUEUE)}")
    print(f"{'Thứ tự':<8} | {'Mã đơn':<8} | {'Tên món ăn':<20} | {'SL':<4} | {'Ghi chú':<15}")
    print("-" * 60)

    # Duyệt qua các phần tử trong Queue để xem thứ tự
    for idx, task in enumerate(KITCHEN_QUEUE, start=1):
        ghi_chu = task["ghi_chu"] if task["ghi_chu"] else "-"
        print(f"{idx:<8} | {task['ma_don']:<8} | {task['ten_mon']:<20} | {task['so_luong']:<4} | {ghi_chu:<15}")
    print("=" * 60)
    print("💡 Món ở thứ tự số 1 sẽ được chế biến tiếp theo theo nguyên tắc FIFO.")


def bep_nau_mon():
    """Bếp lấy món đầu hàng đợi (Dequeue) ra chế biến và hoàn thành."""
    print("\n--- BẾP TIẾP NHẬN & CHẾ BIẾN MÓN ---")

    # Kiểm tra hàng đợi có rỗng không
    if len(KITCHEN_QUEUE) == 0:
        print("🟢 Hàng đợi trống! Bếp có thể nghỉ ngơi.")
        return

    # DEQUEUE: Lấy phần tử ở đầu hàng đợi ra (O(1))
    mon_can_nau = KITCHEN_QUEUE.popleft()

    print(f"👨‍🍳 Bếp đang nấu: [{mon_can_nau['ten_mon']}] x {mon_can_nau['so_luong']} (Đơn: {mon_can_nau['ma_don']})")
    if mon_can_nau["ghi_chu"]:
        print(f"   ⚠️ Lưu ý cho bếp: {mon_can_nau['ghi_chu']}")

    # Cập nhật trạng thái món trong đơn thành ĐÃ XONG
    mon_can_nau["ref_mon"]["trang_thai"] = "DA_XONG"

    print(f"✅ ĐÃ NẤU XONG: [{mon_can_nau['ten_mon']}]! Có thể mang ra cho khách.")
    print(f"📦 Số món còn lại trong hàng đợi bếp: {len(KITCHEN_QUEUE)}")


def thanh_toan_don_hang():
    """Chọn đơn hàng từ danh sách chưa thanh toán (không cần gõ mã tay) và in hóa đơn."""
    print("\n--- THANH TOÁN ĐƠN HÀNG ---")
    
    # Lấy danh sách các đơn chưa thanh toán
    don_chua_thanh_toan = [d for d in ORDERS.values() if d["trang_thai"] == "OPEN"]
    
    if not don_chua_thanh_toan:
        print("🟢 Hiện không có đơn hàng nào đang chờ thanh toán!")
        return

    print("📋 DANH SÁCH ĐƠN ĐANG CHỜ THANH TOÁN:")
    for idx, d in enumerate(don_chua_thanh_toan, start=1):
        so_mon = len(d["danh_sach_mon"])
        da_xong = sum(1 for m in d["danh_sach_mon"] if m["trang_thai"] == "DA_XONG")
        tt_bep = "Bếp đã xong" if da_xong == so_mon else f"Bếp xong {da_xong}/{so_mon} món"
        print(f"  {idx}. [{d['ma_don']}] - {so_mon} món | {d['tong_tien']:,} đ | ({tt_bep})")

    chon_str = input("\n👉 Nhập SỐ THỨ TỰ đơn cần thanh toán (hoặc 0 để hủy): ").strip()
    if chon_str == "0":
        print("Đã hủy thao tác.")
        return

    try:
        chon_idx = int(chon_str) - 1
        if chon_idx < 0 or chon_idx >= len(don_chua_thanh_toan):
            print("❌ Số thứ tự không hợp lệ!")
            return
    except ValueError:
        print("❌ Vui lòng nhập số hợp lệ!")
        return

    don = don_chua_thanh_toan[chon_idx]
    ma_don = don["ma_don"]

    # In chi tiết đơn hàng
    print("\n" + "=" * 55)
    print(f"                🧾 HÓA ĐƠN: {ma_don}")
    print(f" Thời gian đặt: {don['thoi_gian']}")
    print("=" * 55)
    print(f"{'Tên món':<20} | {'SL':<4} | {'Đơn giá':>10} | {'Trạng thái':<10}")
    print("-" * 55)

    chua_xong_count = 0
    for mon in don["danh_sach_mon"]:
        gia_str = f"{mon['don_gia']:,} đ"
        tt_str = "✔️ Đã xong" if mon["trang_thai"] == "DA_XONG" else "⏳ Chờ nấu"
        if mon["trang_thai"] != "DA_XONG":
            chua_xong_count += 1
        print(f"{mon['ten_mon']:<20} | {mon['so_luong']:<4} | {gia_str:>10} | {tt_str:<10}")

    print("-" * 55)
    print(f"💰 TỔNG CỘNG: {don['tong_tien']:,} đ")
    print("=" * 55)

    # Cảnh báo nếu vẫn còn món chưa chế biến xong
    if chua_xong_count > 0:
        print(f"⚠️ Chú ý: Đơn này vẫn còn {chua_xong_count} món chưa được bếp nấu xong.")
        xac_nhan = input("Bạn vẫn muốn thanh toán trước? (c/k): ").strip().lower()
        if xac_nhan != "c":
            print("Đã hoãn thanh toán.")
            return

    # Xử lý giảm giá (nếu có)
    giam_gia = 0
    try:
        nhap_giam = input("Nhập số tiền giảm giá (nhấn Enter để bỏ qua): ").strip()
        if nhap_giam:
            giam_gia = int(nhap_giam)
            if giam_gia < 0 or giam_gia > don["tong_tien"]:
                print("[!] Số tiền giảm giá không hợp lệ (không được âm và không quá tổng tiền)!")
                return
    except ValueError:
        print("[!] Vui lòng nhập số tiền hợp lệ!")
        return

    tien_phai_tra = don["tong_tien"] - giam_gia
    don["giam_gia"] = giam_gia
    don["thanh_toan"] = tien_phai_tra
    don["trang_thai"] = "PAID"
    don["thoi_gian_tra"] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    print("\n" + "=" * 50)
    print("             🎉 THANH TOÁN THÀNH CÔNG!")
    print(f"  Mã đơn:           {ma_don}")
    print(f"  Tiền gốc:         {don['tong_tien']:,} đ")
    print(f"  Giảm giá:         {giam_gia:,} đ")
    print(f"  👉 THỰC THU:      {tien_phai_tra:,} đ")
    print("=" * 50)


# ==============================================================================
# 3. GIAO DIỆN CONSOLE MENU CHÍNH
# ==============================================================================

def in_menu_chinh():
    """In giao diện bảng chọn menu chính."""
    print("\n" + "╔" + "═" * 46 + "╗")
    print("║     🍽️  QUẢN LÝ ĐƠN HÀNG NHÀ HÀNG (F&B)      ║")
    print("╠" + "═" * 46 + "╣")
    print("║  1. Xem thực đơn (Menu)                      ║")
    print("║  2. Tạo đơn hàng mới (Đặt món)               ║")
    print("║  3. Xem hàng đợi bếp chế biến (Queue FIFO)   ║")
    print("║  4. Bếp nấu món tiếp theo (Dequeue món)      ║")
    print("║  5. Chọn & Thanh toán đơn hàng (Hóa đơn)     ║")
    print("║  0. Thoát chương trình                       ║")
    print("╚" + "═" * 46 + "╝")


def main():
    """Hàm chạy vòng lặp chính của ứng dụng console."""
    print("Chào mừng bạn đến với Hệ thống Quản lý F&B đơn giản!")

    while True:
        in_menu_chinh()
        lua_chon = input("👉 Nhập lựa chọn của bạn (0-5): ").strip()

        if lua_chon == "1":
            hien_thi_menu()
        elif lua_chon == "2":
            tao_don_hang()
        elif lua_chon == "3":
            xem_hang_doi_bep()
        elif lua_chon == "4":
            bep_nau_mon()
        elif lua_chon == "5":
            thanh_toan_don_hang()
        elif lua_chon == "0":
            print("\n👋 Cảm ơn bạn đã sử dụng chương trình. Tạm biệt!\n")
            break
        else:
            print("❌ Lựa chọn không hợp lệ, vui lòng nhập số từ 0 đến 5!")


if __name__ == "__main__":
    main()
